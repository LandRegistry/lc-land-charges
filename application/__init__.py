from flask import Flask
import os
from log.logger import setup_logging
from application.exchange import setup_messaging


app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS'))

setup_logging(app.config['DEBUG'])
producer = setup_messaging(app.config)
