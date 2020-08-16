import numpy as np
from numpy.random import choice
import pandas as pd
from flask import Flask, jsonify, request, make_response, render_template
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


def choose_name_randomly(names, p_distribution):
    draw = choice(names, len(names), p=list(p_distribution.flatten()))[0]
    return draw


def generate_order(names, weights):
    final_order = []

    np_weights = np.array(weights)
    total_sum = np.sum(np_weights, axis=1).reshape(1, 1)
    p_distribution = np_weights / total_sum

    for i in range(len(names)):
        name_drawn = choose_name_randomly(names, p_distribution)
        while name_drawn in final_order:
            name_drawn = choose_name_randomly(names, p_distribution)
        final_order.append(name_drawn)

    return final_order


def get_names_and_weights(file_received):
    df = pd.read_excel(file_received)
    names = df['Name'].tolist()
    weights = [df['Points'].tolist()]
    return names, weights


def read_file_from_api():
    file_received = request.files.get('file')
    return file_received


@app.route('/rotations', methods=['POST'])  # VIA API
def rotations():
    file_obj = read_file_from_api()
    names, weights = get_names_and_weights(file_obj)
    try:
        final_order = generate_order(names, weights)
        return jsonify(final_order), 200
    except Exception as e:
        return jsonify(str(e)), 500


@app.route('/upload')
def upload_file():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        file_received = request.files['file']
        names, weights = get_names_and_weights(file_received)
        try:
            final_order = generate_order(names, weights)
            return jsonify(final_order), 200
        except Exception as e:
            return jsonify(str(e)), 500


# a route where we will display a welcome message via an HTML template
@app.route("/")
def hello():
    return render_template('template.html')


if __name__ == '__main__':
    app.run(debug=True)
