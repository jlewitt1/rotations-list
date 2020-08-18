import uuid
import os
from flask import Flask, jsonify, request, render_template, Blueprint
from flask_login import LoginManager, login_required, current_user
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from config import ROTATION_NUMBERS, MAX_ALLOCATION_POINTS

IMAGES_FOLDER = os.path.join('static', 'images')
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER

os.environ['APP_SETTINGS'] = "config.DevelopmentConfig"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from models import *
from utils import *

api = Api(app)
main = Blueprint('main', __name__)

# blueprint for auth routes in our app
from auth import auth as auth_blueprint

app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from main import main as main_blueprint

app.register_blueprint(main_blueprint)


@app.route('/rotations_order', methods=['POST'])  # VIA API
def rotations_order():
    file_obj = request.files.get('file')
    df = pd.read_excel(file_obj)
    names, weights = get_names_and_weights(df)
    try:
        final_order = generate_order(names, [weights])
        return jsonify(final_order), 200
    except Exception as e:
        return jsonify(str(e)), 500


@app.route('/upload')
def upload_file():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'sample.PNG')
    return render_template('upload.html', sample_image=full_filename, rotation_numbers=ROTATION_NUMBERS)


@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':
        try:
            file_received = request.files['file']
            rotation_number = int(request.form.get('rotation_select'))
            df = pd.read_excel(file_received)
            names, weights = get_names_and_weights(df)
            final_names_order = generate_order(names, [weights])
            lottery_id = str(uuid.uuid4())
            save_lottery_drawing_results_in_database(names, weights, final_names_order, lottery_id)
            save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)
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
            df = build_dataframe_for_given_rotation(rotation_number)
            names, weights = get_names_and_weights(df)
            final_names_order = generate_order(names, [weights])
            lottery_id = str(uuid.uuid4())
            save_lottery_drawing_results_in_database(names, weights, final_names_order, lottery_id)
            save_lottery_overview_info_in_database(lottery_id, rotation_number=rotation_number)

            dates_run, rotations_run = generate_data_for_stats_page()
            return render_template('stats.html', dates=dates_run, rotations=rotations_run)
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/lottery', methods=['POST'])
def lottery():
    if request.method == 'POST':
        try:
            rotation_number = int(request.form.get('rotation_select'))
            df = build_dataframe_for_given_rotation(rotation_number)
            names, weights = get_names_and_weights(df)
            final_names_order = generate_order(names, [weights])
            return render_template('results.html', names=final_names_order,
                                   all_data={"names": names, "weights": weights})
        except Exception as e:
            print(f"Unable to save data in table: {e}")
            return render_template('error.html', error=str(e))


@app.route('/stats')
def stats():
    dates_run, rotations_run = generate_data_for_stats_page()
    return render_template('stats.html', dates=dates_run, rotations=rotations_run)


@app.route("/dates", methods=['GET', 'POST'])
def dates():
    date_selected = request.form.get('date_select')
    lottery_id = db.session.query(Overview).filter_by(date=date_selected).first().lottery_id
    data_for_date_selected = db.session.query(Result).filter_by(lottery_id=lottery_id)
    df = build_final_dataframe_for_page(data_for_date_selected)
    return render_template('dates.html', date=date_selected, all_data=df)


@app.route("/rotations", methods=['GET', 'POST'])
def rotations():
    rotation_selected = request.form.get('rotation_select')
    data_for_rotation_selected = db.session.query(Overview).filter_by(rotation_number=int(rotation_selected))
    all_dates_for_rotation = [data.date for data in data_for_rotation_selected]
    all_lottery_ids_for_rotation = [data.lottery_id for data in data_for_rotation_selected]
    # get winner for given date and lottery id
    all_winners = []
    for idx, date in enumerate(all_dates_for_rotation):
        winner_name = Result.query.filter_by(lottery_id=all_lottery_ids_for_rotation[idx]).order_by(
            Result.final_ranking.asc()).first().name
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
        save_points_for_given_user(current_user.email, allocations_list)
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
    return User.query.get(int(user_id))


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin.html', rotation_numbers=ROTATION_NUMBERS)

    # def is_accessible(self):
    #     # rendering the view only if the user is authenticate
    #     return current_user.is_authenticated()
    #


if __name__ == '__main__':
    admin = Admin(app)
    admin.add_view(ModelView(models.User, db.session))
    admin.add_view(MyView(name='Lottery', endpoint='lottery'))
    app.run(debug=True)
