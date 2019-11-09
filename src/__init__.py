from flask import Flask

webapp = Flask(__name__)

from src import main, view_instance_details, scaling
