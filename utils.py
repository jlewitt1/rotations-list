import numpy as np
from numpy.random import choice
import pandas as pd
import models
from app import db
import logging

logging = logging.getLogger(__name__)


def choose_name_randomly(names, p_distribution):
    return choice(names, len(names), p=list(p_distribution.flatten()))[0]


def generate_order(names, weights):
    final_order = []

    np_weights = np.array(weights)
    total_sum = np.sum(np_weights, axis=1).reshape(1, 1)
    p_distribution = np_weights / total_sum  # normalize points into a probability distribution

    for i in range(len(names)):
        name_drawn = choose_name_randomly(names, p_distribution)
        while name_drawn in final_order:
            name_drawn = choose_name_randomly(names, p_distribution)
        final_order.append(name_drawn)

    return final_order


def get_names_and_points(df):
    names = df['Name'].tolist()
    points = df['Points'].tolist()

    return names, points


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


def save_lottery_overview_info_in_database(lottery_id, rotation_number, school_selected, year_selected):
    overview_obj = models.Overview(lottery_id=lottery_id, rotation_number=rotation_number, organization=school_selected,
                                   graduating_year=year_selected)
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
    current_user_points = models.Points.query.filter_by(email=user_email).first()
    if current_user_points:  # if data already exists then update
        num_submissions = current_user_points.num_submissions
        current_user_points.points_one = allocations_list[0]
        current_user_points.points_two = allocations_list[1]
        current_user_points.points_three = allocations_list[2]
        current_user_points.points_four = allocations_list[3]
        current_user_points.points_five = allocations_list[4]
        current_user_points.points_six = allocations_list[5]
        current_user_points.num_submissions += 1
        num_submissions += 1
    else:  # adding points for the first time for this user
        num_submissions = 0
        points_obj = models.Points(email=user_email, points_one=allocations_list[0],
                                   points_two=allocations_list[1], points_three=allocations_list[2],
                                   points_four=allocations_list[3], points_five=allocations_list[4],
                                   points_six=allocations_list[5])
        db.session.add(points_obj)
    db.session.commit()
    return num_submissions


def generate_full_name(first_name, last_name):
    return first_name + " " + last_name


def get_name_from_email(email):
    query = db.session.query(models.User).filter_by(email=email).first()
    res = generate_full_name(query.first_name, query.last_name)
    return res


def get_school_from_email(email):
    return db.session.query(models.User).filter_by(email=email).first().organization


def get_year_from_email(email):
    return db.session.query(models.User).filter_by(email=email).first().graduating_year


def build_dataframe_for_given_rotation(rotation_number, school_selected, year_selected):
    if rotation_number == 1:
        result = db.session.query(models.Points.email, models.Points.points_one)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_one,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]
    elif rotation_number == 2:
        result = db.session.query(models.Points.email, models.Points.points_two)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_two,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]
    elif rotation_number == 3:
        result = db.session.query(models.Points.email, models.Points.points_three)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_three,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]
    elif rotation_number == 4:
        result = db.session.query(models.Points.email, models.Points.points_four)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_four,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]
    elif rotation_number == 5:
        result = db.session.query(models.Points.email, models.Points.points_five)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_five,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]
    else:
        result = db.session.query(models.Points.email, models.Points.points_six)
        res = [{"Name": get_name_from_email(user.email), "Points": user.points_six,
                "Organization": get_school_from_email(user.email), "Year": get_year_from_email(user.email)} for user in
               result]

    df = pd.DataFrame(res)
    df = df.loc[((df['Organization'] == school_selected) & (df['Year'] == int(year_selected)))]
    return df


def get_current_point_totals_for_user(user_email):
    num_submissions = 0
    results = []
    query_results = db.session.query(models.Points).filter_by(email=user_email).first()
    if query_results:  # if user has already saved points in DB
        num_submissions = query_results.num_submissions
        results = [query_results.points_one, query_results.points_two, query_results.points_three,
                   query_results.points_four, query_results.points_five, query_results.points_six]
    return results, num_submissions


def generate_data_for_stats_page(school_selected, year_selected):
    if year_selected is None:
        results_list = db.session.query(models.Overview).filter_by(organization=school_selected).all()
    else:
        results_list = db.session.query(models.Overview).filter_by(organization=school_selected,
                                                                   graduating_year=year_selected).all()
    dates_run = [result.date for result in results_list]
    rotations_run = list(set([result.rotation_number for result in results_list]))
    return dates_run[::-1], rotations_run


def generate_final_lottery_order_for_rotation(rotation_number, school_selected, year_selected, from_file):
    if from_file:
        df = pd.read_excel(from_file)
    else:
        df = build_dataframe_for_given_rotation(rotation_number, school_selected, year_selected)
    names, points = get_names_and_points(df)
    final_names_order = generate_order(names, [points])

    return names, points, final_names_order


def get_all_mail_recipients():
    query_result = db.session.query(models.User).all()
    all_users = [{"name": generate_full_name(result.first_name, result.last_name), "email": result.email} for result in
                 query_result]
    return all_users


def format_str_date(date):
    return ":".join(date.split(":")[:-1])
