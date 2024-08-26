from routes.imports import *
from config import *
from flask import Blueprint

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/')
def index():
    try:
        response = requests.get(f'{base_url_journeys}categories')
        response.raise_for_status()
        categories = response.json()
        total = len(categories)
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        categories = []
        total = 0
    return render_template('index.html', categories=categories, total=total)


@categories_bp.route('/categories/<int:category_id>/journeys')
def category_journeys(category_id):
    try:
        response = requests.get(
            f'{base_url_journeys}/categories/{category_id}/journeys')
        response.raise_for_status()
        journeys = response.json()

    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        journeys = []
        categories = []

    return render_template('journeys.html', journeys=journeys)
