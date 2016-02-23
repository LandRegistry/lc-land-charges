from flask import Flask
import os
from log.logger import setup_logging
from application.exchange import setup_messaging


app = Flask(__name__)
app.config.from_object('config.Config')

setup_logging(app.config)
producer = setup_messaging(app.config)
