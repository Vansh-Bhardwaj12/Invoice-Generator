import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = "invoice_generator_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")