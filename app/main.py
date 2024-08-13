from flask import Flask, render_template, redirect, url_for, request, jsonify, json, session, abort, make_response, flash
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import requests
import os
import logging
from functools import wraps
import firebase_admin
from firebase_admin import credentials, auth, exceptions

# Firebase initialization
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app initialization
app = Flask(__name__, static_folder='./static', template_folder='./templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
oauth = OAuth(app)

# Base URLs for APIs
base_url_journeys = 'http://167.71.54.75:8084/'
base_url_company_user = 'http://167.71.54.75:8082/trainees/'
base_url_userprogress = 'http://167.71.54.75:8081/'

# Load Google OAuth details
load_dotenv()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Print client information for debugging
# print(f"Google Client ID: {GOOGLE_CLIENT_ID}")
# print(f"Google Client Secret: {GOOGLE_CLIENT_SECRET}")

# Register Google OAuth
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={'scope': 'openid email profile'}
)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login_oauth')
def login_oauth():
    redirect_uri = 'https://78e3-197-248-16-215.ngrok-free.app/login/callback'
    # print(f"Redirect URI: {redirect_uri}")
    session["nonce"] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/login/callback")
def callback():
    try:
        # Authorize access token
        token = oauth.google.authorize_access_token()
        google_user = oauth.google.parse_id_token(
            token, nonce=session.get("nonce"))
        email = google_user.get('email')
        full_name = google_user.get('name')

        # Check if the user exists in your system
        response = requests.get(f"{base_url_company_user}/email/{email}")

        if response.status_code == 200:
            # User exists in the system
            user = response.json()
            firebase_id = user.get('firebaseId')
        else:
            # User does not exist in the system, create user in Firebase
            try:
                try:
                    firebase_user = auth.create_user(
                        email=email, display_name=full_name)
                except exceptions.FirebaseError as firebase_e:
                    if firebase_e.code == 'EMAIL_EXISTS':
                        # Fetch existing Firebase user if email already exists
                        firebase_user = auth.get_user_by_email(email)
                    else:
                        raise firebase_e

                firebase_id = firebase_user.uid

                # Register the new user in your system
                payload = {
                    "email": email,
                    "firebaseId": firebase_id,
                    "fullName": full_name,
                    "latestDeviceId": None
                }

                response = requests.post(base_url_company_user, json=payload)
                if response.status_code != 201:
                    error_details = response.json()
                    flash(f"Error storing user: {error_details}", 'error')
                    return redirect(url_for('login'))

                user = response.json()
            except requests.RequestException as req_e:
                flash(f"An error occurred with the API: {req_e}", 'error')
                return redirect(url_for('login'))
            except exceptions.FirebaseError as firebase_e:
                flash(f"Firebase error: {str(firebase_e)}", 'error')
                return redirect(url_for('login'))

        # Store user in session
        session['user'] = user
        response = make_response(redirect(url_for('index')))
        response.set_cookie('user_email', email, secure=True, httponly=True)
        response.set_cookie('user_full_name', full_name,
                            secure=True, httponly=True)

        # Redirect to the next URL if it exists
        next_url = session.pop('next', None)
        if next_url:
            return redirect(next_url)

        return response

    except requests.RequestException as req_e:
        flash(f"An error occurred with the external API: {req_e}", 'error')
        return redirect(url_for('login'))
    except exceptions.FirebaseError as firebase_e:
        flash(f"Firebase error: {str(firebase_e)}", 'error')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'error')
        session.pop('oauth_token', None)
        return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Store the URL the user was trying to access
            session['next'] = request.url
            flash('You need to be logged in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/profile')
@login_required
def profile():
    user = session['user']
    # print(user)
    return render_template('profile.html', user=user)


@app.route('/edit-profile', methods=['POST'])
def edit_profile():
    email = request.cookies.get('user_email')
    if not email:
        return redirect(url_for('login'))

    full_name = request.form.get('full_name')
    new_email = request.form.get('email')

    session['user']['full_name'] = full_name
    session['user']['email'] = new_email

    update_payload = {
        "fullName": full_name,
        "email": new_email,
    }

    try:
        # PUT request to update the trainee details by email
        response = requests.put(f"{base_url_company_user}{email}", json=update_payload)
        response.raise_for_status()

        flash('Profile updated successfully', 'success')

        # Update the session cookies
        response = make_response(redirect(url_for('profile')))
        response.set_cookie('user_email', new_email,
                            secure=True, httponly=True)
        response.set_cookie('user_full_name', full_name,
                            secure=True, httponly=True)

        return response

    except requests.RequestException as e:
        flash(f"Failed to update profile: {e}", 'error')
        return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_email', '', expires=0,
                        secure=True, httponly=True)
    return response
# end oauth

@app.route('/')
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


@app.route('/<string:category_name>/journeys')
def category_journeys(category_name):
    try:
        # Fetch all categories to get the category_id by category_name
        response_cat = requests.get(f'{base_url_journeys}/categories')
        response_cat.raise_for_status()
        categories = response_cat.json()

        category = next((cat for cat in categories if cat['categoryTitle']), None)

        if not category:
            flash('Category not found.', 'error')
            return redirect(url_for('index'))

        category_id = category['id']

        # Fetch journeys for the found category_id
        response = requests.get(
            f'{base_url_journeys}/categories/{category_id}/journeys')
        response.raise_for_status()
        journeys = response.json()

    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        journeys = []
        categories = []

    return render_template('journeys.html', journeys=journeys, categories=categories)


@app.route('/<string:title>/<int:id>/all-topics')
def courseTopics(title, id):
    try:
        journey = requests.get(f'{base_url_journeys}/journeys/{id}').json()
        all_Sections = requests.get(
            f'{base_url_journeys}/journeys/{id}/sections').json()
        # Fetch categories and topics (if necessary)
        # ...
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        journey = {}
        all_Sections = []
    return render_template('courseTopics.html', journey=journey, all_Sections=all_Sections)


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        return None


@app.route('/data', methods=['GET'])
def get_data():
    journey_id = request.args.get('journey_id', type=int)
    section_id = request.args.get('section_id', type=int)
    context = {
        'journey': None,
        'sections': None,
        'topics': None,
        'section': None,
        'all_categories': None,
        'category': None,
        'catIds': [],
        'CategoryTopic': [],
        'course': None
    }

    if journey_id is not None:
        journey_url = f'{base_url_journeys}/journeys/{journey_id}'
        context['journey'] = fetch_data(journey_url)
        if section_id is not None:
            sections_url = f'{
                base_url_journeys}/journeys/{journey_id}/sections'
            context['sections'] = fetch_data(sections_url)
        return render_template('client/courseTopics.html', **context)

    if section_id is not None:
        topics_url = f"{base_url_journeys}/sections/{section_id}/topics"
        section_url = f"{base_url_journeys}/sections/{section_id}"
        context['topics'] = fetch_data(topics_url)
        context['section'] = fetch_data(section_url)
        return render_template('client/courseTopics.html', **context)

    return "No valid parameter"


@app.route('/journeys/<int:journey_id>', methods=['GET'])
@login_required
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


@app.route('/<int:journey_id>/sections/<int:section_id>/topics/<int:topic_id>')
def topic_content(journey_id, section_id, topic_id):
    try:
        # Fetch the current topic
        response = requests.get(
            f'{base_url_journeys}/sections/{section_id}/topics/{topic_id}')
        response.raise_for_status()
        content = response.json()

        # Fetch all topics in the current section
        section_response = requests.get(
            f'{base_url_journeys}/sections/{section_id}/topics')
        section_response.raise_for_status()
        topics = section_response.json()
        # print("mimi",topics)

        # Determine the index of the current topic
        topic_index = next((i for i, t in enumerate(
            topics) if t['id'] == topic_id), -1)

        # Determine the previous and next topics
        prev_topic = topics[topic_index - 1] if topic_index > 0 else None
        next_topic = topics[topic_index +
                            1] if topic_index < len(topics) - 1 else None

        # Fetch the current section details
        current_section_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}/sections/{section_id}')
        current_section_response.raise_for_status()
        current_section = current_section_response.json()
        
        sections_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}/sections')
        sections_response.raise_for_status()
        sections = sections_response.json()
        # print("vvv",sections)

        # Render the template with the data
        return render_template(
            'content.html',
            topic=content,
            prev_topic=prev_topic,
            next_topic=next_topic,
            topics=topics,
            current_section=current_section,
            sections=sections
        )
    except requests.RequestException as e:
        # print(f"An error occurred: {e}")
        abort(404)

@app.route('/sections/<int:section_id>/topics')
def get_topics_by_section_id(section_id):
    try:
        topics_api_url = f"{base_url_journeys}/sections/{section_id}/topics"
        topics = fetch_data(topics_api_url)
        section_api_url = f"{base_url_journeys}/sections/{section_id}"
        section = fetch_data(section_api_url)
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        topics = []
        section = {}
    return render_template('client/section_topics.html', section=section, topics=topics)


@app.route('/sections/<int:section_id>/levels/<int:level_id>/topics')
def get_topics_by_level_id(section_id, level_id):
    try:
        api_url = f'{
            base_url_journeys}/sections/{section_id}/levels/{level_id}/topics'
        topics = fetch_data(api_url)
        level_response = requests.get(
            f'{base_url_journeys}/sections/{section_id}/levels/{level_id}')
        level_response.raise_for_status()
        level = level_response.json()
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        topics = []
        level = {}
    return render_template('client/section_topics.html', section_id=section_id, level=level, topics=topics)


@app.route('/sections/<int:section_id>/levels')
def get_levels_by_section_id(section_id):
    try:
        api_url = f'{base_url_journeys}/sections/{section_id}/levels'
        levels = fetch_data(api_url)
        section_response = requests.get(
            f'{base_url_journeys}/sections/{section_id}')
        section_response.raise_for_status()
        section = section_response.json()
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
        levels = []
        section = {}
    return render_template('client/levels.html', levels=levels, section=section)


# user progress
# section progress 
@app.route('/users/<int:user_id>/journeys/<int:journey_id>/sections/<int:section_id>/progress', methods=['GET'])
@login_required
def get_section_progress(user_id, journey_id, section_id):
    try:
        url = f"{
            base_url_userprogress}/users/progress/{user_id}/{journey_id}/{section_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch section progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500
    
# topic progress


@app.route('/users/<int:user_id>/journeys/<int:journey_id>/sections/<int:section_id>/topics/<int:topic_id>/progress', methods=['GET'])
@login_required
def get_topic_progress(user_id, journey_id, section_id, topic_id):
    try:
        url = f"{base_url_userprogress}/users/progress/{
            user_id}/{journey_id}/{section_id}/{topic_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch topic progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

# update section progress


@app.route('/users/progress/sections', methods=['POST'])
@login_required
def create_section_progress():
    data = request.json
    try:
        response = requests.post(
            f"{base_url_userprogress}/users/progress/section", json=data)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        flash(f"Failed to create section progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

# update topic progress


@app.route('/users/progress/topics', methods=['POST'])
@login_required
def create_topic_progress():
    data = request.json
    try:
        response = requests.post(
            f"{base_url_userprogress}/users/progress/topic", json=data)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        flash(f"Failed to create topic progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

# user section progress


@app.route('/users/<int:user_id>/sections/progress', methods=['GET'])
@login_required
def get_user_sections_progress(user_id):
    try:
        url = f"{base_url_userprogress}/users/progress/sections/{user_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch user sections progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500


# user topic progress

@app.route('/users/<int:user_id>/topics/progress', methods=['GET'])
@login_required
def get_user_topics_progress(user_id):
    try:
        url = f"{base_url_userprogress}/users/progress/topics/{user_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch user topics progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

# journey progress 


@app.route('/users/<int:user_id>/journeys/<int:journey_id>/progress/total', methods=['GET'])
@login_required
def get_user_journey_total_progress(user_id, journey_id):
    try:
        url = f"{base_url_userprogress}/users/progress/total/{user_id}/{journey_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch user journey total progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

# all topics 


@app.route('/users/<int:user_id>/journeys/<int:journey_id>/topics/progress', methods=['GET'])
@login_required
def get_user_topics_total_progress(user_id, journey_id):
    try:
        url = f"{base_url_userprogress}/users/topics/{user_id}/{journey_id}"
        progress = fetch_data(url)
        return jsonify(progress)
    except requests.RequestException as e:
        flash(f"Failed to fetch user topics total progress: {e}", 'error')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
