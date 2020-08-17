from flask import Blueprint, render_template
from app import db
from flask_login import login_required, current_user
from config import ROTATION_NUMBERS, MAX_ALLOCATION_POINTS
from utils import get_current_point_totals_for_user

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    points_results = get_current_point_totals_for_user(current_user.email)
    return render_template('profile.html', name=current_user.name, email=current_user.email,
                           max_points=MAX_ALLOCATION_POINTS, rotations=ROTATION_NUMBERS,
                           points_results=points_results)
