import numpy as np
from numpy.random import choice
import pandas as pd
from models import *


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


def get_names_and_weights(df):
    names = df['Name'].tolist()
    weights = df['Points'].tolist()
    return names, weights


def update_entries_for_lottery_results(names, weights, final_names_order, lottery_id):
    res = []
    for idx, name in enumerate(names):
        res.append({"name": name, "points": weights[idx], "final_ranking": final_names_order.index(name),
                    "lottery_id:": lottery_id})
    return res


def save_lottery_drawing_results_in_database(names, weights, final_names_order, lottery_id):
    lottery_results_data = update_entries_for_lottery_results(names, weights, final_names_order, lottery_id)
    for lottery_result in lottery_results_data:
        lottery_obj = Result(name=lottery_result['name'], points=lottery_result['points'],
                             final_ranking=lottery_result['final_ranking'], lottery_id=lottery_id)
        db.session.add(lottery_obj)
    db.session.commit()


def save_lottery_overview_info_in_database(lottery_id, rotation_number):
    overview_obj = Overview(lottery_id=lottery_id, rotation_number=rotation_number)
    db.session.add(overview_obj)
    db.session.commit()


def build_final_dataframe_for_page(data):
    df = pd.DataFrame(pd.read_sql(data.statement, db.session.bind))
    df = df.sort_values(by=['final_ranking'], ascending=True).reset_index(drop=True)
    df['final_ranking'] = df['final_ranking'] + 1  # increment to start with 1 and not 0
    del df['lottery_id']  # delete columns not needed to show to user
    del df['id']

    return df
