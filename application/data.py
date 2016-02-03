from application import app
import psycopg2
import json
import datetime
import logging
import re
from application.search import get_searchable_string


def connect(cursor_factory=None):
    connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
        app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
        app.config['DATABASE_PASSWORD']))
    return connection.cursor(cursor_factory=cursor_factory)


def complete(cursor):
    cursor.connection.commit()
    cursor.close()
    cursor.connection.close()


def rollback(cursor):
    cursor.connection.rollback()
    cursor.close()
    cursor.connection.close()


def insert_address(cursor, address, address_type, party_id):
    if 'address_lines' in address:
        lines = address['address_lines'][0:5]   # First five lines
        remaining = ", ".join(address['address_lines'][5:])
        if remaining != '':
            lines.append(remaining)             # Remaining lines into 6th line

        while len(lines) < 6:
            lines.append("")                    # Pad to 6 lines for avoidance of horrible if statements later

        county = address['county']
        postcode = address['postcode']       # Postcode in the last
        cursor.execute("INSERT INTO address_detail ( line_1, line_2, line_3, line_4, line_5, line_6 ,county, postcode) " +
                       "VALUES( %(line1)s, %(line2)s, %(line3)s, %(line4)s, %(line5)s, %(line6)s, %(county)s, %(postcode)s ) " +
                       "RETURNING id",
                       {
                           "line1": lines[0], "line2": lines[1], "line3": lines[2],
                           "line4": lines[3], "line5": lines[4], "line6": lines[5],
                           "county": county, "postcode": postcode,
                       })
        detail_id = cursor.fetchone()[0]
        address_string = "{}, {}, {}".format(", ".join(address['address_lines']), address["county"], address["postcode"])
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
    if 'estate_owner_ind' in name:
        # name_string, forename, middle_names, surname, company = (None,) * 5
        # local_auth, local_auth_area, complex_name, other, searchable_string = (None,) * 5
        # complex_number = None
        if len(name['private']['forenames']) > 0 or name['private']['surname'] != '':
            forename = name['private']['forenames'][0]
            middle_names = " ".join(name['private']['forenames'][1:])
            surname = name['private']['surname']
            name_join = " ".join(name['private']['forenames']) + " " + name['private']['surname']
            # store the name without punctuation or spaces for searching
            # searchable_string = re.sub('[^A-Za-z0-9]+', '', name_string)
        else:
            forename = None
            middle_names = None
            surname = None
            name_join = ''

        name_string = name_join if name_join != '' else None
        company = name['company'] if name['company'] != '' else None
        local_auth = name['local']['name'] if name['local']['name'] != '' else None
        local_auth_area = name['local']['area'] if name['local']['area'] != '' else None
        other = name['other'] if name['other'] != '' else None
        complex_name = name['complex']['name'] if name['complex']['name'] != '' else None
        complex_number = name['complex']['number'] if name['complex']['number'] != '' else None

        if complex_name is None:
            searchable_string = get_searchable_string(name_string, company, local_auth, local_auth_area, other)
        else:
            searchable_string = None
        print(searchable_string)

        cursor.execute("INSERT INTO party_name ( party_name, forename, " +
                       "middle_names, surname, alias_name, complex_number, complex_name, " +
                       "name_type_ind, company_name, local_authority_name, local_authority_area, other_name, " +
                       "searchable_string ) " +
                       "VALUES ( %(name)s, %(forename)s, %(midnames)s, %(surname)s, %(alias)s, " +
                       "%(comp_num)s, %(comp_name)s, %(type)s, %(company)s, " +
                       "%(loc_auth)s, %(loc_auth_area)s, %(other)s, %(search_name)s ) " +
                       "RETURNING id",
                       {
                           "name": name_string, "forename": forename, "midnames": middle_names,
                           "surname": surname, "alias": is_alias, "comp_num":complex_number, "comp_name": complex_name,
                           "type": name['estate_owner_ind'], "company": company, "loc_auth": local_auth,
                           "loc_auth_area": local_auth_area, "other": other, "search_name": searchable_string
                       })
        name['id'] = cursor.fetchone()[0]
        return_data = {'id': name['id'],
                       'name': name}
    elif 'number' in name:
        cursor.execute("INSERT INTO party_name (alias_name, complex_number, complex_name) " +
                       "VALUES ( %(alias)s, %(number)s, %(name)s ) " +
                       "RETURNING id",
                       {
                           "alias": is_alias, "number": name['number'], "name": name['name']
                       })
        name['id'] = cursor.fetchone()[0]
        return_data = {
            'id': name['id'],
            'name': name['name'],
            'number': name['number']
        }
    else:
        name_string = "{} {}".format(" ".join(name['forenames']), name['surname'])
        searchable_string = re.sub('[^A-Za-z0-9]+', '', name_string).upper()
        forename = name['forenames'][0]
        middle_names = " ".join(name['forenames'][1:])
        cursor.execute("INSERT INTO party_name ( party_name, forename, " +
                       "middle_names, surname, alias_name, searchable_string ) " +
                       "VALUES ( %(name)s, %(forename)s, %(midnames)s, %(surname)s, %(alias)s, %(search)s ) " +
                       "RETURNING id",
                       {
                           "name": name_string, "forename": forename, "midnames": middle_names,
                           "surname": name['surname'], "alias": is_alias, "search": searchable_string
                       })
        name['id'] = cursor.fetchone()[0]
        return_data = {
            'id': name['id'],
            'forenames': name['forenames'],
            'surname': name['surname']
        }

    cursor.execute("INSERT INTO party_name_rel (party_name_id, party_id) " +
                   "VALUES( %(name)s, %(party)s ) RETURNING id",
                   {
                       "name": name['id'], "party": party_id
                   })

    return return_data


def insert_registration(cursor, details_id, name_id, date, county_id, orig_reg_no=None):
    if orig_reg_no is None:
        # Get the next registration number
        year = date[:4]  # date is a string
        cursor.execute('select MAX(registration_no) + 1 AS reg '
                       'from register  '
                       'where date >=%(start)s AND date < %(end)s',
                       {
                           'start': "{}-01-01".format(year),
                           'end': "{}-01-01".format(int(year) + 1)
                       })

        rows = cursor.fetchall()
        if rows[0]['reg'] is None:
            reg_no = 1000
        else:
            reg_no = int(rows[0]['reg'])
    else:
        reg_no = orig_reg_no

    # Cap it all off with the actual legal "one registration per name":
    cursor.execute("INSERT INTO register (registration_no, debtor_reg_name_id, details_id, date, county_id) " +
                   "VALUES( %(regno)s, %(debtor)s, %(details)s, %(date)s, %(county)s ) RETURNING id",
                   {
                       "regno": reg_no,
                       "debtor": name_id,
                       "details": details_id,
                       'date': date,
                       'county': county_id
                   })
    reg_id = cursor.fetchone()[0]
    return reg_no, reg_id


def insert_register_details(cursor, request_id, data, amends):
    if 'lc_register_details' in data:
        class_of_charge = data['lc_register_details']['class']
        bank_date = None
    else:
        class_of_charge = data['class_of_charge']
        bank_date = data['date']
    date = data['date']
    legal_body = data['legal_body'] if 'legal_body' in data else ""
    legal_body_ref = data['legal_body_ref'] if 'legal_body_ref' in data else ""
    district = data['lc_register_details']['district'] if 'lc_register_details' in data else ""
    short_description = data['lc_register_details']['short_description'] if 'lc_register_details' in data else ""
    additional_info = data['lc_register_details']['additional_info'] if 'lc_register_details' in data else ""

    cursor.execute("INSERT INTO register_details (request_id, registration_date, class_of_charge, " +
                   "bankruptcy_date, legal_body, legal_body_ref, amends, district, short_description, "
                   "additional_info) " +
                   "VALUES ( %(req_id)s, %(reg_date)s, %(charge)s, %(bank_date)s, " +
                   " %(lbody)s, %(lbodyref)s, %(amends)s, %(district)s, %(short_desc)s, " +
                   "%(addl_info)s )" +
                   "RETURNING id",
                   {
                       "req_id": request_id, "reg_date": date,
                       "charge": class_of_charge, "bank_date": bank_date,
                       "lbody": legal_body, "lbodyref": legal_body_ref,
                       "amends": amends, "district": district, "short_desc": short_description,
                       "addl_info": additional_info
                   })   # TODO: Seems probable we won't need both dates
    return cursor.fetchone()[0]


# pylint: disable=too-many-arguments
def insert_request(cursor, key_number, application_type, reference, date, document=None, insolvency_data=None,
                   customer_name=None, customer_address=None):
    if insolvency_data is not None:
        cursor.execute("INSERT INTO ins_bankruptcy_request (request_data) VALUES (%(json)s) RETURNING id",
                       {"json": json.dumps(insolvency_data)})
        ins_request_id = cursor.fetchone()[0]
    else:
        ins_request_id = None  # TODO: consider when ins data should be added...

    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, " +
                   "ins_request_id, document_ref, customer_name, customer_address) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(ins_id)s, %(doc)s, " +
                   "%(cust_name)s, %(cust_addr)s ) RETURNING id",
                   {
                       "key": key_number, "app_type": application_type, "app_ref": reference,
                       "app_date": date, "ins_id": ins_request_id, "doc": document, "cust_name": customer_name,
                       "cust_addr": customer_address
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


def insert_migration_status(cursor, register_id, registration_number, registration_date, class_of_charge, additional_data):
    cursor.execute("INSERT INTO migration_status (register_id, original_regn_no, date, class_of_charge, "
                   "migration_complete, extra_data ) "
                   "VALUES( %(register_id)s, %(reg_no)s, %(date)s, %(class)s, True, %(extra)s ) RETURNING id",
                   {
                       "register_id": register_id,
                       "reg_no": registration_number,
                       "date": registration_date,
                       "class": class_of_charge,
                       "extra": json.dumps(additional_data)
                   })
    return cursor.fetchone()[0]


def insert_details(cursor, request_id, data, amends_id):
    logging.debug("Insert details")
    # register details
    register_details_id = insert_register_details(cursor, request_id, data, amends_id)

    # party
    if 'lc_register_details' in data:
        party_type = 'Estate Owner'
        occupation = data['lc_register_details']['occupation']
    else:
        party_type = 'Debtor'
        occupation = data['occupation']

    party_id = insert_party(cursor, register_details_id, party_type, occupation, data['date_of_birth'],
                            data['residence_withheld'])

    # party_address, address, address_detail
    if 'residence' in data:
        for address in data['residence']:
            insert_address(cursor, address, "Debtor Residence", party_id)

    if "business_address" in data:
        for address in data["investment_property"]:
            insert_address(cursor, address, "Debtor Business", party_id)

    if "investment_property" in data:
        if not isinstance(data['investment_property'], list):
            data['investment_property'] = [data['investment_property']]

        for address in data["investment_property"]:
            insert_address(cursor, address, "Investment", party_id)

    # party_name, party_name_rel
    if 'lc_register_details' in data:
        # TODO: insert county here???
        data['county_ids'] = []
        for item in data['lc_register_details']['county']:
            county_detl_id, county_id = insert_lc_county(cursor, register_details_id, item)
            data['county_ids'].append({'id': county_id, 'name': item})  # for use later...

        names = [insert_name(cursor, data['lc_register_details']['estate_owner'], party_id)]
        names[0]['county_detl_id'] = county_detl_id

    elif 'complex' in data:
        names = [insert_name(cursor, data['complex'], party_id)]
    else:
        # if 'debtor_names' in data: # Handle array input
        names = [insert_name(cursor, data['debtor_names'][0], party_id)]
        for name in data['debtor_names'][1:]:
            names.append(insert_name(cursor, name, party_id, True))

        # else:  # TODO: retire this leg
        #     names = [insert_name(cursor, data['debtor_name'], party_id)]
        #     for name in data['debtor_alternative_name']:
        #         names.append(insert_name(cursor, name, party_id, True))

    # party_trading
    if "trading_name" in data:
        cursor.execute("INSERT INTO party_trading (party_id, trading_name) " +
                       "VALUES ( %(party)s, %(trading)s ) RETURNING id",
                       {"party": party_id, "trading": data['trading_name']})
    return names, register_details_id


def insert_bankruptcy_regn(cursor, details_id, names, date, orig_reg_no):
    reg_nos = []
    for name in names:
        reg_no, reg_id = insert_registration(cursor, details_id, name['id'], date, None, orig_reg_no)
        if 'forenames' in name:
            reg_nos.append({
                'number': reg_no,
                'date': date,
                'forenames': name['forenames'],
                'surname': name['surname']
            })
        else:
            reg_nos.append({
                'number': reg_no,
                'date': date,
                'name': name['name']
            })
    return reg_nos


def insert_landcharge_regn(cursor, details_id, names, county_ids, date, orig_reg_no):
    if len(names) != 1:
        raise RuntimeError("Invalid number of names")

    reg_nos = []
    for county in county_ids:
        logging.debug(county['id'])
        name = names[0]
        reg_no, reg_id = insert_registration(cursor, details_id, name['id'], date, county['id'], orig_reg_no)

        reg_nos.append({
            'number': reg_no,
            'date': date,
            'county': county['name'],
        })

    return reg_nos


def insert_record(cursor, data, request_id, amends=None, orig_reg_no=None):
    names, register_details_id = insert_details(cursor, request_id, data, amends)

    if data['class_of_charge'] in ['PA(B)', 'WO(B)']:
        reg_nos = insert_bankruptcy_regn(cursor, register_details_id, names, data['date'], orig_reg_no)
    else:
        reg_nos = insert_landcharge_regn(cursor, register_details_id, names, data['county_ids'], data['date'], orig_reg_no)

    # TODO: audit-log not done. Not sure it belongs here?
    return reg_nos, register_details_id


def insert_new_registration(cursor, data):
    document = None
    if 'document_id' in data:
        document = data['document_id']

    # request
    original = None
    if 'original_request' in data:
        original = data['original_request']
    request_id = insert_request(cursor, data['key_number'], data["class_of_charge"], data['application_ref'],
                                data['date'], document, original, data['customer_name'], data['customer_address'])

    reg_nos, details_id = insert_record(cursor, data, request_id)
    return reg_nos, details_id, request_id


def insert_amendment(cursor, orig_reg_no, date, data):
    # For now, always insert a new record
    original_detl_id = get_register_details_id(cursor, orig_reg_no, date)
    if original_detl_id is None:
        return None, None, None

    document = None
    if 'document_id' in data:
        document = data['document_id']

    now = datetime.datetime.now()
    request_id = insert_request(cursor, None, "AMENDMENT", None, now, document, None, data['customer_name'],
                                data['customer_address'])

    original_regs = get_all_registration_nos(cursor, original_detl_id)
    amend_detl_id = get_register_details_id(cursor, orig_reg_no, date)
    # pylint: disable=unused-variable
    reg_nos, details = insert_record(cursor, data, request_id, amend_detl_id)

    # Update old registration
    cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                   "id = %(id)s AND cancelled_by IS NULL",
                   {
                       "canc": request_id, "id": original_detl_id
                   })
    rows = cursor.rowcount
    return original_regs, reg_nos, rows


def insert_rectification(cursor, orig_reg_no, data):
    # For now, always insert a new record
    original_detl_id = get_register_details_id(cursor, orig_reg_no)
    if original_detl_id is None:
        return None, None, None

    document = None
    if 'document_id' in data:
        document = data['document_id']

    now = datetime.datetime.now()
    request_id = insert_request(cursor, None, "RECTIFICATION", None, now, document, None, data['customer_name'],
                                data['customer_address'])

    # pylint: disable=unused-variable
    original_regs = get_all_registration_nos(cursor, original_detl_id)
    amend_detl_id = get_register_details_id(cursor, orig_reg_no)
    reg_nos, details = insert_record(cursor, data, request_id, amend_detl_id, orig_reg_no)

    # Update old registration
    cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                   "id = %(id)s AND cancelled_by IS NULL",
                   {
                       "canc": request_id, "id": original_detl_id
                   })
    rows = cursor.rowcount
    return original_regs, reg_nos, rows


def get_register_details_id(cursor, reg_no, date):
    cursor.execute("SELECT details_id FROM register WHERE registration_no = %(regno)s AND date=%(date)s",
                   {
                       "regno": reg_no,
                       'date': date
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    elif len(rows) > 1:
        raise RuntimeError("Too many rows retrieved")
    else:
        return rows[0]['details_id']


def get_all_registration_nos(cursor, details_id):
    cursor.execute("SELECT registration_no, date FROM register WHERE details_id = %(details)s",
                   {"details": details_id})
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            'number': str(row['registration_no']),
            'date': str(row['date'])
        })
    return results


def get_registration(cursor, reg_id, date=None):
    if date is None:
        cursor.execute("select r.registration_no, r.debtor_reg_name_id, rd.registration_date, rd.class_of_charge, rd.id, " +
                       "r.id as register_id from register r, register_details rd " +
                       "where r.details_id = rd.id " +
                       "and r.id=%(id)s", {'id': reg_id})
    else:
        cursor.execute("select r.registration_no, r.debtor_reg_name_id, rd.registration_date, rd.class_of_charge, rd.id, " +
                       "r.id as register_id from register r, register_details rd " +
                       "where r.details_id = rd.id " +
                       "and r.id=%(id)s and r.date=%(date)s", {'id': reg_id, 'date': date})
    rows = cursor.fetchall()
    row = rows[0]
    result = {
        "registration_date": str(row['registration_date']),
        "class_of_charge": row['class_of_charge'],
        "registration_no": row['registration_no'],
    }
    return result


# def get_new_registration_number(cursor, db2_reg_no):
#     cursor.execute("select r.registration_no from register r, migration_status ms where r.id = ms.register_id"
#                    " and ms.original_regn_no = %(reg_no)s", {'reg_no': db2_reg_no})
#     rows = cursor.fetchall()
#     # row = rows[0]
#     reg_nos = []
#     for row in rows:
#         reg_nos.append(row['registration_no'])
#
#     return reg_nos

def get_party_names(cursor, party_id):
    cursor.execute("select forename, middle_names, surname, alias_name, complex_number, complex_name, "
                   "name_type_ind, company_name, local_authority_name, local_authority_area, other_name "
                   "from party_name pn, party_name_rel pnr where pnr.party_id=%(id)s and "
                   "pnr.party_name_id = pn.id order by alias_name desc", {"id": party_id})
    rows = cursor.fetchall()

    result = []
    for row in rows:
        name = {}
        pname = {}
        if row['forename'] != "":
            pname['forenames'] = [row['forename']]

        if row['middle_names']:
            if 'forenames' not in pname:
                pname['forenames'] = ['']
            pname['forenames'] += row['middle_names'].split(' ')

        if row['surname'] != "":
            pname['surname'] = row['surname']

        if 'forenames' in pname:
            name['private'] = pname

        if row['complex_number'] is not None or row['complex_name'] != "":
            name['complex'] = {'number': row['complex_number'], 'name': row['complex_name']}

        name['type'] = row['name_type_ind']

        if row['company_name'] != "":
            name['company'] = row['company_name']

        if row['local_authority_name'] != "" or row['local_authority_area'] != "":
            name['local'] = {
                'name': row['local_authority_name'],
                'area': row['local_authority_area']
            }

        if row['other_name'] != "":
            name['other'] = row['other_name']
        result.append(name)

    return result


def get_parties(cursor, data, details_id):
    cursor.execute("select p.party_type, p.occupation, p.date_of_birth, pt.trading_name, p.id, p.residence_withheld  "
                   "from party p left outer join party_trading pt on p.id = pt.party_id "
                   "where p.register_detl_id=%(id)s", {'id': details_id})
    rows = cursor.fetchall()

    party_ids = []
    for row in rows:
        party_id = row['id']
        party_ids.append(party_id)
        names = get_party_names(cursor, party_id)
        if row['party_type'] == 'Debtor':
            data['debtor_names'] = names
            data['trading'] = row['trading_name']
            data['occupation'] = row['occupation']
            data['residence_withheld'] = row['residence_withheld']
        elif row['party_type'] == 'Estate Owner':
            data['occupation'] = row['occupation']
            data['residence_withheld'] = row['residence_withheld']
            if len(names) > 1:
                logging.debug(names)
                raise RuntimeError("Too many estate owner names returned")
            elif len(names) == 0:
                raise RuntimeError("No names returned")

            name = names[0]
            data['estate_owner_ind'] = name['type']
            del(name['type'])
            data['estate_owner'] = name
        else:
            raise RuntimeError("Unknown party type: " + row['party_type'])
    return party_ids


def get_registration_no_from_details_id(cursor, details_id):
    cursor.execute("select r.registration_no, d.registration_date, d.amendment_type from register r, register_details d where " +
                   "  r.details_id = %(id)s AND r.details_id = d.id",
                   {'id': details_id})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return {
            'number': rows[0]['registration_no'],
            'date': str(rows[0]['registration_date']),
            'type': rows[0]['amendment_type']
        }


def get_all_registrations(cursor):
    cursor.execute('select r.registration_no, r.date, d.class_of_charge '
                   'from register r, register_details d '
                   'where d.id = r.details_id')
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    results = []
    for row in rows:
        results.append({
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'class': row['class_of_charge'],
            'uri': row['date'].strftime('%Y-%m-%d') + '/' + str(row['registration_no'])
        })
    return results

        
def get_registrations_by_date(cursor, date):
    cursor.execute('select id from request where application_date=%(date)s', {'date': date})
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            'application': '',
            'id': row['id'],
            'data': []
        })

    for result in results:
        cursor.execute('select r.registration_no, r.date, d.class_of_charge, d.amends, d.cancelled_by '
                       'from register r, register_details d '
                       'where r.details_id = d.id and d.request_id=%(id)s', {'id': result['id']})
        rows = cursor.fetchall()
        if rows[0]['amends'] is None:
            result['application'] = 'new'
        else:
            result['application'] = 'amend'
        # TODO: cancellations

        for row in rows:
            result['data'].append({
                'number': row['registration_no'],
                'date': row['date'].strftime('%Y-%m-%d')
            })

    return results

    # cursor.execute('select r.registration_no, r.date, d.class_of_charge '
    #                'from register r, register_details d '
    #                'where d.id = r.details_id '
    #                'and date=%(date)s', {'date': date})
    # rows = cursor.fetchall()
    # if len(rows) == 0:
    #     return None
    #
    # results = []
    # for row in rows:
    #     results.append({
    #         'number': row['registration_no'],
    #         'date': row['date'].strftime('%Y-%m-%d'),
    #         'class': row['class_of_charge']
    #     })
    # return results


def get_registration_details(cursor, reg_no, date):
    cursor.execute("select r.registration_no, r.debtor_reg_name_id, rd.registration_date, rd.class_of_charge, rd.id, " +
                   " r.id as register_id, rd.legal_body, rd.legal_body_ref, rd.cancelled_by, rd.amends, rd.request_id, " +
                   " rd.additional_info, rd.district, rd.short_description "
                   "from register r, register_details rd " +
                   "where r.registration_no = %(reg_no)s and r.details_id = rd.id " +
                   "and rd.registration_date = %(date)s", {
                       'reg_no': reg_no,
                       'date': date,
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    data = {
        'registration': {
            'number': rows[0]['registration_no'],
            'date': str(rows[0]['registration_date'])
        },
        'class_of_charge': rows[0]['class_of_charge'],
        'legal_body': rows[0]['legal_body'],
        'legal_body_ref': rows[0]['legal_body_ref'],
        'status': "current",
        'additional_info': rows[0]['additional_info'],
        'district': rows[0]['district'],
        'short_description': rows[0]['short_description']

    }
    details_id = rows[0]['id']
    name_id = rows[0]['debtor_reg_name_id']
    register_id = rows[0]['register_id']

    if rows[0]['amends'] is not None:
        data['amends_regn'] = get_registration_no_from_details_id(cursor, rows[0]['amends'])

    cancelled_by = rows[0]['cancelled_by']
    if cancelled_by is not None:
        cursor.execute("select amends, amendment_type from register_details where amends=%(id)s",
                       {"id": details_id})

        rows = cursor.fetchall()
        if len(rows) > 0:
            data['status'] = 'superseded'
        else:
            data['status'] = 'cancelled'
            data['cancellation_ref'] = cancelled_by
            cursor.execute('select application_date from request where id=%(id)s', {'id': data['cancellation_ref']})
            cancel_rows = cursor.fetchall()
            data['cancellation_date'] = cancel_rows[0]['application_date'].isoformat()

    cursor.execute('select r.registration_no, r.date, d.amendment_type, d.amends FROM register r, register_details d ' +
                   'WHERE r.details_id=d.id AND d.amends=%(id)s', {'id': details_id})
    rows = cursor.fetchall()
    if len(rows) > 0:
        data['amended_by'] = {
            'number': rows[0]['registration_no'],
            'date': str(rows[0]['date']),
            'type': rows[0]['amendment_type']
        }

    cursor.execute("select dcr.county_id, c.name  from detl_county_rel dcr, county c " +
                   "where dcr.details_id = %(id)s and dcr.county_id = c.id ", {'id': details_id})
    rows = cursor.fetchall()
    if len(rows) != 0:
        counties = []
        for row in rows:
            counties.append(row['name'])
        data['counties'] = counties

    party_ids = get_parties(cursor, data, details_id)

    cursor.execute("select r.key_number, r.application_reference, r.document_ref, r.customer_name, " +
                   "r.customer_address " +
                   " from request r, register_details d where r.id = d.request_id and d.id = %(id)s",
                   {'id': details_id})
    rows = cursor.fetchall()
    data['application_ref'] = rows[0]['application_reference']
    data['document_id'] = rows[0]['document_ref']
    data['key_number'] = rows[0]['key_number']
    data['customer_name'] = rows[0]['customer_name']
    data['customer_address'] = rows[0]['customer_address']

    if len(party_ids) > 1:
        raise RuntimeError("Unexpected multitude of party ids")

    party_id = party_ids[0]
    cursor.execute("select d.line_1, d.line_2, d.line_3, d.line_4, d.line_5, d.line_6, d.county, " +
                   "d.postcode, a.address_string, a.address_type " +
                   "from address a " +
                   "left outer join address_detail d on a.detail_id = d.id " +
                   "inner join party_address pa on a.id = pa.address_id " +
                   "where pa.party_id = %(id)s", {'id': party_id})

    rows = cursor.fetchall()
    data['residence'] = []
    data['investment_property'] = []
    data['business_address'] = []
    for row in rows:
        add_to = ''
        address_type = row['address_type']
        if address_type == 'Debtor Residence':
            add_to = 'residence'
        elif address_type == 'Debtor Business':
            add_to = 'business_address'
        elif address_type == 'Investment':
            add_to = 'investment_property'

        if row['line_1'] is None:  # Unstructured address stored as text
            text = row['address_string']
            data[add_to].append({'text': text})

        else:
            address = []
            for i in range(1, 7):
                line = row['line_{}'.format(i)]
                if line != "":
                    address.append(line)

            data[add_to].append({
                'address_lines': address, 'county': row['county'], 'postcode': row['postcode']
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


def insert_migrated_record(cursor, data):
    data["class_of_charge"] = re.sub(r"\(|\)", "", data["class_of_charge"])

    # TODO: using registration date as request date. Valid? Always?

    logging.debug(data)
    if data['type'] in ['CN']:

        data['customer_name'] = ''
        data['customer_address'] = ''
        insert_cancellation(data['migration_data']['original']['registration_no'],
                            data['migration_data']['original']['date'], data)
        registration_id = None
        details_id = None
        request_id = None
    else:
        request_id = insert_request(cursor, None, data["class_of_charge"], data['application_ref'],
                                    data['registration']['date'], None,
                                    None, None)

        details_id = insert_register_details(cursor, request_id, data, None)  # TODO get court
        party_id = insert_party(cursor, details_id, "Debtor", None, None, False)

        name_id = None
        if 'eo_name' in data:
            name_id = insert_name(cursor, data['eo_name'], party_id)
            name_id = name_id['id']
        # if 'complex' in data:
            # name_id = insert_name(cursor, data['complex'], party_id)
        # elif 'debtor_names' in data:
            # name_id = insert_name(cursor, data['debtor_names'][0], party_id)
        # else:
            # data['complex'] = {"number": 0, "name": ""}
            # name_id = insert_name(cursor, data['complex'], party_id)

        insert_address(cursor, data['residence'], "Debtor Residence", party_id)

        logging.debug(data['date'])
        county_id = None
        
        registration_no, registration_id = insert_registration(cursor, details_id, name_id, data['date'], county_id, data['reg_no'])

    
    insert_migration_status(cursor, registration_id, data['registration']['registration_no'], data['registration']['date'],
                            data['class_of_charge'], data['migration_data'])
    return details_id, request_id


def get_head_of_chain(cursor, reg_no, date):
    # reg_no/date could be anywhere in the 'chain', though typically would be the start
    # as cancelled_by is a request_id, navigate by request_ids until we find the uncancelled
    # head entry
    cursor.execute('SELECT d.request_id, d.id FROM register r, register_details d '
                   'WHERE registration_no=%(reg)s AND date=%(date)s AND r.details_id = d.id ',
                   {"reg": reg_no, "date": date})
    row = cursor.fetchone()
    request_id = row['request_id']

    while True:
        cursor.execute('SELECT cancelled_by, id FROM register_details WHERE request_id=%(id)s', {"id": request_id})
        row = cursor.fetchone()
        next_id = row['cancelled_by']
        details_id = row['id']

        if next_id is None:
            return details_id
        request_id = next_id


def insert_cancellation(registration_no, date, data):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Insert a row with application info
        logging.info("Cancelling {} {}".format(registration_no, date))

        now = datetime.datetime.now()
        document = None
        if 'document_id' in data:
            logging.warning("Obsolete: cancellation with document-id")  # TODO: remove this and what needs it
            document = data['document_id']

        request_id = insert_request(cursor, None, "CANCELLATION", None, now, document, None, data['customer_name'],
                                    data['customer_address'])
        logging.info(request_id)
        # Set cancelled_on to now
        original_detl_id = get_head_of_chain(cursor, registration_no, date)
            #get_register_details_id(cursor, registration_no, date)
        logging.debug("Retrieved details id {}".format(original_detl_id))
        logging.info(original_detl_id)

        original_regs = get_all_registration_nos(cursor, original_detl_id)
        logging.info('--->')
        logging.info(original_regs)

        logging.info("SELECT * FROM register_details where id='" + str(original_detl_id) + "' AND cancelled_by IS NULL")
        cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                       "id = %(id)s AND cancelled_by IS NULL",
                       {
                           "canc": request_id, "id": original_detl_id
                       })

        # TODO: archive document
        rows = cursor.rowcount
        complete(cursor)
    except:
        rollback(cursor)
        raise

    return rows, original_regs


def insert_lc_county(cursor, register_details_id, county):
    county_id = get_county_id(cursor, county)
    cursor.execute("INSERT INTO detl_county_rel (county_id, details_id) " +
                   "VALUES( %(county_id)s, %(details_id)s ) RETURNING id",
                   {
                       "county_id": county_id, "details_id": register_details_id
                   })
    return cursor.fetchone()[0], county_id


def get_county_id(cursor, county):
    cursor.execute("SELECT id FROM county WHERE UPPER(name) = %(county)s",
                   {
                       "county": county.upper()
                   })
    rows = cursor.fetchone()[0]
    return rows

def get_register_request_details(request_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        sql = "Select request_id, registration_date, registration_no "\
              " from register_details a, register b "\
              " where a.request_id = %(request_id)s and a.id = b.details_id "
        cursor.execute(sql, {"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    registrations = []
    for row in rows:
        registration = {"request_id": row["request_id"], "registration_date": row["registration_date"], "registration_no": row["registration_no"]}
        registrations.append(registration)
    return registrations


def get_search_request_details(request_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    print("get  search request details")
    try:
        sql = " Select a.id as request_id, b.id as search_details_id, b.search_timestamp, b.type, b.counties, "\
              " a.key_number, a.application_type, a.application_reference, a.application_date, a.customer_name, "\
              " a.customer_address, b.certificate_date, b.expiry_date "\
              " from request a, search_details b "\
              " where a.id = %(request_id)s and a.id = b.request_id "
        cursor.execute(sql, {"request_id": request_id})
        rows = cursor.fetchall()
        print('sql 1')
    finally:
        complete(cursor)
    request = {}
    print('rows ' + str(len(rows)))
    for row in rows:
        request = {'request_id': row['request_id'], 'key_number': row['key_number'],
                   'certificate_date': str(row['certificate_date']), 'expiry_date': str(row['expiry_date']),
                   'customer_name': row['customer_name'], 'customer_address': row['customer_address'],
                   'application_reference': row['application_reference'],
                   'application_date': str(row['application_date']),
                   'search_details_id': row['search_details_id'],
                   'search_timestamp': str(row['search_timestamp']), 'type': row['type'],
                   'counties': row['counties'], 'search_details':[]}
        print(str(request))
        if request['search_details_id'] == None:
            request ={'noresult':'nosearchdetlid'}
        else:
            search_details = get_search_details(request["search_details_id"])
            request['search_details'] = search_details
    return request


def get_search_details(search_details_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    sql = ' select a.id as search_name_id, a.name_type, a.forenames, a.surname, a.complex_name, a.complex_number, '\
          ' a.company_name, a.local_authority_name, a.local_authority_area, a.other_name, a.year_from, a.year_to, '\
          ' b.result '\
          ' from search_name a, search_results b '\
          ' where a.details_id = %(search_details_id)s and  a.id = b.name_id '
    cursor.execute(sql, {"search_details_id": search_details_id})
    rows = cursor.fetchall()
    complete(cursor)
    sn_data = []
    for row in rows: # for each name searched against
        name_data = {'id':row['search_name_id'],
                     'name':{'name_type':row['name_type'],
                             'forenames':row['forenames'], 'surname':row['surname'], 'complex_name':row['complex_name'],
                             'complex_number':row['complex_number'], 'company_name':row['company_name'],
                             'local_authority_name':row['local_authority_name'],
                             'local_authority_area':row['local_authority_area'],'other_name':row['other_name']},
                     'year_from':row['year_from'],'year_to':row['year_to'], 'results':[]}
        results = []
        # sn_data['search_names']['results'] = results
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
        print("res_id ", str(row['result']))
        for res_id in row['result']:
            #get regsiter details from id and add to searchresults array in search name block
            #regs= get_all_registration_nos(cursor, res_id)
            #print("regs ", regs)
            #for reg_no in regs: #TO what if multiple register bought back????
            #    results_data = get_registration_details(cursor, reg['number'], reg['date'])
            #    results.append(results_data)

            results.append(get_registration_details_from_register_id(res_id))
        name_data['results'] = results
        sn_data.append(name_data)
        #sn_data = {'search_names:':name_data}
        complete(cursor)
    return sn_data

def get_registration_details_from_register_id(register_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    sql = 'select registration_no, date from register where id = %(register_id)s '
    cursor.execute(sql, {"register_id": register_id})
    rows = cursor.fetchall()
    complete(cursor)
    results = []
    for row in rows:
        results.append({
            'number': str(row['registration_no']),
            'date': str(row['date'])
        })
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    data = []
    for res in results:
        res_data = get_registration_details(cursor, res['number'], res['date'])
        data.append(res_data)
    complete(cursor)
    return data
