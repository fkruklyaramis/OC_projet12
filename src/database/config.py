import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./epic_events.db')
SENTRY_DSN = os.getenv('SENTRY_DSN')
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me')
