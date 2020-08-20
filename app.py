import uuid
import os
import logging
from flask import Flask, jsonify, request, render_template, Blueprint, flash, redirect, url_for
from flask_admin.babel import gettext
from flask_login import LoginManager, login_required, current_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import ROTATION_NUMBERS, MAX_ALLOCATION_POINTS, MAIL_CONFIG

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
        return current_user.is_authenticated

    @expose('/')
    def index(self):
        return self.render('admin.html', rotation_numbers=ROTATION_NUMBERS)


class UserModelView(ModelView):
    can_edit = False

    def is_accessible(self):
        return current_user.is_authenticated

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
    form_excluded_columns = ['email']

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))


class OverviewModelView(ModelView):
    can_create = False
    can_edit = False

    def is_accessible(self):
        return current_user.is_authenticated

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
        return current_user.is_authenticated


from auth import auth as auth_blueprint
from main import main as main_blueprint
import models

# register the blueprints for main.py
main = Blueprint('main', __name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
# add admin panels to app
admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(UserModelView(models.User, db.session))
admin.add_view(PointsModelView(models.Points, db.session))
admin.add_view(OverviewModelView(models.Overview, db.session))
admin.add_view(MyView(name='Lottery', endpoint='lottery'))

import utils


@app.route('/results', methods=['POST'])
def results():
    """gets all results for a specified lottery to display to user"""
    if request.method == 'POST':
        try:
            file_received = request.files['file']
            rotation_number = int(request.form.get('rotation_select'))
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               from_file=file_received)
            lottery_id = str(uuid.uuid4())
            utils.save_lottery_drawing_results_in_database(names, points, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)
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
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               from_file=False)
            utils.save_lottery_drawing_results_in_database(names, points, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)
            dates_run, rotations_run = utils.generate_data_for_stats_page()
            return render_template('stats.html', dates=dates_run, rotations=rotations_run)
        except Exception as e:
            logging.error(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/lottery', methods=['POST'])
def lottery():
    """perform a lottery on a given rotation - does not save results"""
    if request.method == 'POST':
        try:
            rotation_number = int(request.form.get('rotation_select'))
            names, points, final_names_order = utils.generate_final_lottery_order_for_rotation(rotation_number,
                                                                                               from_file=False)
            return render_template('results.html', names=final_names_order, all_data={"names": names,
                                                                                      "weights": points})
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/stats')
def stats():
    """main stats page showing all dates for lotteries run and all rotations represented"""
    dates_run, rotations_run = utils.generate_data_for_stats_page()
    return render_template('stats.html', dates=dates_run, rotations=rotations_run)


@app.route('/lottery_participants', methods=['POST'])
def lottery_participants():
    """retrieves the participants and allocations for a given rotation"""
    rotation_number = int(request.form['rotation'])
    df = utils.build_dataframe_for_given_rotation(rotation_number)
    if df.empty:
        return f"Currently no participants for rotation {rotation_number}"
    # if there is data for given rotation
    return jsonify(df.to_dict('records'))


@app.route("/dates", methods=['GET', 'POST'])
def dates():
    """show the complete lottery results based on a given datetime selected"""
    date_selected = request.form.get('date_select')
    lottery_id = db.session.query(models.Overview).filter_by(date=date_selected).first().lottery_id
    data_for_date_selected = db.session.query(models.Result).filter_by(lottery_id=lottery_id)
    df = utils.build_final_dataframe_for_page(data_for_date_selected)
    return render_template('dates.html', date=date_selected, all_data=df)


@app.route("/rotations", methods=['GET', 'POST'])
def rotations():
    """show the results of a fake lottery run by a registered user"""
    rotation_selected = request.form.get('rotation_select')
    data_for_rotation_selected = db.session.query(models.Overview).filter_by(rotation_number=int(rotation_selected))
    all_dates_for_rotation = [data.date for data in data_for_rotation_selected]
    all_lottery_ids_for_rotation = [data.lottery_id for data in data_for_rotation_selected]
    # get winner for given date and lottery id
    all_winners = []
    for idx, date in enumerate(all_dates_for_rotation):
        winner_name = models.Result.query.filter_by(lottery_id=all_lottery_ids_for_rotation[idx]).order_by(
            models.Result.final_ranking.asc()).first().name
        all_winners.append(winner_name)
    return render_template('rotations.html', rotation=rotation_selected, all_dates=all_dates_for_rotation,
                           all_winners=all_winners)


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
        try:
            utils.save_points_for_given_user(current_user.email, allocations_list)
            emails.send_mail(subject=MAIL_CONFIG["update_subj"], recipient=current_user.email,
                             html_body=render_template('email/status.html', user=current_user.name,
                                                       points_remaining=str(MAX_ALLOCATION_POINTS - total_sum)))
        except Exception as e:
            logging.error(f"failed to save points and send email for {current_user.email}: {e}")
        return render_template('summary.html', rotation_numbers=ROTATION_NUMBERS, name=current_user.name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
def profile():
    points_results = utils.get_current_point_totals_for_user(current_user.email)
    return render_template('profile.html', name=current_user.name, email=current_user.email,
                           max_points=MAX_ALLOCATION_POINTS, rotations=ROTATION_NUMBERS,
                           points_results=points_results)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return models.User.query.get(int(user_id))


@app.teardown_appcontext
def shutdown_session(exception=None):
    """automatically close all unused/hanging connections and prevent bottleneck"""
    db.session.remove()


if __name__ == '__main__':
    app.run(debug=True)
