from flask import Blueprint, render_template

pages_bp = Blueprint('users_pages', __name__)


@pages_bp.get('/')
def home():
    return render_template('users/home.html')


@pages_bp.get('/users/<int:user_id>/')
def detail(user_id):
    return render_template('users/detail.html', user_id=user_id)
