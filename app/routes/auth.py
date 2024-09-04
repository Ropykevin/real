from routes.imports import *
from config import *
from authlib.integrations.flask_client import OAuth
from flask import Blueprint 

oauth_bp = Blueprint('oauth', __name__)



oauth = OAuth()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            session['next'] = request.url
            flash('You need to be logged in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


load_dotenv()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={'scope': 'openid email profile'}
)

section_topics = {}


@oauth_bp.route('/login')
def login():
    return render_template('login.html')


@oauth_bp.route('/login_oauth')
def login_oauth():
    redirect_uri = 'https://bca4-197-248-16-215.ngrok-free.app/login/callback'
    # print(f"Redirect URI: {redirect_uri}")
    session["nonce"] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@oauth_bp.route("/login/callback")
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


@oauth_bp.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_email', '', expires=0,
                        secure=True, httponly=True)
    return response
# end oauth
