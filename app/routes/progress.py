from routes.imports import *
from flask import Blueprint
from config import base_url_userprogress

progress_bp = Blueprint('progress', __name__)

# post section
@progress_bp.route('/users/progress/section', methods=['POST'])
def section_progress():
    Data = request.json()
    journey_id = Data.get('journey_id')
    section_id = Data.get('section_id')
    level_id = Data.get('level_id')
    user_id = Data.get('user_id')
    data=data.get('data')

    payload = {
        "journeyId": journey_id,
        "sectionId": section_id,
        "levelId": level_id,
        "userId": user_id,
        'data':data
    }
    response = requests.post(
        f"{base_url_userprogress}users/progress/sections", json=payload)

    try:
        response = requests.post(
            base_url_userprogress, json=payload)
        response.raise_for_status()
        return jsonify({
            'message': 'Progress posted successfully',
            'response': response.json()
        }), response.status_code
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': str(http_err)}), response.status_code
    except requests.exceptions.RequestException as err:
        return jsonify({'error': str(err)}), 500

# post topic

@progress_bp.route('/users/progress/topic', methods=['POST'])
def topic_progress():
    Data = request.json()
    journey_id = Data.get('journey_id')
    section_id = Data.get('section_id')
    level_id = Data.get('level_id')
    topic_id = Data.get('topic_id')
    user_id = Data.get('user_id')
    data = data.get('data')
    
    print('sss',Data)

    

    payload = {
        "journeyId": journey_id,
        "sectionId": section_id,
        "levelId": level_id,
        'topicid': topic_id,
        "userId": user_id,
        'data': data
    }
    response = requests.post(
        f"{base_url_userprogress}users/progress/topic", json=payload)
    try:
        response = requests.post(
            base_url_userprogress, json=payload)
        response.raise_for_status()
        return jsonify({
            'message': 'Progress posted successfully',
            'response': response.json()
        }), response.status_code
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': str(http_err)}), response.status_code
    except requests.exceptions.RequestException as err:
        return jsonify({'error': str(err)}), 500


# get section progress
@progress_bp.route('/users/progress/<int:userId>/<int:journeyId>/<int:sectionId>', methods=['GET'])
def get_section_progress(userId, journeyId, sectionId):
    external_api_url = f"{base_url_userprogress}users/progress{userId}/{journeyId}/{sectionId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


# get topic progress

@progress_bp.route('/users/progress/<int:userId>/<int:journeyId>/<int:sectionId>/<int:topicId>', methods=['GET'])
def get_topic_progress(userId, journeyId, sectionId,topicId):
    external_api_url = f"{
        base_url_userprogress}users/progress{userId}/{journeyId}/{sectionId}/{topicId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
# get users section progress


@progress_bp.route('/users/progress/sections/<int:userId>', methods=['GET'])
def get_user_sections_progress(userId):
    external_api_url = f"{
        base_url_userprogress}users/progress/sections/{userId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
# get users topic progress

@progress_bp.route('/users/progress/topics/<int:userId>', methods=['GET'])
def get_user_topics_progress(userId):
    external_api_url = f"{
        base_url_userprogress}users/progress/topics/{userId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# get topic progress


@progress_bp.route('/users/progress/total/<int:userId>/<int:journeyId>', methods=['GET'])
def get_journey_progress(userId, journeyId):
    external_api_url = f"{
        base_url_userprogress}users/progress{userId}/total/{journeyId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# get topic progress


@progress_bp.route('/users/topics/<int:userId>/<int:journeyId>', methods=['GET'])
def get_total_topic_progress(userId, journeyId):
    external_api_url = f"{
        base_url_userprogress}users/topics/{userId}/{journeyId}"
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        progress_data = response.json()
        return jsonify(progress_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
