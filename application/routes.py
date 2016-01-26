from application import app, producer
from application.exchange import publish_new_bankruptcy, publish_amendment, publish_cancellation
from flask import Response, request
import psycopg2
import psycopg2.extras
import json
import logging
import traceback
import kombu
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from application.data import connect, get_registration_details, complete, \
    get_registration, insert_migrated_record, insert_cancellation,  \
    insert_amendment, insert_new_registration, get_req_details, rollback
from application.schema import SEARCH_SCHEMA, validate, BANKRUPTCY_SCHEMA, LANDCHARGE_SCHEMA
from application.search import store_search_request, perform_search, store_search_result, read_searches


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


@app.route('/health', methods=['GET'])
def health():
    result = {
        'status': 'OK',
        'dependencies': {}
    }
    return Response(json.dumps(result), status=200, mimetype='application/json')


def raise_error(error):
    hostname = "amqp://{}:{}@{}:{}".format(app.config['MQ_USERNAME'], app.config['MQ_PASSWORD'],
                                           app.config['MQ_HOSTNAME'], app.config['MQ_PORT'])
    connection = kombu.Connection(hostname=hostname)
    connection.SimpleQueue('errors').put(error)
    logging.warning('Error successfully raised.')


@app.errorhandler(Exception)
def error_handler(err):
    logging.error('Unhandled exception: ' + str(err))
    call_stack = traceback.format_exc()

    lines = call_stack.split("\n")
    for line in lines:
        logging.error(line)

    error = {
        "type": "F",
        "message": str(err),
        "stack": call_stack
    }
    raise_error(error)
    return Response(json.dumps(error), status=500)


@app.before_request
def before_request():
    logging.info("BEGIN %s %s [%s] (%s)",
                 request.method, request.url, request.remote_addr, request.__hash__())


@app.after_request
def after_request(response):
    logging.info('END %s %s [%s] (%s) -- %s',
                 request.method, request.url, request.remote_addr, request.__hash__(),
                 response.status)
    return response

# ============== /registrations ===============

@app.route('/registrations/<date>/<int:reg_no>', methods=['GET'])
def registration(date, reg_no):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        details = get_registration_details(cursor, reg_no, date)
    finally:
        complete(cursor)
    if details is None:
        logging.warning("Returning 404")
        return Response(status=404)
    else:
        return Response(json.dumps(details), status=200, mimetype='application/json')


@app.route('/registrations', methods=['POST'])
def register():
    suppress = False
    if 'suppress_queue' in request.args:
        logging.info('Queue suppressed')
        suppress = True

    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    json_data = request.get_json(force=True)
    if 'lc_register_details' in json_data:
        errors = validate(json_data, LANDCHARGE_SCHEMA)
    else:
        errors = validate(json_data, BANKRUPTCY_SCHEMA)

    if len(errors) > 0:
        logging.error("Input data failed validation")
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # pylint: disable=unused-variable
    try:
        new_regns, details_id, request_id = insert_new_registration(cursor, json_data)
        complete(cursor)
    except:
        rollback(cursor)
        raise

    if not suppress:
        publish_new_bankruptcy(producer, new_regns)

    return Response(json.dumps({'new_registrations': new_regns, 'request_id': request_id}), status=200)


@app.route('/registrations/<date>/<reg_no>', methods=["PUT"])
def amend_registration(date, reg_no):
    # Amendment... we're being given the replacement data
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    suppress = False
    if 'suppress_queue' in request.args:
        logging.info('Queue suppressed')
        suppress = True

    json_data = request.get_json(force=True)
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

    # TODO: may need to revisit if business rules for rectification differs to amendment
    # if appn_type == 'amend':
    originals, reg_nos, rows = insert_amendment(cursor, reg_no, date, json_data)
    # else:
    # originals, reg_nos, rows = insert_rectification(cursor, reg_no, json_data)

    if rows is None or rows == 0:
        cursor.connection.rollback()
        cursor.close()
        cursor.connection.close()
        return Response(status=404)
    else:
        complete(cursor)
        data = {
            "new_registrations": reg_nos,
            "amended_registrations": originals
        }
        if not suppress:
            publish_amendment(producer, data)

        return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/registrations/<date>/<reg_no>', methods=["DELETE"])
def cancel_registration(date, reg_no):
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    suppress = False
    if 'suppress_queue' in request.args:
        logging.info('Queue suppressed')
        suppress = True

    json_data = request.get_json(force=True)
    rows, nos = insert_cancellation(reg_no, date, json_data)
    if rows == 0:
        return Response(status=404)
    else:
        data = {
            "cancelled": nos
        }
        if not suppress:
            publish_cancellation(producer, nos)
        return Response(json.dumps(data), status=200, mimetype='application/json')


# ============== Searches ===============


@app.route('/searches', methods=['POST'])
def create_search():
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    data = request.get_json(force=True)
    errors = validate(data, SEARCH_SCHEMA)
    if len(errors) > 0:
        return Response(json.dumps(errors), status=400)

    if data['parameters']['search_type'] not in ['full', 'banks']:
        message = "Invalid search type supplied"
        logging.error(message)
        return Response(message, status=400)

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Store the search request
        search_request_id = store_search_request(cursor, data)

        # name_string = "{} {}".format(name['private']['forenames'], name['private']['surname'])
        # Run the queries
        # results = perform_search(cursor, data['parameters'])
        # print(results)

        # store_search_result(cursor, search_request_id, results)

        complete(cursor)
    except:
        rollback(cursor)
        raise
    results = [search_request_id]
    if len(results) == 0:
        return Response(status=404)
    else:
        return Response(json.dumps(results, ensure_ascii=False), status=200, mimetype='application/json')

        
@app.route('/searches', methods=['GET'])
def get_searches():
    nonissued = False
    if 'filter' in request.args:
        nonissued = (request.args['filter'] == 'nonissued')
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        result = read_searches(cursor, nonissued)
    finally:
        complete(cursor)

    return Response(json.dumps(result), status=200, mimetype='application/json')


migrated_schema = {
    "type": "object",
    "properties": {
        "application_type": {"type": "string"},
        "application_ref": {"type": "string"},
        "date": {"type": "string", "pattern": "^([0-9]{4}-[0-9]{2}-[0-9]{2})$"},
        "debtor_name": {
            "type": "object",
            "properties": {
                "forenames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "surname": {"type": "string"}
            },
            "required": ["forenames", "surname"]
        },
        "occupation": {"type": "string"},
        "residence": {
            "type": "array",
            "items": {"type": "object"}
        }
    },
    "required": ["application_type", "application_ref", "date", "debtor_name", "residence"]
}


@app.route('/migrated_record', methods=['POST'])
def insert():
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    data = request.get_json(force=True)
    # logging.info(data)
    # TODO: is there a need to validate the migration schema???
    """try:
        validate(data, migrated_schema)
    except ValidationError as error:
        message = "{}\n{}".format(error.message, error.path)
        return Response(message, status=400)"""

    previous_id = None
    for reg in data:
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
        try:
            details_id, request_id = insert_migrated_record(cursor, reg)
            if reg['type'] in ['AM', 'CN', 'CP', 'RN']:
                if details_id is not None:
                    cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                                   "id = %(id)s AND cancelled_by IS NULL",
                                   {
                                       "canc": request_id, "id": previous_id
                                   })
                else:
                    pass

                if reg['type'] == 'AM':
                    cursor.execute("UPDATE register_details SET amends = %(amend)s, amendment_type=%(type)s WHERE " +
                                   "id = %(id)s",
                                   {
                                       "amend": previous_id, "id": details_id, "type": "Amendment"
                                   })

                if reg['type'] == 'RN':
                    cursor.execute("UPDATE register_details SET amends = %(amend)s, amendment_type=%(type)s WHERE " +
                                   "id = %(id)s",
                                   {
                                       "amend": previous_id, "id": details_id, "type": "Renewal"
                                   })

            previous_id = details_id
            complete(cursor)
        except:
            rollback(cursor)
            raise

    return Response(status=200)


# ============= Dev routes ===============


@app.route('/registrations', methods=['DELETE'])
def delete_all_regs():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("DELETE FROM party_address")
        cursor.execute("DELETE FROM address")
        cursor.execute("DELETE FROM address_detail")
        cursor.execute("DELETE FROM party_trading")
        cursor.execute("DELETE FROM party_name_rel")
        cursor.execute("DELETE FROM party")
        cursor.execute("DELETE FROM migration_status")
        cursor.execute("DELETE FROM register")
        cursor.execute("DELETE FROM detl_county_rel")
        cursor.execute("DELETE FROM register_details")
        cursor.execute("DELETE FROM audit_log")
        cursor.execute("DELETE FROM search_details")
        cursor.execute("DELETE FROM request")
        cursor.execute("DELETE FROM ins_bankruptcy_request")
        cursor.execute("DELETE FROM party_name")
        cursor.execute("DELETE FROM county")
        complete(cursor)
    except:
        rollback(cursor)
        raise
    return Response(status=200)


# Route exists purely for testing purposes - need to get something invalid onto
# the synchroniser's queue!
@app.route('/synchronise', methods=["POST"])
def synchronise():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    json_data = request.get_json(force=True)
    publish_new_bankruptcy(producer, json_data)
    return Response(status=200)


@app.route('/counties', methods=['POST'])
def load_counties():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    json_data = request.get_json(force=True)
    cursor = connect()
    try:
        for item in json_data:
            if 'cym' not in item:
                item['cym'] = None

            cursor.execute('INSERT INTO COUNTY (name, welsh_name) VALUES (%(e)s, %(c)s)',
                           {
                               'e': item['eng'], 'c': item['cym']
                           })
        complete(cursor)
    except:
        rollback(cursor)
        raise

    return Response(status=200)


# Get details of a request for printing
@app.route('/request_details/<request_id>', methods=["GET"])
def get_request_details(request_id):
    reqs = get_req_details(request_id)
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        reg = get_registration_details(cursor, reqs[0]["registration_no"], reqs[0]["registration_date"])
    finally:
        complete(cursor)
    return Response(json.dumps(reg), status=200, mimetype='application/json')


# Route exists purely for testing purposes - get some valid request ids for test data
# count is the amount of ids to return
@app.route('/request_ids/<count>', methods=["GET"])
def get_request_ids(count):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        sql = "Select id as request_id from request fetch first " + str(count) + " rows only"
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    data = []
    if len(rows) == 0:
        data = None
    else:
        for row in rows:
            job = {'request_id': row['request_id']}
            data.append(job)
    return Response(json.dumps(data), status=200, mimetype='application/json')