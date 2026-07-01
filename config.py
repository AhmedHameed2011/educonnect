import os

# Find the absolute path of the directory containing this config.py file
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "educonnect_super_secret_key"
    
    # Securely point directly to the database file inside the instance folder
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "instance", "educonnect.db")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False