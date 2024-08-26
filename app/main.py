from flask import Flask
from authlib.integrations.flask_client import OAuth
from routes.journeys import journeys_bp
from routes.categories import categories_bp
from routes.sections import sections_bp
from routes.topics import topics_bp
from dotenv import load_dotenv
from routes.auth import oauth_bp
from routes.profile import profile_bp
from routes.curriculum import curriculum_bp

oauth = OAuth()

app = Flask(__name__, static_folder='./static', template_folder='./templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

load_dotenv()

# Register Blueprints with unique names
app.register_blueprint(categories_bp)
app.register_blueprint(curriculum_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(journeys_bp)
app.register_blueprint(sections_bp)
app.register_blueprint(topics_bp)

oauth.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
