from routes.imports import *
from config import *
from flask import Blueprint


topics_bp = Blueprint('topics', __name__)


@topics_bp.route('/<int:journey_id>/sections/<int:section_id>/topics/<int:topic_id>')
def topic_content(journey_id, section_id, topic_id):
    response = requests.get(
        f'{base_url_journeys}journeys/{journey_id}/curriculum')
    response.raise_for_status()
    curr = response.json()

    return render_template('content.html', curr=curr)
