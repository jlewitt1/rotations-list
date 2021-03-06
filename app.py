import uuid
import os
import datetime
import logging
from flask import Flask, jsonify, request, render_template, Blueprint, flash, redirect, url_for
from flask_admin.babel import gettext
from flask_login import LoginManager, login_required, current_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import ROTATION_NUMBERS, MAX_ALLOCATION_POINTS, MAIL_CONFIG, ROTATION_NAMES, MAX_SUBMISSIONS, ALL_SCHOOLS, \
    GRADUATING_CLASSES

logging = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"max_overflow": 15, "pool_pre_ping": True, "pool_recycle": 60 * 60,
                                           "pool_size": 30}
db = SQLAlchemy(app)
# add login to app
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
# configure mail settings
app.config.update(MAIL_SERVER='smtp.gmail.com', MAIL_PORT=587, MAIL_USE_SSL=False, MAIL_USE_TLS=True,
                  MAIL_USERNAME=os.environ['MAIL_ACCOUNT'], MAIL_PASSWORD=os.environ['MAIL_PASSWORD'])
mail = Mail(app)
import emails


# initialize custom views for admin panel
class MyView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    @expose('/')
    def index(self):
        return self.render('admin.html', rotation_numbers=ROTATION_NUMBERS, rotation_names=ROTATION_NAMES,
                           organizations=ALL_SCHOOLS, graduating_classes=GRADUATING_CLASSES)


class UserModelView(ModelView):
    column_editable_list = ('graduating_year', 'is_superuser')
    form_widget_args = {
        'organization': {'readonly': True}, 'first_name': {'readonly': True}, 'last_name': {'readonly': True},
        'email': {'readonly': True}, 'password': {'readonly': True}
    }
    column_list = ('first_name', 'last_name', 'email', 'organization', 'graduating_year', 'is_superuser')
    column_labels = dict(first_name='First Name', last_name='Last Name', email='Email',
                         organization='Medical School', graduating_year='Graduation Year', is_superuser='Superuser')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            email_to_query = model.email
            points_record = db.session.query(models.Points).filter_by(email=email_to_query).first()
            if points_record:  # if user to be deleted has also registered points - delete those too
                self.session.delete(points_record)
                flash(f'Successfully deleted points allocated for: {model.email}')
            self.session.delete(model)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                logging.info('Failed to delete record.')
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
            self.session.rollback()
            return False
        else:
            self.after_model_delete(model)
        return True


class PointsModelView(ModelView):
    can_create = False
    can_edit = False
    column_list = ('email', 'points_one', 'points_two', 'points_three', 'points_four', 'points_five', 'points_six')
    column_labels = dict(points_one=ROTATION_NAMES[0], points_two=ROTATION_NAMES[1], points_three=ROTATION_NAMES[2],
                         points_four=ROTATION_NAMES[3], points_five=ROTATION_NAMES[4], points_six=ROTATION_NAMES[5])

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))


class OverviewModelView(ModelView):
    can_create = False
    can_edit = False
    column_list = ('date', 'rotation_number', 'organization', 'graduating_year')
    column_labels = dict(date='Date', rotation_number='Rotation Number', organization='School Name',
                         graduating_year='Graduation Year')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

    def delete_model(self, model):  # when deleting a lottery remove all results for given lottery
        try:
            self.on_model_delete(model)
            lottery_id_to_remove = model.lottery_id
            all_results = db.session.query(models.Result).filter(models.Result.lottery_id == lottery_id_to_remove).all()
            for result in all_results:
                self.session.delete(result)
            flash(f'Successfully deleted all names and points associated with lottery id: {lottery_id_to_remove}')
            self.session.delete(model)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                logging.info('Failed to delete record.')
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
            self.session.rollback()
            return False
        else:
            self.after_model_delete(model)
        return True


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser


from auth import auth as auth_blueprint
from main import main as main_blueprint
import models

# register the blueprints for main.py
main = Blueprint('main', __name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
# add admin panels to app
admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(UserModelView(models.User, db.session, name="Registered Users"))
admin.add_view(PointsModelView(models.Points, db.session, name="Points Allocations"))
admin.add_view(OverviewModelView(models.Overview, db.session, name="Lottery History"))
admin.add_view(MyView(name='New Lottery', endpoint='lottery'))

import utils


@app.route('/results', methods=['POST'])
def results():
    """gets all results for a specified lottery to display to user"""
    if request.method == 'POST':
        try:
            file_received = request.files['file']
            rotation_number = int(request.form.get('rotation_select'))
            school_selected = request.form.get('school_select')
            year_selected = request.form.get('year_select')
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               school_selected,
                                                                                               year_selected,
                                                                                               from_file=file_received)
            lottery_id = str(uuid.uuid4())
            utils.save_lottery_drawing_results_in_database(names, points, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number,
                                                         school_selected=school_selected, year_selected=year_selected)
            return render_template('results.html', names=final_names_order, all_data={"names": names,
                                                                                      "weights": points})
        except Exception as e:
            logging.error(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/admin_lottery', methods=['POST'])
def admin_lottery():
    """performs real lottery for given rotation provided by admin and saves results to database"""
    if request.method == 'POST':
        try:
            lottery_id = str(uuid.uuid4())
            rotation_number = int(request.form.get('rotation_select'))
            school_selected = request.form.get('school_select')
            year_selected = request.form.get('year_select')
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               school_selected,
                                                                                               year_selected,
                                                                                               from_file=False)
            utils.save_lottery_drawing_results_in_database(names, points, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number,
                                                         school_selected=school_selected, year_selected=year_selected)
            dates_run, rotations_run = utils.generate_data_for_stats_page(school_selected, year_selected)
            return render_template('stats.html', dates=dates_run, rotations=rotations_run,
                                   rotation_names=ROTATION_NAMES, school_selected=school_selected,
                                   organizations=ALL_SCHOOLS, graduating_classes=GRADUATING_CLASSES)
        except Exception as e:
            logging.error(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/lottery', methods=['POST'])
def lottery():
    """perform a lottery on a given rotation - does not save results"""
    if request.method == 'POST':
        try:
            rotation_number = int(request.form.get('rotation_select'))
            school_selected = request.form.get('school_select')
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               school_selected,
                                                                                               from_file=False)
            return render_template('results.html', names=final_names_order, all_data={"names": names,
                                                                                      "weights": points})
        except Exception as e:
            logging.error(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/stats')
def stats():
    """main stats page showing all dates for lotteries run and all rotations represented"""
    try:
        dates_run, rotations_run = utils.generate_data_for_stats_page(school_selected=None, year_selected=None)
        return render_template('stats.html', dates=dates_run, rotations=rotations_run, rotation_names=ROTATION_NAMES,
                               school_selected=None, organizations=ALL_SCHOOLS, graduating_classes=GRADUATING_CLASSES)
    except Exception as e:
        logging.error(f"Unable to generate stats table: {e}")
        return render_template('error.html', error=str(e))


@app.route('/school_results', methods=['POST'])
def school_results():
    try:
        school_selected = request.form.get('school_select')
        dates_run, rotations_run = utils.generate_data_for_stats_page(school_selected, year_selected=None)
        return render_template('stats.html', dates=dates_run, rotations=rotations_run, rotation_names=ROTATION_NAMES,
                               school_selected=school_selected, organizations=ALL_SCHOOLS,
                               graduating_classes=GRADUATING_CLASSES)
    except Exception as e:
        logging.error(f"Unable to generate school_results: {e}")
        return render_template('error.html', error=str(e))


@app.route('/graduating_class', methods=['POST'])
def graduating_class():
    try:
        year_selected = int(request.form['year'])
        school_selected = request.form['school']
        dates_run, rotations_run = utils.generate_data_for_stats_page(school_selected, year_selected)
        return {"dates_run": [str(date) for date in dates_run], "rotations_run": rotations_run,
                "rotation_names": ROTATION_NAMES}
    except Exception as e:
        logging.error(f"Unable to generate graduating_class: {e}")
        return render_template('error.html', error=str(e))


@app.route('/lottery_participants', methods=['POST'])
def lottery_participants():
    """retrieves the participants and allocations for a given rotation"""
    rotation_number = int(request.form['rotation'])
    school_selected = request.form['school']
    year_selected = request.form['year']
    df = utils.build_dataframe_for_given_rotation(rotation_number, school_selected, year_selected)
    if df.empty:
        return f"Currently no participants for rotation {rotation_number} in {school_selected}"
    # if there is data for given rotation
    return jsonify(df.to_dict('records'))


@app.route("/dates", methods=['GET', 'POST'])
def dates():
    """show the complete lottery results based on a given datetime selected"""
    try:
        date_selected_str = request.form.get('date_select')
        date_selected = datetime.datetime.strptime(date_selected_str, '%Y-%m-%d %H:%M:%S.%f')
        lottery_id = db.session.query(models.Overview).filter_by(date=date_selected).first().lottery_id
        data_for_date_selected = db.session.query(models.Result).filter_by(lottery_id=lottery_id)
        df = utils.build_final_dataframe_for_page(data_for_date_selected)
        return render_template('dates.html', date=utils.format_str_date(date_selected_str), all_data=df)

    except Exception as e:
        logging.error(f"Unable to generate dates: {e}")
        return render_template('error.html', error=str(e))


@app.route("/rotations", methods=['GET', 'POST'])
def rotations():
    """show the results of a fake lottery run by a registered user"""
    try:
        rotation_selected = request.form['rotation']
        school_selected = request.form['school']
        data_for_rotation_selected = db.session.query(models.Overview).filter_by(rotation_number=int(rotation_selected),
                                                                                 organization=school_selected)
        all_dates_for_rotation = [data.date for data in data_for_rotation_selected]
        all_lottery_ids_for_rotation = [data.lottery_id for data in data_for_rotation_selected]
        # get winner for given date and lottery id
        all_winners = []
        for idx, date in enumerate(all_dates_for_rotation):
            try:
                winner_name = models.Result.query.filter_by(lottery_id=all_lottery_ids_for_rotation[idx]).order_by(
                    models.Result.final_ranking.asc()).first().name
                all_winners.append(winner_name)
            except Exception as e:
                del all_dates_for_rotation[idx]
                logging.error(f'Unable to find winner: {str(e)}')
        return render_template('rotations.html', all_dates=all_dates_for_rotation[::-1], all_winners=all_winners[::-1],
                               rotation_name=ROTATION_NAMES[int(rotation_selected) - 1])
    except Exception as e:
        logging.error(f"Unable to generate rotations: {e}")
        return render_template('error.html', error=str(e))


@login_required
@app.route('/allocations', methods=['POST'])
def allocations():
    """saves the provided allocations for each rotation for a given user and allows them to run a trial lottery"""
    res = dict(request.form)  # {rotation_number : points}
    allocations_list = [int(vv) for kk, vv in res.items()]
    total_sum = sum(allocations_list)
    if total_sum > MAX_ALLOCATION_POINTS:
        return render_template('error.html',
                               error="The total points allotted must not exceed {}".format(MAX_ALLOCATION_POINTS))
    else:
        num_submissions = utils.save_points_for_given_user(current_user.email, allocations_list)
        try:
            emails.send_mail(subject=MAIL_CONFIG["update_subj"], recipient=current_user.email,
                             html_body=render_template('email/status.html', user=current_user.first_name,
                                                       points_remaining=str(MAX_ALLOCATION_POINTS - total_sum)))
        except Exception as e:
            logging.error(f"failed to send email for {current_user.email}: {e}")
        return render_template('summary.html', rotation_numbers=ROTATION_NUMBERS, name=current_user.first_name,
                               num_submissions_remaining=MAX_SUBMISSIONS - int(num_submissions))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
def profile():
    try:
        points_results, num_submissions = utils.get_current_point_totals_for_user(current_user.email)
        return render_template('profile.html', name=current_user.first_name, email=current_user.email,
                               max_points=MAX_ALLOCATION_POINTS, rotations=ROTATION_NUMBERS,
                               points_results=points_results, rotation_names=ROTATION_NAMES,
                               num_submissions_remaining=MAX_SUBMISSIONS - num_submissions)
    except Exception as e:
        logging.error(f"Unable to generate profile: {e}")
        return render_template('error.html', error=str(e))


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return models.User.query.get(int(user_id))


@app.teardown_appcontext
def shutdown_session(exception=None):
    """automatically close all unused/hanging connections and prevent bottleneck"""
    db.session.remove()


@app.errorhandler(403)
def page_not_found(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
