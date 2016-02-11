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
    insert_rectification, insert_new_registration, get_register_request_details, get_search_request_details, rollback, \
    get_registrations_by_date, get_all_registrations
from application.schema import SEARCH_SCHEMA, validate, validate_registration, validate_migration, validate_update
from application.search import store_search_request, perform_search, store_search_result, read_searches
from application.oc import get_ins_office_copy


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


@app.route('/registrations/<date>', methods=['GET'])
def registrations_by_date(date):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        details = get_registrations_by_date(cursor, date)
    finally:
        complete(cursor)
    if details is None:
        logging.warning("Returning 404")
        return Response(status=404)
    else:
        return Response(json.dumps(details), status=200, mimetype='application/json')


@app.route('/registrations', methods=['GET'])
def all_registrations():
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        details = get_all_registrations(cursor)
    finally:
        complete(cursor)
    if details is None:
        logging.warning("Returning 404")
        return Response(status=404)
    else:
        return Response(json.dumps(details), status=200, mimetype='application/json')
        

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

    logging.info("Received: %s", request.data.decode('utf-8'))
    suppress = False
    if 'suppress_queue' in request.args:
        logging.info('Queue suppressed')
        suppress = True

    if request.headers['Content-Type'] != "application/json":
        raise_error({
            "type": "E",
            "message": "Received invalid input data (non-JSON)",
            "stack": ""
        })
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    json_data = request.get_json(force=True)

    errors = validate_registration(json_data)
    if 'dev_date' in request.args and app.config['ALLOW_DEV_ROUTES']:
        logging.info('Overriding date')
        json_data['dev_registration'] = {
            'date': request.args['dev_date']
        }

    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
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

    reg_type = 'new_registrations'
    if 'priority_notice' in json_data and json_data['priority_notice']:
        reg_type = 'priority_notices'

    return Response(json.dumps({reg_type: new_regns, 'request_id': request_id}), status=200, mimetype='application/json')


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
    errors = validate_update(json_data)
    if 'dev_date' in request.args and app.config['ALLOW_DEV_ROUTES']:
        logging.info('Overriding date')
        json_data['dev_registration'] = {
            'date': request.args['dev_date']
        }

    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
        logging.error("Input data failed validation")
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

    # TODO: may need to revisit if business rules for rectification differs to amendment
    # if appn_type == 'amend':
    # originals, reg_nos, rows = insert_amendment(cursor, reg_no, date, json_data)
    # else:
    originals, reg_nos = insert_rectification(cursor, reg_no, date, json_data)

    complete(cursor)
    data = {
        "new_registrations": reg_nos,
        "amended_registrations": originals
    }
    return Response(json.dumps(data), status=200)



    # if rows is None or rows == 0:
    #     cursor.connection.rollback()
    #     cursor.close()
    #     cursor.connection.close()
    #     return Response(status=404)
    # else:

    #     if not suppress:
    #         publish_amendment(producer, data)
    #
    #     return Response(json.dumps(data), status=200, mimetype='application/json')


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
    print('this is search data', json.dumps(data))
    errors = validate(data, SEARCH_SCHEMA)
    if errors is not None:
        return Response(json.dumps(errors), status=400)
    print(data['parameters']['search_type'])
    if data['parameters']['search_type'] not in ['full', 'banks']:
        message = "Invalid search type supplied: {}".format(data['parameters']['search_type'])
        logging.error(message)
        return Response(message, status=400)

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Store the search request
        search_request_id, search_details_id, search_data = store_search_request(cursor, data)

        # Run the queries
        results = perform_search(cursor, search_data['parameters'], search_data['search_date'])
        for item in results:
            store_search_result(cursor, search_request_id, search_details_id, item['name_id'], item['name_result'])

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
    name = request.args['name']
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        result = read_searches(cursor, name)
        data = []
        for results in result:
            for ids in results['result']:
                reg_data = get_registration(cursor, ids, None)
                data.append({'reg_id': ids,
                             'reg_no': reg_data['registration_no'],
                             'reg_date': reg_data['registration_date'],
                             'class': reg_data['class_of_charge']
                             })
    finally:
        complete(cursor)

    return Response(json.dumps(data), status=200, mimetype='application/json')


# ============== Office Copies ===============


@app.route('/office_copy', methods=['GET'])
def retrieve_office_copy():
    class_of_charge = request.args['class']
    reg_no = request.args['reg_no']
    date = request.args['date']

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        data = get_ins_office_copy(cursor, class_of_charge, reg_no, date)
    finally:
        complete(cursor)

    if data is None:
        return Response(data, status=404, mimetype='application/json')
    else:
        return Response(data, status=200, mimetype='application/json')


@app.route('/migrated_record', methods=['POST'])
def insert():
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    data = request.get_json(force=True)
    errors = validate_migration(data)
    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
        logging.error("Input data failed validation")
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    previous_id = None
    for reg in data:
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
        try:
            details_id, request_id = insert_migrated_record(cursor, reg)
            if reg['type'] in ['AM', 'CN', 'CP', 'RN', 'RC']:
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
                                   
                if reg['type'] == 'RC':
                    cursor.execute("UPDATE register_details SET amends = %(amend)s, amendment_type=%(type)s WHERE " +
                                   "id = %(id)s",
                                   {
                                       "amend": previous_id, "id": details_id, "type": "Rectification"
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
        cursor.execute("DELETE FROM search_results")
        cursor.execute("DELETE FROM search_name")
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


@app.route('/counties', methods=['GET'])
def get_counties_list():
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    welsh_req = ""
    try:
        if 'welsh' in request.args:
            welsh_req = request.args['welsh']

        if welsh_req == "yes":
            cursor.execute("SELECT name, welsh_name FROM COUNTY")
        else:
            cursor.execute("SELECT name FROM COUNTY")

        rows = cursor.fetchall()
        counties = list()
        for row in rows:
            counties.append(row['name'])
            if welsh_req == "yes" and row['welsh_name'] and (row['welsh_name'] != row['name']):
                counties.append(row['welsh_name'])
        counties.sort()
    finally:
        complete(cursor)
    return Response(json.dumps(counties), status=200, mimetype='application/json')


@app.route('/county/<county_name>', methods=['GET'])
def get_translated_county(county_name):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        counties = list()
        counties.append(county_name)

        cursor.execute("SELECT name FROM COUNTY where UPPER(welsh_name) = %(n)s", {'n': county_name.upper()})
        rows = cursor.fetchall()

        for row in rows:
            if row['name']:
                counties.append(row['name'])
        else:
            cursor.execute("SELECT welsh_name FROM COUNTY where UPPER(name) = %(n)s", {'n': county_name.upper()})
            rows = cursor.fetchall()

            for row in rows:
                if row['welsh_name']:
                    counties.append(row['welsh_name'])
    finally:
        complete(cursor)
    return Response(json.dumps(counties), status=200, mimetype='application/json')


# Get details of a request for printing
@app.route('/request_details/<request_id>', methods=["GET"])
def get_request_details(request_id):
    request_type = get_request_type(request_id)
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        if request_type.lower() == 'new registration':
            data = get_register_request_details(request_id)
            details = get_registration_details(cursor, data[0]["registration_no"], data[0]["registration_date"])
            data[0]['details'] = details
        elif request_type.lower() == 'search':
            print('call search request')
            data = get_search_request_details(request_id)
        else:
            return Response("invalid request_type " + request_type, status=500)
    finally:
        complete(cursor)
    return Response(json.dumps(data), status=200, mimetype='application/json')


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


@app.route('/search_type/<request_id>', methods=["GET"])
def get_search_type(request_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # get all rows for this request id, if none contain results then search type is 'search_nr'
    try:
        sql = "Select result from search_results where request_id = %(request_id)s"
        cursor.execute(sql,{"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    search_type = {'search_type':'search nr'}
    for row in rows:
        if row['result']:
            search_type = {'search_type':'search'}
    return Response(json.dumps(search_type), status=200,mimetype='application/json')


# test route
@app.route('/last_search', methods=["GET"])
def last_search():
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # get all rows for this request id, if none contain results then search type is 'search_nr'
    try:
        sql = "Select id as search_details_id, request_id, search_timestamp " \
              "from search_details where id = (select max(id) from search_details) "
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    for row in rows:
        data = {'search_details_id':row['search_details_id'], 'request_id': row['request_id'],
                'timestamp': str(row['search_timestamp'])}
    return Response(json.dumps(data), status=200, mimetype='application/json')


def get_request_type(request_id):
   cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
   # get all rows for this request id, if none contain results then search type is 'search_nr'
   try:
       cursor.execute("Select application_type " \
             "from request where id = %(request_id)s ",
                  {
                      "request_id": request_id,
                  })
       rows = cursor.fetchall()
   finally:
       complete(cursor)
   for row in rows:
       data = row['application_type']
   return data
