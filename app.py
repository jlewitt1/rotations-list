import uuid
import os
from flask import Flask, jsonify, request, render_template
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from utils import *
from config import ROTATION_NUMBERS

IMAGES_FOLDER = os.path.join('static', 'images')
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER

os.environ['APP_SETTINGS'] = "config.DevelopmentConfig"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from models import *

api = Api(app)


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
            rotation_number = request.form.get('date_select')
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
            return jsonify(str(e)), 500


@app.route('/stats')
def stats():
    results_list = db.session.query(Overview).all()
    dates_run = [result.date for result in results_list]
    rotations_run = list(set([result.rotation_number for result in results_list]))
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
            Result.final_ranking.desc()).first().name
        all_winners.append(winner_name)
    return render_template('rotations.html', rotation=rotation_selected, all_dates=all_dates_for_rotation,
                           all_winners=all_winners)


@app.route("/")
def home():
    return render_template('template.html')


if __name__ == '__main__':
    app.run(debug=True)
