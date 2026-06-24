import os

class Config:
    SECRET_KEY = "educonnect_super_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///educonnect.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
