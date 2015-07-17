from application import app, producer
from application.exchange import setup_messaging, publish_new_bankruptcy
from flask import Response, request
import psycopg2
import psycopg2.extras
import json
import re
import sys
from log.logger import logger
from jsonschema import validate
from jsonschema.exceptions import ValidationError

@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


def connect(cursor_factory=None):
    connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
        app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
        app.config['DATABASE_PASSWORD']))
    return connection.cursor(cursor_factory=cursor_factory)


def complete(cursor):
    cursor.connection.commit()
    cursor.close()
    cursor.connection.close()


def insert_address(cursor, address, address_type, party_id):
    if 'address_lines' in address:
        lines = address['address_lines'][0:4]   # First four lines
        remaining = ", ".join(address['address_lines'][4:])
        if remaining != '':
            lines.append(remaining)             # Remaining lines into 5th line
        lines.append(address['postcode'])       # Postcode in the last

        while len(lines) < 6:
            lines.append("")                    # Pad to 6 lines for avoidance of horrible if statements later

        cursor.execute("INSERT INTO address_detail ( line_1, line_2, line_3, line_4, line_5, line_6 ) " +
                       "VALUES( %(line1)s, %(line2)s, %(line3)s, %(line4)s, %(line5)s, %(line6)s ) " +
                       "RETURNING id",
                       {
                           "line1": lines[0], "line2": lines[1], "line3": lines[2],
                           "line4": lines[3], "line5": lines[4], "line6": lines[5],
                       })
        detail_id = cursor.fetchone()[0]

        address_string = "{}, {}".format(", ".join(address['address_lines']), address["postcode"])
    elif 'text' in address:
        address_string = address['text']
        detail_id = None
    else:
        raise Exception('Invalid address object')

    cursor.execute("INSERT INTO address (address_type, address_string, detail_id) " +
                   "VALUES( %(type)s, %(string)s, %(detail)s ) " +
                   "RETURNING id",
                   {
                       "type": address_type,
                       "string": address_string,
                       "detail": detail_id
                   })
    address['id'] = cursor.fetchone()[0]

    cursor.execute("INSERT INTO party_address (address_id, party_id) " +
                   "VALUES ( %(address)s, %(party)s ) RETURNING id",
                   {
                       "address": address['id'], "party": party_id
                   })
    return address['id']


def insert_name(cursor, name, party_id, is_alias=False):
    name_string = "{} {}".format(" ".join(name['forenames']), name['surname'])
    forename = name['forenames'][0]
    middle_names = " ".join(name['forenames'][1:])
    cursor.execute("INSERT INTO party_name ( party_name, forename, " +
                   "middle_names, surname, alias_name ) " +
                   "VALUES ( %(name)s, %(forename)s, %(midnames)s, %(surname)s, %(alias)s ) " +
                   "RETURNING id",
                   {
                       "name": name_string, "forename": forename, "midnames": middle_names,
                       "surname": name['surname'], "alias": is_alias
                   })
    name['id'] = cursor.fetchone()[0]

    cursor.execute("INSERT INTO party_name_rel (party_name_id, party_id) " +
                   "VALUES( %(name)s, %(party)s ) RETURNING id",
                   {
                       "name": name['id'], "party": party_id
                   })

    return name['id']


def insert_registration(cursor, details_id, name_id):
    # Get the next registration number
    cursor.execute("SELECT MAX(registration_no) FROM register", {})

    rows = cursor.fetchall()
    if rows[0][0] is None:
        reg_no = 50000
    else:
        reg_no = int(rows[0][0]) + 1

    # Cap it all off with the actual legal "one registration per name":
    cursor.execute("INSERT INTO register (registration_no, debtor_reg_name_id, details_id) " +
                   "VALUES( %(regno)s, %(debtor)s, %(details)s ) RETURNING id",
                   {
                       "regno": reg_no,
                       "debtor": name_id,
                       "details": details_id
                   })
    id = cursor.fetchone()[0]
    return reg_no, id


def insert_register_details(cursor, request_id, date, application_type):
    cursor.execute("INSERT INTO register_details (request_id, registration_date, application_type, " +
                   "bankruptcy_date) " +
                   "VALUES ( %(req_id)s, %(reg_date)s, %(app_type)s, %(bank_date)s ) " +
                   "RETURNING id",
                   {
                       "req_id": request_id, "reg_date": date,
                       "app_type": application_type, "bank_date": date
                   })   # TODO: Seems probable we won't need both dates
    return cursor.fetchone()[0]


def insert_request(cursor, key_number, application_type, reference, date, insolvency_id):
    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, " +
                   "ins_request_id) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(ins_id)s ) RETURNING id",
                   {
                       "key": key_number, "app_type": application_type, "app_ref": reference,
                       "app_date": date, "ins_id": insolvency_id
                   })
    return cursor.fetchone()[0]


def insert_party(cursor, details_id, party_type, occupation, date_of_birth, residence_withheld):
    cursor.execute("INSERT INTO party (register_detl_id, party_type, occupation, date_of_birth, residence_withheld) " +
                   "VALUES( %(reg_id)s, %(type)s, %(occupation)s, %(dob)s, %(rw)s ) RETURNING id",
                   {
                       "reg_id": details_id, "type": party_type, "occupation": occupation,
                       "dob": date_of_birth, "rw": residence_withheld
                   })
    return cursor.fetchone()[0]


def insert_migration_status(cursor, register_id, registration_number, additional_data):
    cursor.execute("INSERT INTO migration_status (register_id, original_regn_no, migration_complete, extra_data ) " +
                   "VALUES( %(register_id)s, %(reg_no)s, True, %(extra)s ) RETURNING id",
                   {
                       "register_id": register_id,
                       "reg_no": registration_number,
                       "extra": json.dumps(additional_data)
                   })
    return cursor.fetchone()[0]


def insert_record(data):
    cursor = connect()

    # ins_bankruptcy_request
    cursor.execute("INSERT INTO ins_bankruptcy_request (request_data) VALUES (%(json)s) RETURNING id",
                   {"json": json.dumps(data)})
    ins_request_id = cursor.fetchone()[0]

    app_type = re.sub(r"\(|\)", "", data["application_type"])

    # request
    request_id = insert_request(cursor, data['key_number'], app_type, data['application_ref'], data['date'],
                                ins_request_id)

    # register details
    register_details_id = insert_register_details(cursor, request_id, data['date'], app_type)

    # party
    party_id = insert_party(cursor, register_details_id, "Debtor", data['occupation'], data['date_of_birth'],
                            data['residence_withheld'])

    # party_address, address, address_detail
    if 'residence' in data:
        for address in data['residence']:
            insert_address(cursor, address, "Debtor Residence", party_id)

    if "business_address" in data:
        insert_address(cursor, data["business_address"], "Debtor Business", party_id)

    if "investment_property" in data:
        for address in data["investment_property"]:
            insert_address(cursor, address, "Investment", party_id)

    # party_name, party_name_rel
    name_ids = [insert_name(cursor, data['debtor_name'], party_id)]
    for name in data['debtor_alternative_name']:
        name_ids.append(insert_name(cursor, name, party_id, True))

    # party_trading
    if "trading_name" in data:
        cursor.execute("INSERT INTO party_trading (party_id, trading_name) " +
                       "VALUES ( %(party)s, %(trading)s ) RETURNING id",
                       {"party": party_id, "trading": data['trading_name']})

    # insert_registration(cursor, details_id, name_id)
    reg_nos = []
    for name_id in name_ids:
        reg_no, reg_id = insert_registration(cursor, register_details_id, name_id)
        reg_nos.append(reg_no)

    # TODO: audit-log not done. Not sure it belongs here?
    complete(cursor)

    return reg_nos


def get_registration_from_name(cursor, forenames, surname):
    fn_list = forenames.split(" ")
    forename = fn_list[0]
    middle_name = ""
    if len(forenames) > 1:
        middle_name = " ".join(fn_list[1:])

    cursor.execute("SELECT p.register_detl_id " +
                   "FROM party_name n, party_name_rel pr, party p " +
                   "where n.alias_name=False and UPPER(n.forename)=%(forename)s and UPPER(n.surname)=%(surname)s " +
                   "and UPPER(n.middle_names)=%(midname)s and n.id = pr.party_name_id and pr.party_id = p.id",
                   {
                       'forename': forename.upper(), 'midname': middle_name.upper(), 'surname': surname.upper()
                   })

    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append(row['register_detl_id'])

    return result


def get_registration(cursor, reg_id):
    cursor.execute("select r.registration_no, r.debtor_reg_name_id, rd.registration_date, rd.application_type, rd.id, " +
                   "r.id as register_id from register r, register_details rd " +
                   "where r.details_id = rd.id " +
                   "and r.id=%(id)s", {'id': reg_id})
    rows = cursor.fetchall()
    row = rows[0]
    result = {
        "registration_date": str(row['registration_date']),
        "application_type": row['application_type'],
        "registration_no": row['registration_no'],
    }
    return result


def get_new_registration_number(cursor, db2_reg_no):
    cursor.execute("select r.registration_no from register r, migration_status ms where r.id = ms.id"
                   " and ms.original_regn_no = %(reg_no)s", {'reg_no': db2_reg_no})
    rows = cursor.fetchall()
    # row = rows[0]
    reg_nos = []
    for n in rows:
        reg_nos.append(n['registration_no'])

    return reg_nos


def get_registration_details(cursor, reg_no):
    cursor.execute("select r.registration_no, r.debtor_reg_name_id, rd.registration_date, rd.application_type, rd.id, " +
                   "r.id as register_id from register r, register_details rd " +
                   "where r.registration_no = %(reg_no)s and r.details_id = rd.id", {'reg_no': reg_no})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    data = {
        'registration_no': rows[0]['registration_no'],
        'registration_date': str(rows[0]['registration_date']),
        'application_type': rows[0]['application_type']
    }
    details_id = rows[0]['id']
    name_id = rows[0]['debtor_reg_name_id']
    register_id = rows[0]['register_id']

    cursor.execute("select forename, middle_names, surname from party_name where id = %(id)s", {'id': name_id})
    rows = cursor.fetchall()
    forenames = [rows[0]['forename']]
    if rows[0]['middle_names'] != "":
        forenames += rows[0]['middle_names'].split(" ")
    data['debtor_name'] = {'forenames': forenames, 'surname': rows[0]['surname']}

    cursor.execute("select occupation, id from party where party_type='Debtor' and register_detl_id=%(id)s",
                   {'id': details_id})
    rows = cursor.fetchall()
    data['occupation'] = rows[0]['occupation']
    party_id = rows[0]['id']

    cursor.execute("select n.forename, n.middle_names, n.surname from party_name n, party_name_rel r " +
                   "where n.id = r.party_name_id and r.party_id = %(party_id)s and n.id != %(id)s ",
                   {'party_id': party_id, 'id': name_id})
    rows = cursor.fetchall()
    data['debtor_alias'] = []
    for row in rows:
        forenames = [row['forename']]
        if row['middle_names'] != "":
            forenames += row['middle_names'].split(" ")
        data['debtor_alias'].append({
            'forenames': forenames, 'surname': row['surname']
        })

    cursor.execute("select trading_name from party_trading where party_id = %(id)s", {'id': party_id})
    rows = cursor.fetchall()
    if len(rows) != 0:
        data['trading_name'] = rows[0]['trading_name']

    cursor.execute("select r.application_reference from request r, register_details d " +
                   "where r.id = d.request_id and d.id = %(id)s", {'id': details_id})
    rows = cursor.fetchall()
    data['application_ref'] = rows[0]['application_reference']

    cursor.execute("select d.line_1, d.line_2, d.line_3, d.line_4, d.line_5, d.line_6, a.address_string " +
                   "from address a " +
                   "left outer join address_detail d on a.detail_id = d.id " +
                   "inner join party_address pa on a.id = pa.address_id " +
                   "where a.address_type='Debtor Residence' and pa.party_id = %(id)s", {'id': party_id})

    rows = cursor.fetchall()
    data['residence'] = []
    for row in rows:
        if row['line_1'] is None:  # Unstructured address stored as text
            text = row['address_string']
            data['residence'].append({'text': text})

        else:
            address = []
            if row['line_1'] != "":
                address.append(row['line_1'])
            if row['line_2'] != "":
                address.append(row['line_2'])
            if row['line_3'] != "":
                address.append(row['line_3'])
            if row['line_4'] != "":
                address.append(row['line_4'])
            if row['line_5'] != "":
                address.append(row['line_5'])
            if row['line_6'] != "":
                address.append(row['line_6'])

            data['residence'].append({
                'address_lines': address
            })

    cursor.execute("SELECT original_regn_no, extra_data FROM migration_status WHERE register_id=%(id)s",
                   {'id': register_id})
    rows = cursor.fetchall()
    if len(rows) > 0:
        data['legacy'] = {
            'original_registration': rows[0]['original_regn_no'],
            'extra': rows[0]['extra_data']
        }

    return data


@app.route('/registration/<int:reg_no>', methods=['GET'])
def registration(reg_no):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    d = get_registration_details(cursor, reg_no)
    complete(cursor)
    if d is None:
        return Response(status=404)
    else:
        return Response(json.dumps(d), status=200, mimetype='application/json')


@app.route('/migrated_registration/<int:db2_reg_no>', methods=['GET'])
def migrated_registration(db2_reg_no):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    new_reg_no = get_new_registration_number(cursor, db2_reg_no)

    registrations = []
    for n in new_reg_no:
        registrations.append(get_registration_details(cursor, n))

    complete(cursor)

    if len(registrations) > 0:
        return Response(json.dumps(registrations), status=200, mimetype='application/json')
    else:
        return Response(status=404)



@app.route('/search', methods=['POST'])
def retrieve():
    if request.headers['Content-Type'] != "application/json":
        logger.error('Content-Type is not JSON')
        return Response(status=415)

    try:
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
        data = request.get_json(force=True)

        reg_ids = get_registration_from_name(cursor, data['forenames'], data['surname'])
        if len(reg_ids) == 0:
            return Response(status=404)

        regs = []
        for reg_id in reg_ids:
            regs.append(get_registration(cursor, reg_id))
        complete(cursor)
        data = json.dumps(regs, ensure_ascii=False)
        return Response(data, status=200, mimetype='application/json')
    except Exception as error:
        logger.error(error)
        return Response("Error: " + str(error), status=500)


@app.route('/register', methods=['POST'])
def register():
    if request.headers['Content-Type'] != "application/json":
        logger.error('Content-Type is not JSON')
        return Response(status=415)

    try:
        json_data = request.get_json(force=True)
        new_regns = insert_record(json_data)
        publish_new_bankruptcy(producer, new_regns)
        return Response(json.dumps({'new_registrations': new_regns}), status=200)
    except Exception as error:
        logger.error(error)
        return Response("Error: " + str(error), status=500)


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
        logger.error('Content-Type is not JSON')
        return Response(status=415)

    try:
        data = request.get_json(force=True)
        try:
            validate(data, migrated_schema)
        except ValidationError as error:
            message = "{}\n{}".format(error.message, error.path)
            return Response(message, status=400)

        app_type = re.sub(r"\(|\)", "", data["application_type"])
        cursor = connect()

        request_id = insert_request(cursor, None, app_type, data['application_ref'], data['date'], None)
        details_id = insert_register_details(cursor, request_id, data['date'], app_type)
        party_id = insert_party(cursor, details_id, "Debtor", None, None, False)
        name_id = insert_name(cursor, data['debtor_name'], party_id)

        for address in data['residence']:
            insert_address(cursor, address, "Debtor Residence", party_id)

        registration_no, registration_id = insert_registration(cursor, details_id, name_id)
        insert_migration_status(cursor, registration_id, data['migration_data']['registration_no'],
                                data['migration_data']['extra'])

        complete(cursor)
        return Response(json.dumps({'new_registrations': [registration_no]}), status=200)

    except Exception as error:
        logger.error(error)
        return Response("Error: " + str(error), status=500)

