from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
import models
from config import ROTATION_NUMBERS
from app import db
import app


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin.html', rotation_numbers=ROTATION_NUMBERS)


def admin_page():
    admin = Admin(app)
    admin.add_view(ModelView(models.User, db.session))
    admin.add_view(MyView(name='Lottery', endpoint='lottery'))
    return admin
