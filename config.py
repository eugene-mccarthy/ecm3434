import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
