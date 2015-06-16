from application import app
from flask import Response

@app.route('/', methods=["GET"])
def index():
	return Response(status=200)
