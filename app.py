import uuid
import os
from flask import Flask, jsonify, request, render_template, Blueprint, flash
from flask_admin.babel import gettext
from flask_login import LoginManager, login_required, current_user
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from config import ROTATION_NUMBERS, MAX_ALLOCATION_POINTS
import pandas as pd

app = Flask(__name__)

os.environ['APP_SETTINGS'] = "config.DevelopmentConfig"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin.html', rotation_numbers=ROTATION_NUMBERS)


class MyModelView(ModelView):

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
                print('Failed to delete record.')
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
            self.session.rollback()
            return False
        else:
            self.after_model_delete(model)
        return True


from auth import auth as auth_blueprint
from main import main as main_blueprint
import models

main = Blueprint('main', __name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)

admin = Admin(app)
admin.add_view(MyModelView(models.User, db.session))
admin.add_view(MyView(name='Lottery', endpoint='lottery'))

import utils


@app.route('/rotations_order', methods=['POST'])  # VIA API
def rotations_order():
    file_obj = request.files.get('file')
    df = pd.read_excel(file_obj)
    names, weights = utils.get_names_and_weights(df)
    try:
        final_order = utils.generate_order(names, [weights])
        return jsonify(final_order), 200
    except Exception as e:
        return jsonify(str(e)), 500


@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':
        try:
            file_received = request.files['file']
            rotation_number = int(request.form.get('rotation_select'))
            df = pd.read_excel(file_received)
            names, weights = utils.get_names_and_weights(df)
            final_names_order = utils.generate_order(names, [weights])
            lottery_id = str(uuid.uuid4())
            utils.save_lottery_drawing_results_in_database(names, weights, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)
            return render_template('results.html', names=final_names_order,
                                   all_data={"names": names, "weights": weights})
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/admin_lottery', methods=['POST'])
def admin_lottery():
    if request.method == 'POST':
        try:
            rotation_number = int(request.form.get('rotation_select'))
            df = utils.build_dataframe_for_given_rotation(rotation_number)
            names, weights = utils.get_names_and_weights(df)
            final_names_order = utils.generate_order(names, [weights])
            lottery_id = str(uuid.uuid4())
            utils.save_lottery_drawing_results_in_database(names, weights, final_names_order, lottery_id)
            utils.save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)

            dates_run, rotations_run = utils.generate_data_for_stats_page()
            return render_template('stats.html', dates=dates_run, rotations=rotations_run)
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/lottery', methods=['POST'])
def lottery():
    if request.method == 'POST':
        try:
            rotation_number = int(request.form.get('rotation_select'))
            df = utils.build_dataframe_for_given_rotation(rotation_number)
            names, weights = utils.get_names_and_weights(df)
            final_names_order = utils.generate_order(names, [weights])
            return render_template('results.html', names=final_names_order,
                                   all_data={"names": names, "weights": weights})
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/stats')
def stats():
    dates_run, rotations_run = utils.generate_data_for_stats_page()
    return render_template('stats.html', dates=dates_run, rotations=rotations_run)


@app.route('/lottery_participants', methods=['POST'])
def lottery_participants():
    rotation_number = int(request.form['rotation'])
    df = utils.build_dataframe_for_given_rotation(rotation_number)
    if df.empty:
        return f"Currently no participants for rotation {rotation_number}"
    # if there is data for given rotation
    return jsonify(df.to_dict('records'))


@app.route("/dates", methods=['GET', 'POST'])
def dates():
    date_selected = request.form.get('date_select')
    lottery_id = db.session.query(models.Overview).filter_by(date=date_selected).first().lottery_id
    data_for_date_selected = db.session.query(models.Result).filter_by(lottery_id=lottery_id)
    df = utils.build_final_dataframe_for_page(data_for_date_selected)
    return render_template('dates.html', date=date_selected, all_data=df)


@app.route("/rotations", methods=['GET', 'POST'])
def rotations():
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
    res = dict(request.form)  # {rotation_number : points}
    allocations_list = [int(vv) for kk, vv in res.items()]
    total_sum = sum(allocations_list)
    if total_sum > MAX_ALLOCATION_POINTS:
        return render_template('error.html',
                               error="The total points allotted ({}) must not exceed {}".format(total_sum,
                                                                                                MAX_ALLOCATION_POINTS))
    else:
        utils.save_points_for_given_user(current_user.email, allocations_list)
        return render_template('summary.html', rotation_numbers=ROTATION_NUMBERS, name=current_user.name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return models.User.query.get(int(user_id))


if __name__ == '__main__':
    app.run(debug=True)
