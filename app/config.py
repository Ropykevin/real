import os

base_url_journeys = 'http://167.71.54.75:8084/'
base_url_company_user = 'http://167.71.54.75:8082/trainees/'
base_url_userprogress = 'http://167.71.54.75:8081/'

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
