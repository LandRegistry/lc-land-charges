from application import app, producer
from application.exchange import setup_messaging, publish_new_bankruptcy
from flask import Response, request
import psycopg2
import json
import re


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


def connect():
    connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
        app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
        app.config['DATABASE_PASSWORD']))
    return connection.cursor()


def complete(cursor):
    cursor.connection.commit()
    cursor.close()
    cursor.connection.close()


def insert_address(cursor, address, address_type, party_id):
    print(address)
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


def insert_record(data):
    cursor = connect()

    # ins_bankruptcy_request
    cursor.execute("INSERT INTO ins_bankruptcy_request (request_data) VALUES (%(json)s) RETURNING id",
                   {"json": json.dumps(data)})
    ins_request_id = cursor.fetchone()[0]

    app_type = re.sub(r"\(|\)", "", data["application_type"])

    # request
    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, " +
                   "ins_request_id) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(ins_id)s ) RETURNING id",
                   {
                       "key": data["key_number"], "app_type": app_type,
                       "app_ref": data["application_ref"], "app_date": data["date"], "ins_id": ins_request_id
                   })
    request_id = cursor.fetchone()[0]

    # register
    cursor.execute("INSERT INTO register (request_id, registration_no, registration_date, application_type, " +
                   "bankruptcy_date) " +
                   "VALUES ( %(req_id)s, %(reg_no)s, %(reg_date)s, %(app_type)s, %(bank_date)s ) " +
                   "RETURNING id",
                   {
                       "req_id": request_id, "reg_no": 7, "reg_date": data["date"],
                       "app_type": app_type, "bank_date": data["date"]
                   })   # TODO: dates being the same is wrong; reg_no probably shouldn't be 7...
                        # Seems probable we won't need both dates
    registration_id = cursor.fetchone()[0]

    # party
    cursor.execute("INSERT INTO party (register_id, party_type, occupation, date_of_birth, residence_withheld) " +
                   "VALUES( %(reg_id)s, %(type)s, %(occupation)s, %(dob)s, %(rw)s ) RETURNING id",
                   {
                       "reg_id": registration_id, "type": "Debtor", "occupation": data["occupation"],
                       "dob": data["date_of_birth"], "rw": data["residence_withheld"]
                   })
    party_id = cursor.fetchone()[0]

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
    insert_name(cursor, data['debtor_name'], party_id)
    for name in data['debtor_alternative_name']:
        insert_name(cursor, name, party_id, True)

    # party_trading
    if "trading_name" in data:
        cursor.execute("INSERT INTO party_trading (party_id, trading_name) " +
                       "VALUES ( %(party)s, %(trading)s ) RETURNING id",
                       { "party": party_id, "trading": data['trading_name'] })

    # TODO: audit-log not done. Not sure it belongs here?
    complete(cursor)


def get_registration_from_name(cursor, forenames, surname):
    fn_list = forenames.split(" ")
    forename = fn_list[0]
    middle_name = ""
    if len(forenames) > 1:
        middle_name = " ".join(fn_list[1:])

    cursor.execute("SELECT p.register_id " +
                   "FROM party_name n, party_name_rel pr, party p " +
                   "where n.alias_name=False and n.forename=%(forename)s and n.surname=%(surname)s " +
                   "and n.middle_names=%(midname)s and n.id = pr.party_name_id and pr.party_id = p.id",
                   {
                       'forename': forename, 'midname': middle_name, 'surname': surname
                   })

    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append(row[0])

    return result


def get_registration(cursor, reg_id):
    cursor.execute("select registration_date, application_type, registration_no, bankruptcy_date " +
                   "from register where id=%(id)s", {"id": reg_id})
    rows = cursor.fetchall()
    row = rows[0]
    result = {
        "registration_date": str(row[0]),
        "application_type": row[1],
        "registration_no": row[2],
        "bankruptcy_date": str(row[3])
    }
    return result


@app.route('/search', methods=['POST'])
def retrieve():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    cursor = connect()
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


@app.route('/register', methods=['POST'])
def register():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    json_data = request.get_json(force=True)
    insert_record(json_data)

    publish_new_bankruptcy(producer, json_data)
    return Response(status=200)




