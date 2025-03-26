 # app/__init__.py
from flask import Flask
from flask_cors import CORS

# Create Flask application
app = Flask(__name__)

# Enable CORS for all routes from localhost:4200
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})

