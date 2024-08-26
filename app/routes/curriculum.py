from routes.imports import *
from flask import Blueprint
from config import base_url_company_user,base_url_journeys
curriculum_bp=Blueprint("curriculum",__name__)


@curriculum_bp.route('/journeys/<int:journey_id>/curriculum', methods=['GET'])
def get_curriculum(journey_id):
    try:
        # Fetch journey details
        journey_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}')
        journey_response.raise_for_status()
        journey = journey_response.json()

        # Fetch curriculum for the journey
        curriculum_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}/curriculum')
        curriculum_response.raise_for_status()
        curr = curriculum_response.json()

        # Render the curriculum template with journey and curriculum data
        return render_template('curriculum.html', journey=journey, curr=curr)

    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('index'))
