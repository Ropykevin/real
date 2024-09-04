from routes.imports import *
from config import *
from flask import Blueprint
topics_bp = Blueprint('topics', __name__)


@topics_bp.route('/journeys/<int:journey_id>/sections/<int:section_id>/topics/<int:topic_id>')
def topic_content(journey_id, section_id, topic_id):
    # Fetch the current journey details
    journey_response = requests.get(
        f'{base_url_journeys}journeys/{journey_id}')
    journey_response.raise_for_status()
    journey = journey_response.json()
    print(journey)

    # Fetch the current section details
    section_response = requests.get(
        f'{base_url_journeys}journeys/{journey_id}/sections/{section_id}')
    section_response.raise_for_status()
    section = section_response.json()
    print(section)

    # Fetch all topics in the section
    topics_response = requests.get(
        f'{base_url_journeys}sections/{section_id}/topics')
    topics_response.raise_for_status()
    topics = topics_response.json()
    print(topics)

    # Fetch specific topic details
    topic_response = requests.get(
        f'{base_url_journeys}sections/{section_id}/topics/{topic_id}')
    topic_response.raise_for_status()
    topic = topic_response.json()
    print(topic)

    # Fetch curriculum data for the journey
    curriculum_response = requests.get(
        f'{base_url_journeys}journeys/{journey_id}/curriculum')
    curriculum_response.raise_for_status()
    curr = curriculum_response.json()
    print(curr)
    # users
    user=session['user']
    print("mimi",user['id'])
    user_id=user['id']
    

    return render_template('content.html',user_id=user_id ,topicsection=topics, curr=curr, current_topic=topic, current_section=section, current_journey=journey)


