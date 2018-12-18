import os

# base_dir
basedir = os.path.abspath(os.path.dirname(__file__))

# debug
DEBUG = True

# port
PORT = 5580

# Your App secret key
SECRET_KEY = os.urandom(64)

# Mail
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
MAIL_DEFAULT_SENDER = ''

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:passwd@localhost/tasker'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json', 'pickle']

# App name
APP_NAME = "Tasker REST API"

# Mail Gun
MAILGUN_API_KEY = ''.encode('utf-8')

# Twilio Auth
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ""

