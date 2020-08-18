import numpy as np
from numpy.random import choice
import pandas as pd
import models
from app import db


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
        lottery_obj = models.Result(name=lottery_result['name'], points=lottery_result['points'],
                                    final_ranking=lottery_result['final_ranking'], lottery_id=lottery_id)
        db.session.add(lottery_obj)
    db.session.commit()


def save_lottery_overview_info_in_database(lottery_id, rotation_number):
    overview_obj = models.Overview(lottery_id=lottery_id, rotation_number=rotation_number)
    db.session.add(overview_obj)
    db.session.commit()


def build_final_dataframe_for_page(data):
    df = pd.DataFrame(pd.read_sql(data.statement, db.session.bind))
    df = df.sort_values(by=['final_ranking'], ascending=True).reset_index(drop=True)
    df['final_ranking'] = df['final_ranking'] + 1  # increment to start with 1 and not 0
    del df['lottery_id']  # delete columns not needed to show to user
    del df['id']

    return df


def save_points_for_given_user(user_email, allocations_list):
    current_user = models.Points.query.filter_by(email=user_email).first()
    if current_user:  # if data already exists then update
        current_user.points_one = allocations_list[0]
        current_user.points_two = allocations_list[1]
        current_user.points_three = allocations_list[2]
        current_user.points_four = allocations_list[3]
        current_user.points_five = allocations_list[4]
    else:
        points_obj = models.Points(email=user_email, points_one=allocations_list[0], points_two=allocations_list[1],
                                   points_three=allocations_list[2], points_four=allocations_list[3],
                                   points_five=allocations_list[4])
        db.session.add(points_obj)
    db.session.commit()


def get_name_from_email(email):
    return db.session.query(models.User).filter_by(email=email).first().name


def build_dataframe_for_given_rotation(rotation_number):
    res = []
    if rotation_number == 1:
        result = db.session.query(models.Points.email, models.Points.points_one)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_one} for user in result]
    elif rotation_number == 2:
        result = db.session.query(models.Points.email, models.Points.points_two)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_two} for user in result]
    elif rotation_number == 3:
        result = db.session.query(models.Points.email, models.Points.points_three)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_three} for user in result]
    elif rotation_number == 4:
        result = db.session.query(models.Points.email, models.Points.points_four)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_four} for user in result]
    elif rotation_number == 5:
        result = db.session.query(models.Points.email, models.Points.points_five)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_five} for user in result]

    df = pd.DataFrame(res)
    return df


def get_current_point_totals_for_user(user_email):
    results = []
    query_results = db.session.query(models.Points).filter_by(email=user_email).first()
    if query_results:  # if user has already saved points in DB
        results = [query_results.points_one, query_results.points_two, query_results.points_three,
                   query_results.points_four, query_results.points_five]
    return results


def generate_data_for_stats_page():
    results_list = db.session.query(models.Overview).all()
    dates_run = [result.date for result in results_list]
    rotations_run = list(set([result.rotation_number for result in results_list]))

    return dates_run, rotations_run
