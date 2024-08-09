from flask import Flask, render_template, redirect, url_for, request, jsonify, json, session, send_from_directory, abort, make_response, flash
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import requests
import os
import logging

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='./static', template_folder='./templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
oauth = OAuth(app)

base_url_journeys = 'http://167.71.54.75:8084/'
base_url_company_user = 'http://167.71.54.75:8082/trainees/'
base_url_userprogress = 'http://167.71.54.75:8081/'

# Google OAuth
load_dotenv()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

print(f"Google Client ID: {GOOGLE_CLIENT_ID}")
print(f"Google Client Secret: {GOOGLE_CLIENT_SECRET}")

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
    redirect_uri = "https://5816-197-248-16-215.ngrok-free.app/login/callback"
    print(f"Redirect URI: {redirect_uri}")
    session["nonce"] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/login/callback")
def callback():
    try:
        token = oauth.google.authorize_access_token()
        google_user = oauth.google.parse_id_token(
            token, nonce=session["nonce"])
        email = google_user['email']
        full_name = google_user['name']

        # Check if user already exists in the external API
        response = requests.get(f"{base_url_company_user}/email/{email}")
        if response.status_code == 200:
            user = response.json()
            print(user)
            journey_id = session.pop('journey_id', None)
            if journey_id:
                redirect_url = url_for('get_journey', journey_id=journey_id)
            else:
                redirect_url = url_for('index')
        else:
            # Register new user in the external API
            payload = {
                "email": email,
                "firebaseId": 'web',
                "fullName": full_name,
                "id": 0,
                "latestDeviceId": "web"
            }
            response = requests.post(base_url_company_user, json=payload)
            if response.status_code != 201:
                flash(f"Error storing user in external API: {\
                      response.text}", 'error')
                return redirect(url_for('login'))
            user = response.json()
            redirect_url = url_for('index')

        # Set cookies
        response = make_response(redirect(redirect_url))
        response.set_cookie('user_email', email, secure=True, httponly=True)
        response.set_cookie('user_full_name', full_name,
                            secure=True, httponly=True)
        return response

    except requests.RequestException as req_e:
        flash(f"An error occurred with the external API: {req_e}", 'error')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'error')
        session.pop('oauth_token', None)
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_email', '', expires=0,
                        secure=True, httponly=True)
    return response


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


@app.route('/<int:category_id>/journeys')
def category_journeys(category_id):
    try:
        response = requests.get(
            f'{base_url_journeys}categories/{category_id}/journeys')
        response.raise_for_status()
        journeys = response.json()
        response_cat = requests.get(f'{base_url_journeys}/categories')
        response_cat.raise_for_status()
        categories = response_cat.json()
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
    email = request.cookies.get('user_email')
    if not email:
        return redirect(url_for('login'))

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
def get_journey(journey_id):
    email = request.cookies.get('user_email')
    if not email:
        return redirect(url_for('login'))

    try:
        journey_response = requests.get(
            f'{base_url_journeys}/journeys/{journey_id}')
        journey_response.raise_for_status()
        journey = journey_response.json()
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

    return render_template('courseTopics.html', journey=journey, sections=sections, section=section, section_id=section_id, topics=topics)


@app.route('/sections/<int:section_id>/topics/<int:topic_id>')
def topic_content(section_id, topic_id):
    try:
        response = requests.get(
            f'{base_url_journeys}/sections/{section_id}/topics/{topic_id}')
        response.raise_for_status()
        content = response.json()
        section_response = requests.get(
            f'{base_url_journeys}/sections/{section_id}/topics')
        section_response.raise_for_status()
        topics = section_response.json()
        topic_index = next((i for i, t in enumerate(
            topics) if t['id'] == topic_id), -1)
        prev_topic = topics[topic_index - 1] if topic_index > 0 else None
        next_topic = topics[topic_index +
                            1] if topic_index < len(topics) - 1 else None

        return render_template('courseTopics.html', topic=content, prev_topic=prev_topic, next_topic=next_topic, topics=topics)
    except requests.RequestException as e:
        flash(f"An error occurred: {e}", 'error')
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


if __name__ == '__main__':
    app.run(debug=True)
