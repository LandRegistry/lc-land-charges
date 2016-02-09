from application import app
import psycopg2
import json
import datetime
import logging
import re
from application.search import get_searchable_string
from application.data_diff import get_rectification_type


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


def insert_address(cursor, address, party_id):
    if 'address_lines' in address and len(address['address_lines']) > 0:
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
    elif 'address_string' in address:
        address_string = address['address_string']
        detail_id = None
    else:
        raise Exception('Invalid address object')

    cursor.execute("INSERT INTO address (address_type, address_string, detail_id) " +
                   "VALUES( %(type)s, %(string)s, %(detail)s ) " +
                   "RETURNING id",
                   {
                       "type": address['type'],
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


def insert_party_name(cursor, party_id, name):
    name_string = None
    forename = None
    middle_names = None
    surname = None
    is_alias = False
    complex_number = None
    complex_name = None
    company = None
    local_auth = None
    local_auth_area = None
    other = None

    if name['type'] == 'Private Individual':
        forename = name['private']['forenames'][0]
        middle_names = ' '.join(name['private']['forenames'][1:])
        surname = name['private']['surname']
        name_string = " ".join(name['private']['forenames']) + " " + name['private']['surname']
    elif name['type'] in ['County Council', 'Rural Council', 'Parish Council', 'Other Council']:
        local_auth = name['local']['name']
        local_auth_area = name['local']['area']
    elif name['type'] in ['Development Corporation', 'Other']:
        other = name['other']
    elif name['type'] == 'Limited Company':
        company = name['company']
    elif name['type'] == 'Complex Name':
        complex_number = name['complex']['number']
        complex_name = name['complex']['name']
        searchable_string = None
    else:
        raise RuntimeError('Unknown name type: {}'.format(name['type']))

    if name['type'] != 'Complex Name':
        searchable_string = get_searchable_string(name_string, company, local_auth, local_auth_area, other)

    #get_searchable_string(name_string=None, company=None, local_auth=None, local_auth_area=None, other=None):
    cursor.execute("INSERT INTO party_name ( party_name, forename, middle_names, surname, alias_name, "
                   "complex_number, complex_name, name_type_ind, company_name, local_authority_name, "
                   "local_authority_area, other_name, searchable_string ) "
                   "VALUES ( %(name)s, %(forename)s, %(midnames)s, %(surname)s, %(alias)s, "
                   "%(comp_num)s, %(comp_name)s, %(type)s, %(company)s, "
                   "%(loc_auth)s, %(loc_auth_area)s, %(other)s, %(search_name)s ) "
                   "RETURNING id", {
                       "name": name_string, "forename": forename, "midnames": middle_names,
                       "surname": surname, "alias": is_alias, "comp_num": complex_number, "comp_name": complex_name,
                       "type": name['type'], "company": company, "loc_auth": local_auth,
                       "loc_auth_area": local_auth_area, "other": other, "search_name": searchable_string,
                   })

    name_id = cursor.fetchone()[0]
    return_data = {
        'id': name_id,
        'name': name
    }

    cursor.execute("INSERT INTO party_name_rel (party_name_id, party_id) " +
                   "VALUES( %(name)s, %(party)s ) RETURNING id",
                   {
                       "name": name_id, "party": party_id
                   })

    return return_data


def insert_registration(cursor, details_id, name_id, date, county_id, orig_reg_no=None):
    logging.debug('Insert registration')
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
    cursor.execute("INSERT INTO register (registration_no, debtor_reg_name_id, details_id, date, county_id, reveal) " +
                   "VALUES( %(regno)s, %(debtor)s, %(details)s, %(date)s, %(county)s, %(rev)s ) RETURNING id",
                   {
                       "regno": reg_no,
                       "debtor": name_id,
                       "details": details_id,
                       'date': date,
                       'county': county_id,
                       'rev': True
                   })
    reg_id = cursor.fetchone()[0]
    return reg_no, reg_id


def mark_as_no_reveal(cursor, reg_no, date):
    cursor.execute("UPDATE register SET reveal=%(rev)s WHERE registration_no=%(regno)s AND date=%(date)s", {
        "rev": False, "regno": reg_no, "date": date
    })


def insert_register_details(cursor, request_id, data, date, amends):
    additional_info = data['additional_information'] if 'additional_information' in data else None
    logging.debug(data)
    priority_notice = None
    if 'particulars' in data:
        district = data['particulars']['district']
        short_description = data['particulars']['description']
        if 'priority_notice' in data['particulars']:
            priority_notice = data['particulars']['priority_notice']
    else:
        district = None
        short_description = None

    debtor = None
    for party in data['parties']:
        if party['type'] == 'Debtor':
            debtor = party

    if debtor is not None:
        legal_ref = debtor['case_reference']
    else:
        legal_ref = None

    amend_type = None
    if 'update_registration' in data:
        amend_type = data['update_registration']['type']

    cursor.execute("INSERT INTO register_details (request_id, class_of_charge, legal_body_ref, "
                   "amends, district, short_description, additional_info, amendment_type, priority_notice_no  ) "
                   "VALUES (%(rid)s, %(coc)s, %(legal_ref)s, %(amends)s, %(dist)s, %(sdesc)s, %(addl)s, %(atype)s, %(pno)s) "
                   "RETURNING id", {
                       "rid": request_id, "coc": data['class_of_charge'],
                       "legal_ref": legal_ref, "amends": amends, "dist": district,
                       "sdesc": short_description, "addl": additional_info, "atype": amend_type,
                       "pno": priority_notice
                   })
    return cursor.fetchone()[0]


# pylint: disable=too-many-arguments
def insert_request(cursor, applicant, application_type, date, original_data=None):
    if original_data is not None:
        cursor.execute("INSERT INTO ins_bankruptcy_request (request_data) VALUES (%(json)s) RETURNING id",
                       {"json": json.dumps(original_data)})
        ins_request_id = cursor.fetchone()[0]
    else:
        ins_request_id = None  # TODO: consider when ins data should be added...

    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, " +
                   "ins_request_id, customer_name, customer_address) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(ins_id)s, " +
                   "%(cust_name)s, %(cust_addr)s ) RETURNING id",
                   {
                       "key": applicant['key_number'], "app_type": application_type, "app_ref": applicant['reference'],
                       "app_date": date, "ins_id": ins_request_id, "cust_name": applicant['name'],
                       "cust_addr": applicant['address']
                   })
    return cursor.fetchone()[0]


def insert_party(cursor, details_id, party):
    occupation = None
    date_of_birth = None
    residence_withheld = False
    if party['type'] == 'Debtor':
        occupation = party['occupation']
        if 'date_of_birth' in party:
            date_of_birth = party['date_of_birth']
        else:
            date_of_birth = None
        residence_withheld = party['residence_withheld']

    cursor.execute("INSERT INTO party (register_detl_id, party_type, occupation, date_of_birth, residence_withheld) " +
                   "VALUES( %(reg_id)s, %(type)s, %(occupation)s, %(dob)s, %(rw)s ) RETURNING id",
                   {
                       "reg_id": details_id, "type": party['type'], "occupation": occupation,
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


def insert_details(cursor, request_id, data, date, amends_id):
    logging.debug("Insert details")
    # register details
    register_details_id = insert_register_details(cursor, request_id, data, date, amends_id)

    debtor_id = None
    debtor = None
    names = []
    for party in data['parties']:
        party_id = insert_party(cursor, register_details_id, party)

        if party['type'] == 'Debtor':
            debtor_id = party_id
            debtor = party
            for address in party['addresses']:
                insert_address(cursor, address, party_id)

        for name in party['names']:
            name_info = insert_party_name(cursor, party_id, name)
            if party['type'] == 'Debtor':
                names.append(name_info)

    # party_trading
    if debtor_id is not None:
        trading_name = debtor['trading_name']
        cursor.execute("INSERT INTO party_trading (party_id, trading_name) " +
                       "VALUES ( %(party)s, %(trading)s ) RETURNING id",
                       {"party": debtor_id, "trading": trading_name})
    return names, register_details_id


def insert_bankruptcy_regn(cursor, details_id, names, date, orig_reg_no):
    logging.debug('Inserting banks reg')
    reg_nos = []
    if len(names) == 0: # Migration case only...
        reg_no, reg_id = insert_registration(cursor, details_id, None, date, None, orig_reg_no)
        reg_nos.append({
            'number': reg_no,
            'date': date,
            'name': None
        })
    
    else:    
        logging.debug(names)
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
    logging.debug('Inserting LC reg')
    if len(names) > 1:
        raise RuntimeError("Invalid number of names: {}".format(len(names)))
        
    reg_nos = []
    if len(county_ids) == 0: # can occur on migration only        
        if len(names) > 0:
            name = names[0]['id']
        else:
            name = None
                
        reg_no, reg_id = insert_registration(cursor, details_id, name, date, None, orig_reg_no)
        reg_nos.append({
            'number': reg_no,
            'date': date,
            'county': None,
        })
                
                
    else:
        for county in county_ids:
            logging.debug(county['id'])
            if len(names) > 0:
                name = names[0]['id']
            else:
                name = None
                
            reg_no, reg_id = insert_registration(cursor, details_id, name, date, county['id'], orig_reg_no)

            reg_nos.append({
                'number': reg_no,
                'date': date,
                'county': county['name'],
            })

    return reg_nos


def insert_counties(cursor, details_id, counties):
    ids = []
    for county in counties:
        county_detl_id, county_id = insert_lc_county(cursor, details_id, county)
        ids.append({'id': county_id, 'name': county})
    return ids

    
def insert_record(cursor, data, request_id, date, amends=None, orig_reg_no=None):

    names, register_details_id = insert_details(cursor, request_id, data, date, amends)

    if data['class_of_charge'] in ['PAB', 'WOB']:
        reg_nos = insert_bankruptcy_regn(cursor, register_details_id, names, date, orig_reg_no)
    else:
        county_ids = insert_counties(cursor, register_details_id, data['particulars']['counties'])
        reg_nos = insert_landcharge_regn(cursor, register_details_id, names, county_ids, date, orig_reg_no)

    # TODO: audit-log not done. Not sure it belongs here?
    return reg_nos, register_details_id


def insert_new_registration(cursor, data):
    # document = None
    # if 'document_id' in data:
    #     document = data['document_id']

    date = datetime.datetime.now().strftime('%Y-%m-%d')

    # request
    original = None
    if 'original_request' in data:
        original = data['original_request']

    request_id = insert_request(cursor, data['applicant'], 'New registration', date, original)
    # request_id = insert_request(cursor, data['key_number'], data["class_of_charge"], data['application_ref'],
    #                             data['date'], document, original, data['customer_name'], data['customer_address'])

    if 'dev_registration' in data:
        date = data['dev_registration']['date']

    reg_nos, details_id = insert_record(cursor, data, request_id, date, None, None)
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


def update_previous_details(cursor, request_id, original_detl_id):
    cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                   "id = %(id)s AND cancelled_by IS NULL",
                   {
                       "canc": request_id, "id": original_detl_id
                   })


def insert_rectification(cursor, rect_reg_no, rect_reg_date, data):
    original_details = get_registration_details(cursor,
                                                rect_reg_no,
                                                rect_reg_date)
    logging.debug(original_details)

    original_details_id = get_register_details_id(cursor,
                                                  rect_reg_no,
                                                  rect_reg_date)
    original_regs = get_all_registration_nos(cursor, original_details_id)

    logging.info(original_details_id)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    request_id = insert_request(cursor, data['applicant'], 'Rectification', date)

    # insert_record(cursor, data, request_id, date, amends=None, orig_reg_no=None):
    reg_nos, details_id = insert_record(cursor, data, request_id, date, original_details_id)
    update_previous_details(cursor, request_id, original_details_id)

    rect_type = get_rectification_type(original_details, data)
    logging.debug('Type of rectification is: %d', rect_type)
    if rect_type != 2:  # Legacy/business jargon - three types of rectification. Type 2 behaves differently
        # Mark the original as not reveal
        for reg in original_regs:
            mark_as_no_reveal(cursor, reg['number'], reg['date'])

    return original_regs, reg_nos

    # For now, always insert a new record
    # original_detl_id = get_register_details_id(cursor, orig_reg_no)
    # if original_detl_id is None:
    #     return None, None, None
    #
    # document = None
    # if 'document_id' in data:
    #     document = data['document_id']
    #
    # now = datetime.datetime.now()
    # request_id = insert_request(cursor, None, "RECTIFICATION", None, now, document, None, data['customer_name'],
    #                             data['customer_address'])
    #
    # # pylint: disable=unused-variable
    # original_regs = get_all_registration_nos(cursor, original_detl_id)
    # amend_detl_id = get_register_details_id(cursor, orig_reg_no)
    # reg_nos, details = insert_record(cursor, data, request_id, amend_detl_id, orig_reg_no)
    #
    # # Update old registration
    # cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
    #                "id = %(id)s AND cancelled_by IS NULL",
    #                {
    #                    "canc": request_id, "id": original_detl_id
    #                })
    # rows = cursor.rowcount
    # return original_regs, reg_nos, rows


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
        cursor.execute("select r.registration_no, r.debtor_reg_name_id, r.date, rd.class_of_charge, rd.id, " +
                       "r.id as register_id from register r, register_details rd " +
                       "where r.details_id = rd.id " +
                       "and r.id=%(id)s", {'id': reg_id})
    else:
        cursor.execute("select r.registration_no, r.debtor_reg_name_id, r.date, rd.class_of_charge, rd.id, " +
                       "r.id as register_id from register r, register_details rd " +
                       "where r.details_id = rd.id " +
                       "and r.id=%(id)s and r.date=%(date)s", {'id': reg_id, 'date': date})
    rows = cursor.fetchall()
    row = rows[0]
    result = {
        "registration_date": str(row['date']),
        "class_of_charge": row['class_of_charge'],
        "registration_no": row['registration_no'],
    }
    return result


def get_registration_no_from_details_id(cursor, details_id):
    cursor.execute("select r.registration_no, r.date, d.amendment_type from register r, register_details d where " +
                   "  r.details_id = %(id)s AND r.details_id = d.id",
                   {'id': details_id})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return {
            'number': rows[0]['registration_no'],
            'date': rows[0]['date'].strftime('%Y-%m-%d')
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


def read_names(cursor, party, party_id, lead_debtor_id):
    cursor.execute('select n.id, forename, middle_names, surname, complex_number, complex_name, '
                   'name_type_ind, company_name, local_authority_name, local_authority_area, '
                   'other_name '
                   'from party_name n, party_name_rel pn '
                   'where n.id = pn.party_name_id and pn.party_id = %(id)s', {
                       'id': party_id
                   })
    rows = cursor.fetchall()

    names_list = []
    for row in rows:
        name_id = row['id']

        name_type = row['name_type_ind']
        name = {
            'type': name_type
        }
        print('name type', name_type)
        if name_type == 'Private Individual':
            fornames = [row['forename']]
            middle = row['middle_names']
            if middle is not None and middle != "":
                fornames += middle.split(' ')

            name['private'] = {
                'forenames': fornames,
                'surname': row['surname']
            }
        elif name_type == 'Rural Council' or name_type == 'Parish Council' or \
                        name_type == 'County Council' or name_type == 'Other Council':
            name['local'] = {
                'name': row['local_authority_name'],
                'area': row['local_authority_area']
            }
        elif name_type == 'Development Corporation' or name_type == 'Other':
            name['other'] = row['other_name']
        elif name_type == 'Limited Company':
            name['company'] = row['company_name']
        elif name_type == 'Complex Name':
            name['complex'] = {
                'name': row['complex_name'],
                'number': row['complex_number']
            }
        else:
            raise RuntimeError("Unknown name type: {}".format(name_type))

        if name_id == lead_debtor_id:
            names_list.insert(0, name)
        else:
            names_list.append(name)

    party['names'] = names_list


def get_address_detail(cursor, address, detail_id):
    cursor.execute('SELECT line_1, line_2, line_3, line_4, line_5, line_6, country_id, county, postcode '
                   'FROM address_detail '
                   'WHERE id=%(id)s', {
                       'id': detail_id
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return
    if len(rows) > 1:
        raise RuntimeError("Unexpected multitude of address details")

    row = rows[0]
    address['address_lines'] = []
    if row['line_1'] is not None and row['line_1'] != '':
        address['address_lines'].append(row['line_1'])
    if row['line_2'] is not None and row['line_2'] != '':
        address['address_lines'].append(row['line_2'])
    if row['line_3'] is not None and row['line_3'] != '':
        address['address_lines'].append(row['line_3'])
    if row['line_4'] is not None and row['line_4'] != '':
        address['address_lines'].append(row['line_4'])
    if row['line_5'] is not None and row['line_5'] != '':
        address['address_lines'].append(row['line_5'])
    if row['line_6'] is not None and row['line_6'] != '':
        address['address_lines'].append(row['line_6'])

    address['county'] = row['county']
    address['postcode'] = row['postcode']


def read_addresses(cursor, party, party_id):
    cursor.execute('SELECT address_type, address_string, detail_id '
                   'FROM party_address pa, address a '
                   'WHERE pa.party_id = %(pid)s AND pa.address_id = a.id', {
                       'pid': party_id
                   })
    rows = cursor.fetchall()
    party['addresses'] = []
    for row in rows:
        address = {
            'type': row['address_type'],
            'address_string': row['address_string']
        }
        get_address_detail(cursor, address, row['detail_id'])
        party['addresses'].append(address)


def read_parties(cursor, data, details_id, legal_ref, lead_debtor_id):
    cursor.execute('SELECT id, party_type, occupation, date_of_birth, residence_withheld '
                   'FROM party '
                   'WHERE register_detl_id = %(id)s', {
                       'id': details_id
                   })
    rows = cursor.fetchall()
    data['parties'] = []
    for row in rows:
        party = {
            'type': row['party_type']
        }

        if party['type'] == 'Debtor':
            party['occupation'] = row['occupation']
            if row['date_of_birth'] is not None:
                party['date_of_birth'] = row['date_of_birth'].strftime('%Y-%m-%d')
            else:
                party['date_of_birth'] = None
            party['residence_withheld'] = row['residence_withheld']
            party['case_reference'] = legal_ref
            read_addresses(cursor, party, row['id'])
            # TODO: case_reference

        data['parties'].append(party)
        read_names(cursor, party, row['id'], lead_debtor_id)


def get_lc_counties(cursor, details_id, lead_county_id):
    cursor.execute("SELECT name FROM county WHERE id=%(id)s", {'id': lead_county_id})
    row = cursor.fetchone()
    
    if row is None:  # This is a migrated record with no recorded county
        counties = []
    else:
        counties = [row['name']]
        logging.info(counties)

        cursor.execute("select dcr.county_id, c.name  from detl_county_rel dcr, county c " +
                       "where dcr.details_id = %(id)s and dcr.county_id = c.id ", {'id': details_id})
        rows = cursor.fetchall()

        if len(rows) != 0:
            for row in rows:
                cty = row['name']
                if cty not in counties:
                    counties.append(cty)
        logging.info(counties)
    return counties


def get_registration_details(cursor, reg_no, date):
    cursor.execute("SELECT r.registration_no, r.date, r.reveal, rd.class_of_charge, rd.id, r.id as register_id, "
                   "rd.legal_body_ref, rd.cancelled_by, rd.amends, rd.request_id, rd.additional_info, "
                   "rd.district, rd.short_description, r.county_id, r.debtor_reg_name_id, rd.amendment_type "
                   "from register r, register_details rd "
                   "where r.registration_no=%(reg_no)s and r.date=%(date)s and r.details_id = rd.id", {
                       'reg_no': reg_no, 'date': date
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    details_id = rows[0]['id']
    lead_county = rows[0]['county_id']
    lead_debtor_id = rows[0]['debtor_reg_name_id']
    data = {
        'registration': {
            'number': rows[0]['registration_no'],
            'date': rows[0]['date'].strftime('%Y-%m-%d')
        },
        'class_of_charge': rows[0]['class_of_charge'],
        'status': 'current',
        'revealed': rows[0]['reveal']
    }

    if data['class_of_charge'] not in ['PAB', 'WOB']:
        data['particulars'] = {
            'counties': get_lc_counties(cursor, details_id, lead_county),
            'district': rows[0]['district'],
            'description': rows[0]['short_description']
        }

    register_id = rows[0]['register_id']
    legal_ref = rows[0]['legal_body_ref']
    if rows[0]['amends'] is not None:
        data['amends_registration'] = get_registration_no_from_details_id(cursor, rows[0]['amends'])
        data['amends_registration']['type'] = rows[0]['amendment_type']

    if rows[0]['cancelled_by'] is not None:
        cursor.execute("select amends, amendment_type from register_details where amends=%(id)s",
                       {"id": details_id})
        amd_rows = cursor.fetchall()
        if len(amd_rows) > 0:
            data['status'] = 'superseded'
        else:
            data['status'] = 'cancelled'
            data['cancellation'] = {'reference': rows[0]['cancelled_by']}
            # TODO: this is bugged
            # cursor.execute('select application_date from request where id=%(id)s', {'id': data['cancellation_ref']})
            # cancel_rows = cursor.fetchall()
            # data['cancellation']['date'] = cancel_rows[0]['application_date'].isoformat()

    cursor.execute('select r.registration_no, r.date, d.amendment_type, d.amends FROM register r, register_details d ' +
                   'WHERE r.details_id=d.id AND d.amends=%(id)s', {'id': details_id})
    rows = cursor.fetchall()
    if len(rows) > 0:
        data['amended_by'] = {
            'number': rows[0]['registration_no'],
            'date': rows[0]['date'].strftime('%Y-%m-%d'),
            'type': rows[0]['amendment_type']
        }

    read_parties(cursor, data, details_id, legal_ref, lead_debtor_id)

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
        types = {
            'NR': 'New registration',
            'AM': 'Amendment',
            'CP': 'Part cancellation',
            'CN': 'Cancellation',
            'RN': 'Renewal',
            'PN': 'Priority notice',
            'RC': 'Rectification'
        }
        type_str = types[data['type']]
    
        #def insert_request(cursor, applicant, application_type, date, original_data=None):
        request_id = insert_request(cursor, data['applicant'], type_str, data['registration']['date'], None)                                   
                                    
        reg_nos, details_id = insert_record(cursor, data, request_id, data['registration']['date'], None, data['registration']['registration_no'])
        
        if len(data['parties']) == 0:
            # There was no row on the original index, so by definition is cannot be revealed
            mark_as_no_reveal(cursor, data['registration']['registration_no'], data['registration']['date'])
            
    return details_id, request_id
        # details_id = insert_register_details(cursor, request_id, data, None)  # TODO get court
        # party_id = insert_party(cursor, details_id, "Debtor", None, None, False)

        # name_id = None
        # if 'eo_name' in data:
            # name_id = insert_name(cursor, data['eo_name'], party_id)
            # name_id = name_id['id']


        # insert_address(cursor, data['residence'], "Debtor Residence", party_id)

        # logging.debug(data['date'])
        # county_id = None
        
        # registration_no, registration_id = insert_registration(cursor, details_id, name_id, data['date'], county_id, data['reg_no'])

    
    # insert_migration_status(cursor, registration_id, data['registration']['registration_no'], data['registration']['date'],
                            # data['class_of_charge'], data['migration_data'])
    # return details_id, request_id


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
        sql = "Select a.request_id, b.date as registration_date, b.registration_no "\
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
