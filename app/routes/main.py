from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    # Redirect authenticated users to the meal recording page
    if current_user.is_authenticated:
        return redirect(url_for('meal.record_meal'))
    return render_template('index.html')
