from src import config
from flask import Flask


webapp = Flask(__name__)
webapp.secret_key = config.app_config['secret_key']
webapp.config['MAX_CONTENT_LENGTH'] = config.app_config['max_file_size_MB'] * 1024 * 1024

from src import main
