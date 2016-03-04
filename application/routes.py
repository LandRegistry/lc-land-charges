from application import app, producer
from application.exchange import publish_new_bankruptcy, publish_amendment, publish_cancellation
from application.logformat import format_message
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
    get_registrations_by_date, get_all_registrations, get_k22_request_id, get_registration_history, insert_migrated_cancellation
from application.schema import SEARCH_SCHEMA, validate, validate_registration, validate_migration, validate_update
from application.search import store_search_request, perform_search, store_search_result, read_searches, get_search_by_request_id
from application.oc import get_ins_office_copy
import datetime


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
    # hostname = "amqp://{}:{}@{}:{}".format(app.config['MQ_USERNAME'], app.config['MQ_PASSWORD'],
    #                                        app.config['MQ_HOSTNAME'], app.config['MQ_PORT'])
    # connection = kombu.Connection(hostname=hostname)
    # connection.SimpleQueue('errors').put(error)
    # logging.warning(format_message('Error successfully raised.'))
    logging.error(format_message(error))


@app.errorhandler(Exception)
def error_handler(err):
    logging.error(format_message('Unhandled exception: ' + str(err)))
    call_stack = traceback.format_exc()

    lines = call_stack.split("\n")
    for line in lines:
        logging.error(format_message(line))

    error = {
        "type": "F",
        "message": str(err),
        "stack": call_stack
    }
    raise_error(error)
    return Response(json.dumps(error), status=500)


@app.before_request
def before_request():
    logging.info(format_message("BEGIN %s %s [%s]"),
                 request.method, request.url, request.remote_addr)


@app.after_request
def after_request(response):
    # logging.info('END %s %s [%s] (%s) -- %s',
    #              request.method, request.url, request.remote_addr, request.__hash__(),
    #              response.status)
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
        logging.warning(format_message("Returning 404 for date {}".format(date)))
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
        logging.warning(format_message("Returning 404 for /registrations"))
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
        logging.warning(format_message("Returning 404 for /registrations/{}/{}".format(date, reg_no)))
        return Response(status=404)
    else:
        return Response(json.dumps(details), status=200, mimetype='application/json')


@app.route('/history/<date>/<int:reg_no>', methods=['GET'])
def registration_history(date, reg_no):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        details = get_registration_history(cursor, reg_no, date)
    finally:
        complete(cursor)
    if details is None:
        logging.warning("Returning 404")
        return Response(status=404)
    else:
        return Response(json.dumps(details), status=200, mimetype='application/json')



@app.route('/registrations', methods=['POST'])
def register():

    logging.info(format_message("Received registration data: %s"), request.data.decode('utf-8'))
    suppress = False
    if 'suppress_queue' in request.args:
        logging.info(format_message('Queue suppressed'))
        suppress = True

    if request.headers['Content-Type'] != "application/json":
        raise_error({
            "type": "E",
            "message": "Received invalid input data (non-JSON)",
            "stack": ""
        })
        logging.error(format_message('Content-Type is not JSON'))
        return Response(status=415)

    json_data = request.get_json(force=True)
    logging.debug(json.dumps(json_data))
    errors = validate_registration(json_data)
    if 'dev_date' in request.args and app.config['ALLOW_DEV_ROUTES']:
        logging.warning(format_message('Overriding date'))
        json_data['dev_registration'] = {
            'date': request.args['dev_date']
        }

    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
        logging.error(format_message("Input data failed validation"))
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # pylint: disable=unused-variable
    try:
        new_regns, details_id, request_id = insert_new_registration(cursor, json_data)
        complete(cursor)
        logging.info(format_message("Registration committed"))
    except:
        rollback(cursor)
        raise

    if not suppress:
        publish_new_bankruptcy(producer, new_regns)

    reg_type = 'new_registrations'
    if 'priority_notice' in json_data and json_data['priority_notice']:
        reg_type = 'priority_notices'

    return Response(json.dumps({reg_type: new_regns, 'request_id': request_id}), status=200,
                    mimetype='application/json')


@app.route('/registrations/<date>/<reg_no>', methods=["PUT"])
def amend_registration(date, reg_no):
    # Amendment... we're being given the replacement data
    if request.headers['Content-Type'] != "application/json":
        logging.error(format_message('Content-Type is not JSON'))
        return Response(status=415)

    suppress = False
    if 'suppress_queue' in request.args:
        logging.info(format_message('Queue suppressed'))
        suppress = True

    json_data = request.get_json(force=True)
    if 'pab_amendment' in json_data:
        pab_amendment = json_data['pab_amendment']
        del json_data['pab_amendment']
    else:
        pab_amendment = None
    errors = validate_update(json_data)
    if 'dev_date' in request.args and app.config['ALLOW_DEV_ROUTES']:
        logging.warning(format_message('Overriding date'))
        json_data['dev_registration'] = {
            'date': request.args['dev_date']
        }

    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
        logging.error(format_message("Input data failed validation"))
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

    # TODO: may need to revisit if business rules for rectification differs to amendment
    # if appn_type == 'amend':
    # originals, reg_nos, rows = insert_amendment(cursor, reg_no, date, json_data)
    # else:
    try:
        originals, reg_nos, request_id = insert_rectification(cursor, reg_no, date, json_data, None)
        data = {
            "new_registrations": reg_nos,
            "amended_registrations": originals,
            "request_id": request_id
        }
        if pab_amendment is not None:
            reg_no = pab_amendment['reg_no']
            date = pab_amendment['date']
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            amendment = {'reg_no': data['new_registrations'][0]['number'],
                         'date': today}
            originals, reg_nos, request_id = insert_rectification(cursor, reg_no, date, json_data, amendment)
            data['amended_registrations'].append(originals)
        complete(cursor)
        logging.info(format_message("Alteration committed"))
    except:
        rollback(cursor)
        raise

    return Response(json.dumps(data), status=200)


@app.route('/cancellations', methods=["POST"])
def cancel_registration():
    if request.headers['Content-Type'] != "application/json":
        logging.error('Content-Type is not JSON')
        return Response(status=415)

    suppress = False
    if 'suppress_queue' in request.args:
        logging.info(format_message('Queue suppressed'))
        suppress = True
    json_data = json.loads(request.data.decode('utf-8'))
    logging.debug("Received: %s", json_data)
    reg = json_data['registration']
    logging.debug("Reg: %s", reg)
    reg_no = json_data['registration_no']
    reg_date = json_data['registration']['date']
    rows, nos, canc_request_id = insert_cancellation(reg_no, reg_date, json_data)
    if rows == 0:
        return Response(status=404)
    else:
        data = {
            "cancellations": nos, "request_id": canc_request_id
        }
        if not suppress:
            publish_cancellation(producer, nos)
        return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/court_check/<court>/<ref>/<year>', methods=['GET'])
def court_ref_existence_check(court, ref, year):
    logging.debug("Court existence checking")
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("SELECT registration_no, date FROM register r, register_details rd " +
                       "WHERE UPPER(rd.legal_body)=%(court)s AND UPPER(rd.legal_body_ref_no)=%(ref)s " +
                       "AND rd.legal_body_ref_year=%(year)s AND rd.id=r.details_id",
                       {"court": court.upper(), "ref": ref.upper(), "year": int(year)})
        rows = cursor.fetchall()
        results = []
        if len(rows) > 0:
            status_code = 200
            for row in rows:
                details = get_registration_details(cursor, row['registration_no'], row['date'])
                debtor_name = details['parties'][0]['names'][0]['private']
                name_string = " ".join(debtor_name['forenames']) + " " + debtor_name['surname']
                results.append({'reg_no': details['registration']['number'],
                                'date': details['registration']['date'],
                                'class_of_charge': details['class_of_charge'],
                                'name': name_string})
        else:
            status_code = 404
    finally:
        complete(cursor)

    return Response(json.dumps(results), status=status_code, mimetype='application/json')


# ============== Searches ===============


@app.route('/searches', methods=['POST'])
def create_search():
    if request.headers['Content-Type'] != "application/json":
        logging.error(format_message('Content-Type is not JSON'))
        return Response(status=415)

    data = request.get_json(force=True)
    logging.debug('this is search data', json.dumps(data))
    errors = validate(data, SEARCH_SCHEMA)
    if errors is not None:
        return Response(json.dumps(errors), status=400)
    logging.debug(data['parameters']['search_type'])
    if data['parameters']['search_type'] not in ['full', 'banks']:
        message = "Invalid search type supplied: {}".format(data['parameters']['search_type'])
        logging.error(format_message(message))
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
        logging.info(format_message("Search request and result comitted"))
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
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

    try:
        if 'name' in request.args:
            name = request.args['name']
            result = read_searches(cursor, name)

        elif 'id' in request.args:
            result = get_search_by_request_id(cursor, request.args['id'])

        else:
            result = []

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
        logging.error(format_message('Content-Type is not JSON'))
        return Response(status=415)

    data = request.get_json(force=True)
    errors = validate_migration(data)
    if len(errors) > 0:
        raise_error({
            "type": "E",
            "message": "Input data failed validation",
            "stack": ""
        })
        logging.error(format_message("Input data failed validation"))
        return Response(json.dumps(errors), status=400, mimetype='application/json')

    previous_id = None
    first_record = data[0]
    for reg in data:
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
        try:
            if reg['type'] == 'CN':
                details_id, request_id = insert_migrated_cancellation(cursor, data)
            else:
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

                    # TODO repeating code is bad.
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

                    if reg['type'] == 'CP':
                        cursor.execute("UPDATE register_details SET amends = %(amend)s, amendment_type=%(type)s WHERE " +
                                       "id = %(id)s",
                                       {
                                           "amend": previous_id, "id": details_id, "type": "Part Cancellation"
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
        logging.error(format_message('Content-Type is not JSON'))
        return Response(status=415)

    json_data = request.get_json(force=True)
    publish_new_bankruptcy(producer, json_data)
    return Response(status=200)


@app.route('/counties', methods=['POST'])
def load_counties():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    if request.headers['Content-Type'] != "application/json":
        logging.error(format_message('Content-Type is not JSON'))
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
        if request_type.lower() in ('search'):
            data = get_search_request_details(request_id)
        else:  # not a search - reg register details
            data = get_register_request_details(request_id)
            details = get_registration_details(cursor, data[0]["registration_no"], data[0]["registration_date"])
            data[0]['details'] = details
    finally:
        complete(cursor)
    return Response(json.dumps(data), status=200, mimetype='application/json')


# Get request id for a registration
@app.route('/request_details', methods=["GET"])
def get_request_id():
    if 'registration_no' in request.args:
        reg_no = request.args['registration_no']
    else:
        return Response(json.dumps({'error': 'no registration_no'}), status=400)
    if 'registration_date' in request.args:
        reg_date = request.args['registration_date']
    else:
        return Response(json.dumps({'error': 'no registration_date'}), status=400)
    if 'reprint_type' in request.args:
        reprint_type = request.args['reprint_type']
    else:
        return Response("no reprint_type specified", status=400)
    request_id = 0
    if reprint_type == 'registration':
        request_id = get_k22_request_id(reg_no, reg_date)
    elif reprint_type == 'search':
        request_id = 0  # write method to get k17/18 request ids

    return Response(json.dumps(request_id), status=200, mimetype='application/json')


# Get request id for a search
@app.route('/request_search_details', methods=["POST"])
def get_search_request_ids():
    post_data = json.loads(request.data.decode('utf-8'))
    data = post_data
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    sql = " select a.id as request_id, b.search_timestamp, c.name_type, c.forenames, c.surname, c.complex_name, " \
          " c.complex_number, c.local_authority_name, c.local_authority_area, c.other_name, c.company_name," \
          " c.year_from, c.year_to " \
          " from request a, search_details b, search_name c where a.key_number =  %(key_number)s" \
          " and a.id = b.request_id and b.search_timestamp >= %(date_from)s and b.search_timestamp <= %(date_to)s " \
          " and b.id = c.details_id "
    date_from = datetime.datetime.strptime(data['date_from'], '%Y-%m-%d')
    date_from = date_from + datetime.timedelta(days=-1)
    date_to = datetime.datetime.strptime(data['date_to'], '%Y-%m-%d')
    date_to = date_to + datetime.timedelta(days=1)
    params = {"key_number": data['key_number'], "date_from": date_from, "date_to": date_to}
    if data['estate_owner_ind'].lower() == "privateindividual":
        forenames = ""
        for forename in data['estate_owner']['private']['forenames']:
            forenames += forename.upper() + " "
        if not forenames.strip() == "":
            sql += " and UPPER(c.forenames) = %(forenames)s "
            params['forenames'] = forenames.strip()
        if not data['estate_owner']['private']['surname'].strip() == "":
            sql += " and UPPER(c.surname) = %(surname)s "
            params['surname'] = data['estate_owner']['private']['surname'].upper()
    if data['estate_owner_ind'].lower() == "countycouncil":
        if not data['estate_owner']['local']['name'] == "":
            sql += " and UPPER(c.local_authority_name) = %(local_authority_name)s "
            params['local_authority_name'] = data['estate_owner']['local']['name'].upper()
        if not data['estate_owner']['local']['area'] == "":
            sql += " and UPPER(c.local_authority_area) = %(local_authority_area)s "
            params['local_authority_area'] = data['estate_owner']['local']['area'].upper()
    if data['estate_owner_ind'].lower() == "localauthority":
        if not data['estate_owner']['local']['name'] == "":
            sql += " and UPPER(c.local_authority_name) = %(local_authority_name)s "
            params['local_authority_name'] = data['estate_owner']['local']['name'].upper()
        if not data['estate_owner']['local']['area'] == "":
            sql += " and UPPER(c.local_authority_area) = %(local_authority_area)s "
            params['local_authority_area'] = data['estate_owner']['local']['area'].upper()
    if data['estate_owner_ind'].lower() == "other":
        if not data['estate_owner']['other'] == "":
            sql += " and UPPER(c.other_name) = %(other_name)s "
            params['other_name'] = data['estate_owner']['other'].upper()
    if data['estate_owner_ind'].lower() == 'limitedcompany':
        if not data['estate_owner']['company'] == "":
            sql += " and UPPER(c.company_name) = %(company_name)s "
            params['company_name'] = data['estate_owner']['company'].upper()
    if data['estate_owner_ind'].lower() == 'complexname':
        if not data['estate_owner']['complex']['name'] == "":
            sql += " and UPPER(c.complex_name) = %(complex_name)s "
            params['complex_name'] = data['estate_owner']['complex']['name'].upper()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    results = {'results': []}
    request_ids = []
    for row in rows:
        # if not row['request_id'] in request_ids:
        res = {'request_id': row['request_id'], 'name_type': row['name_type'],
               'search_timestamp': str(row['search_timestamp']),
               'estate_owner': {'private': {"forenames": row['forenames'], "surname": row['surname']},
                                'local': {'name': row['local_authority_name'], "area": row['local_authority_area']},
                                'complex': {"name": row['complex_name'], "number": row['complex_number']},
                                "other": row['other_name'], "company": row['company_name']}}
        results['results'].append(res)
        request_ids.append(row['request_id'])
    return Response(json.dumps(results), status=200, mimetype='application/json')


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
        cursor.execute(sql, {"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    search_type = {'search_type': 'search nr'}
    for row in rows:
        if row['result']:
            search_type = {'search_type': 'search'}
    return Response(json.dumps(search_type), status=200, mimetype='application/json')


# test route
@app.route('/last_search', methods=["GET"])
def last_search():
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # get all rows for this request id, if none contain results then search type is 'search_nr'
    data = {}
    try:
        sql = "Select id as search_details_id, request_id, search_timestamp " \
              "from search_details where id = (select max(id) from search_details) "
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    for row in rows:
        data = {'search_details_id': row['search_details_id'], 'request_id': row['request_id'],
                'timestamp': str(row['search_timestamp'])}
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/request_type/<request_id>', methods=["GET"])
def get_request_type(request_id):
    if not request_id:
        return "none"
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # get all rows for this request id, if none contain results then search type is 'search_nr'
    try:
        cursor.execute("Select application_type "
                       "from request where id = %(request_id)s ", {"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    data = ""
    if rows:
        for row in rows:
            data = row['application_type']
    else:
        logging.error("could not find request " + request_id)
        return "none"
    return data


@app.route('/area_variants', methods=['PUT'])
def set_area_variants():
    data = json.loads(request.data.decode('utf-8'))
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    for item in data:
        cursor.execute('INSERT INTO county_search_keys (name, key, variant_of, county_council) '
                       'VALUES( %(name)s, %(key)s, %(variant)s, %(county)s )', {
                           'name': item['name'], 'key': item['key'],
                           'variant': item['variant_of'], 'county': item['county_council']
                       })
    complete(cursor)
    return Response(status=200)


@app.route('/area_variants', methods=['DELETE'])
def clear_area_variants():
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('DELETE FROM county_search_keys')
    complete(cursor)
    return Response(status=200)