from routes.imports import *
from config import base_url_company_user,base_url_journeys
from flask import Blueprint


journeys_bp = Blueprint('journeys', __name__)


@journeys_bp.route('/journeys/<int:journey_id>', methods=['GET'])
def get_journey(journey_id):

    try:
        journey_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}')
        journey_response.raise_for_status()
        journey = journey_response.json()
        # print("wewe",journey)
        section_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}/sections')
        section_response.raise_for_status()
        sections = section_response.json()
        for section in sections:
            section_id = section["id"]
            topics_response = requests.get(
                f'{base_url_journeys}/sections/{section_id}/topics')
            topics_response.raise_for_status()
            section['topics'] = topics_response.json()

    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        journey = {}
        sections = []

    section = sections[0] if sections else {}
    section_id = section.get("id", None) if section else None
    topics = section.get('topics', []) if section else []
    # print(journey)
    return render_template('courseTopics.html', journey=journey, sections=sections, section=section, section_id=section_id, topics=topics, journey_id=journey_id)
