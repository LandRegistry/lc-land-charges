from application import app, producer
from application.exchange import publish_new_bankruptcy, publish_amendment, publish_cancellation
from flask import Response, request
import psycopg2
import psycopg2.extras
import json
import logging
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from application.data import connect, get_registration_details, complete, \
    get_registration, insert_migrated_record, insert_cancellation,  \
    insert_amendment, insert_new_registration
from application.schema import SEARCH_SCHEMA
from application.search import store_search_request, perform_search, store_search_result



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


# ============== /registrations ===============

@app.route('/registrations/<date>/<int:reg_no>', methods=['GET'])
def registration(date, reg_no):
    logging.debug("GET registration")

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    details = get_registration_details(cursor, reg_no, date)
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
    cursor = connect()
    # pylint: disable=unused-variable
    new_regns, details_id = insert_new_registration(cursor, json_data)
    complete(cursor)
    if not suppress:
        publish_new_bankruptcy(producer, new_regns)

    return Response(json.dumps({'new_registrations': new_regns}), status=200)


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
    cursor = connect()

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
        print(data)
        return Response(json.dumps(data), status=200, mimetype='application/json')


# ============== Searches ===============


@app.route('/searches', methods=['POST'])
def retrieve():
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    data = request.get_json(force=True)
    try:
        validate(data, SEARCH_SCHEMA)
    except ValidationError as error:
        message = "{}\n{}".format(error.message, error.path)
        logging.error(message)
        return Response(message, status=400)

    if data['parameters']['search_type'] not in ['full', 'bankruptcy']:
        message = "Invalid search type supplied"
        logging.error(message)
        return Response(message, status=400)

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # Store the search request
    search_request_id = store_search_request(cursor, data)

    # Run the queries
    results = perform_search(cursor, data['parameters'])

    store_search_result(cursor, search_request_id, results)

    complete(cursor)
    if len(results) == 0:
        return Response(status=404)
    else:
        return Response(json.dumps(results, ensure_ascii=False), status=200, mimetype='application/json')


# @app.route('/migrated_registration/<int:db2_reg_no>', methods=['GET'])
# def migrated_registration(db2_reg_no):
#     cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
#     new_reg_no = get_new_registration_number(cursor, db2_reg_no)
#
#     registrations = []
#     for number in new_reg_no:
#         registrations.append(get_registration_details(cursor, number))
#
#     complete(cursor)
#
#     if len(registrations) > 0:
#         return Response(json.dumps(registrations), status=200, mimetype='application/json')
#     else:
#         return Response(status=404)

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
    # TODO: is there a need to validate the migration schema???
    """try:
        validate(data, migrated_schema)
    except ValidationError as error:
        message = "{}\n{}".format(error.message, error.path)
        return Response(message, status=400)"""

    for reg in data:
        cursor = connect()
        details_id, request_id = insert_migrated_record(cursor, reg)
        if reg['type'] == 'AM' or reg['type'] == 'CN' or reg['type'] == 'CP':
            cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                           "id = %(id)s AND cancelled_by IS NULL",
                           {
                               "canc": request_id, "id": previous_id
                           })
            if reg['type'] == 'AM':
                cursor.execute("UPDATE register_details SET amends = %(amend)s WHERE " +
                               "id = %(id)s",
                               {
                                   "amend": previous_id, "id": details_id
                               })

        previous_id = details_id
        complete(cursor)

    return Response(status=200)


# ============= Dev routes ===============


@app.route('/registrations', methods=['DELETE'])
def delete_all_regs():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    cursor = connect()
    cursor.execute("DELETE FROM party_address")
    cursor.execute("DELETE FROM address")
    cursor.execute("DELETE FROM address_detail")
    cursor.execute("DELETE FROM party_trading")
    cursor.execute("DELETE FROM party_name_rel")
    cursor.execute("DELETE FROM party")
    cursor.execute("DELETE FROM migration_status")
    cursor.execute("DELETE FROM register")
    cursor.execute("DELETE FROM register_details")
    cursor.execute("DELETE FROM audit_log")
    cursor.execute("DELETE FROM search_details")
    cursor.execute("DELETE FROM request")
    cursor.execute("DELETE FROM ins_bankruptcy_request")
    cursor.execute("DELETE FROM party_name")
    cursor.execute("DELETE FROM counties")
    complete(cursor)
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