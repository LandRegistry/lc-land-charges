from flask import Flask
import os

app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS'))


from application import exchange

from log.logger import setup_logging
setup_logging(app.config['DEBUG'])

from application.exchange import setup_messaging
producer = setup_messaging()

from application import routes