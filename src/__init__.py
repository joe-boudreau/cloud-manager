from flask import Flask
from src import config

webapp = Flask(__name__)
webapp.secret_key = config.secret_key

from src import main, view_instance_details, scaling
