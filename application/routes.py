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

    data = (request.get_json(force=True))
    forenames = data['debtor_name']['forenames']
    surname = data['debtor_name']['surname']
    del data['debtor_name']
    surname.strip()

    name_str = ''
    for item in forenames:
        name_str += '%s ' % item.strip()
    data = json.dumps(data)
    name_str.strip()

    try:
        connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        print(error)
        return Response("Failed to connect to database: {}".format(error), status=500)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO temp (banks, forename, surname) VALUES (%(json)s, %(forename)s, %(surname)s)",
                       {"json": data, "forename": name_str, "surname": surname})
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


@app.route('/search', methods=["POST"])
def search():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    data = (request.get_json(force=True))
    forenames = data['forenames']
    surname = data['surname']

    try:
        connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        print(error)
        return Response("Failed to connect to database", status=500)

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, forename, surname, banks FROM temp "
            "WHERE trim(both ' ' from forename)=%(forename)s AND surname=%(surname)s",
            {"forename": forenames, "surname": surname})
    except Exception as error:
        print(error)
        return Response("Failed to select from database", status=500)

    rows = cursor.fetchall()
    if len(rows) == 0:
        return Response(status=404)

    data = json.dumps(rows, ensure_ascii=False)
    print(type(data))
    print(data)

    return Response(data, status=200, mimetype='application/json')
