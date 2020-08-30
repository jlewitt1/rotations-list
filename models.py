import datetime
from datetime import timezone
from sqlalchemy.dialects.postgresql import UUID
from flask_login import UserMixin
from app import db


class Result(db.Model):
    __tablename__ = 'lottery_results'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    points = db.Column(db.Integer)
    final_ranking = db.Column(db.Integer)
    lottery_id = db.Column(UUID)

    def __init__(self, name, points, final_ranking, lottery_id):
        self.name = name
        self.points = points
        self.final_ranking = final_ranking
        self.lottery_id = lottery_id

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Overview(db.Model):
    __tablename__ = 'lottery_overview'

    id = db.Column(db.Integer, primary_key=True)
    lottery_id = db.Column(UUID)
    date = db.Column(db.DateTime)
    rotation_number = db.Column(db.Integer)
    organization = db.Column(db.String(1000))
    graduating_year = db.Column(db.Integer)

    def __init__(self, lottery_id, rotation_number, organization, graduating_year):
        self.lottery_id = lottery_id
        self.rotation_number = rotation_number
        self.date = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        self.organization = organization
        self.graduating_year = graduating_year

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Points(db.Model):
    __tablename__ = 'points'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    num_submissions = db.Column(db.Integer)
    points_one = db.Column(db.Integer)
    points_two = db.Column(db.Integer)
    points_three = db.Column(db.Integer)
    points_four = db.Column(db.Integer)
    points_five = db.Column(db.Integer)
    points_six = db.Column(db.Integer)

    def __init__(self, email, points_one, points_two, points_three, points_four, points_five, points_six):
        self.email = email
        self.num_submissions = 0
        self.points_one = points_one
        self.points_two = points_two
        self.points_three = points_three
        self.points_four = points_four
        self.points_five = points_five
        self.points_six = points_six

    def __repr__(self):
        return '<id {}>'.format(self.id)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))
    organization = db.Column(db.String(1000))
    graduating_year = db.Column(db.Integer)

    def __init__(self, email, password, first_name, last_name, organization, graduating_year):
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.organization = organization
        self.graduating_year = graduating_year

    def __repr__(self):
        return '<id {}>'.format(self.id)
