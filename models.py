import datetime
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

    def __init__(self, lottery_id, rotation_number):
        self.lottery_id = lottery_id
        self.rotation_number = rotation_number
        self.date = datetime.datetime.utcnow()

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Points(db.Model):
    __tablename__ = 'points'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    points_one = db.Column(db.Integer)
    points_two = db.Column(db.Integer)
    points_three = db.Column(db.Integer)
    points_four = db.Column(db.Integer)
    points_five = db.Column(db.Integer)

    def __init__(self, email, points_one, points_two, points_three, points_four, points_five):
        self.email = email
        self.points_one = points_one
        self.points_two = points_two
        self.points_three = points_three
        self.points_four = points_four
        self.points_five = points_five

    def __repr__(self):
        return '<id {}>'.format(self.id)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.name = name

    def __repr__(self):
        return '<id {}>'.format(self.id)
