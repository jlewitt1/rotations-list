import datetime

from app import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey


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
