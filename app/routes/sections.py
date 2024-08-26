from routes.imports import *
from config import base_url_company_user, base_url_journeys
from flask import Blueprint

sections_bp = Blueprint('sections', __name__)


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        return None


@sections_bp.route('/journeys/<int:journey_id>/sections', methods=['GET'])
# @login_required
def get_sections_for_journey(journey_id):
    # user = session["user"]
    try:
        # Fetch journey details
        journey_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}')
        journey_response.raise_for_status()
        journey = journey_response.json()
        # Fetch sections by level
        api_url = f'{base_url_journeys}/journeys/{journey_id}/sections'
        sections = fetch_data(api_url)
        print('kiswahili', sections)
        if sections is None:
            flash(f"Failed to retrieve sections for journey ID {
                  journey_id}", 'error')
            sections = []
        # fetch curricullum
        response = requests.get(
            f'{base_url_journeys}journeys/{journey_id}/curriculum')
        response.raise_for_status()
        curr = response.json()
        print(curr)
        return render_template('courseTopics.html', sections=sections, journey_id=journey_id, journey=journey, curr=curr)

    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('index'))
