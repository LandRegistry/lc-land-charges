from application import app
from flask import Response, request
import psycopg2
import json


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


@app.route('/register', methods=["POST"])
def register():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    data = json.dumps(request.get_json(force=True))
    try:
        connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        print(error)
        return Response("Failed to connect to database: {}".format(error), status=500)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO temp (banks) VALUES (%(json)s)", {"json": data})
    except Exception as error:
        return Response("Failed to insert to database: {}".format(error), status=500)

    connection.commit()
    cursor.close()
    connection.close()
    return Response(status=202)


@app.route('/search/<int:id>', methods=["GET"])
def get(id):
    try:
        connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        print(error)
        return Response("Failed to connect to database", status=500)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT banks FROM temp WHERE id=%(id)s", {"id": id})
    except Exception as error:
        print(error)
        return Response("Failed to select from database", status=500)

    rows = cursor.fetchall()
    if len(rows) == 0:
        return Response(status=404)

    data = json.dumps(rows[0][0], ensure_ascii=False)
    print(type(data))
    print(data)

    return Response(data, status=200, mimetype='application/json')
