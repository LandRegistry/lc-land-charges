from application import app
import psycopg2
import json
import datetime
import logging
import re
from application.data_diff import get_rectification_type, eo_name_string, names_match, all_names_match, party_a_is_subset_of_b
from application.search_key import create_registration_key
from application.logformat import format_message
#from application.additional_info import get_additional_info

def connect(cursor_factory=None):
    connection = psycopg2.connect(app.config['PSQL_CONNECTION'])
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
        cursor.execute("INSERT INTO address_detail ( line_1, line_2, line_3, line_4, line_5, line_6 ,county, postcode) "
                       "VALUES( %(line1)s, %(line2)s, %(line3)s, %(line4)s, %(line5)s, %(line6)s, %(county)s, "
                       "%(postcode)s ) RETURNING id",
                       {
                           "line1": lines[0], "line2": lines[1], "line3": lines[2],
                           "line4": lines[3], "line5": lines[4], "line6": lines[5],
                           "county": county, "postcode": postcode,
                       })
        detail_id = cursor.fetchone()[0]
        address_string = "{}, {}, {}".format(", ".join(address['address_lines']), address["county"],
                                             address["postcode"])
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
    elif name['type'] in ['Development Corporation', 'Other', 'Coded Name']:
        other = name['other']
    elif name['type'] == 'Limited Company':
        company = name['company']
    elif name['type'] == 'Complex Name':
        complex_number = name['complex']['number']
        complex_name = name['complex']['name']
        # searchable_string = None
    else:
        raise RuntimeError('Unknown name type: {}'.format(name['type']))

    # if name['type'] != 'Complex Name':
    #     searchable_string = get_searchable_string(name_string, company, local_auth, local_auth_area, other)

    # get_searchable_string(name_string=None, company=None, local_auth=None, local_auth_area=None, other=None):
    name_key = create_registration_key(cursor, name)
    cursor.execute("INSERT INTO party_name ( party_name, forename, middle_names, surname, alias_name, "
                   "complex_number, complex_name, name_type_ind, company_name, local_authority_name, "
                   "local_authority_area, other_name, searchable_string, subtype ) "
                   "VALUES ( %(name)s, %(forename)s, %(midnames)s, %(surname)s, %(alias)s, "
                   "%(comp_num)s, %(comp_name)s, %(type)s, %(company)s, "
                   "%(loc_auth)s, %(loc_auth_area)s, %(other)s, %(search_name)s, %(subtype)s ) "
                   "RETURNING id", {
                       "name": name_string, "forename": forename, "midnames": middle_names,
                       "surname": surname, "alias": is_alias, "comp_num": complex_number, "comp_name": complex_name,
                       "type": name['type'], "company": company, "loc_auth": local_auth,
                       "loc_auth_area": local_auth_area, "other": other, "search_name": name_key['key'],
                       'subtype': name_key['indicator']
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


def insert_registration(cursor, details_id, name_id, date, county_id, orig_reg_no=None, expires_date=None):
    logging.debug('Insert registration')
    cursor.execute('LOCK TABLE register in ACCESS EXCLUSIVE MODE;')
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

    # Check if registration_no and date already exist, if they do then increase sequence number
    cursor.execute('select MAX(reg_sequence_no) + 1 AS seq_no '
                   'from register  '
                   'where registration_no=%(reg_no)s AND date=%(date)s',
                   {
                       'reg_no': reg_no,
                       'date': date
                   })
    rows = cursor.fetchall()
    if rows[0]['seq_no'] is None:
        version = 1
    else:
        version = int(rows[0]['seq_no'])

    # Cap it all off with the actual legal "one registration per name":
    cursor.execute("INSERT INTO register (registration_no, debtor_reg_name_id, details_id, date, county_id, "
                   "expired_on, reg_sequence_no) " +
                   "VALUES( %(regno)s, %(debtor)s, %(details)s, %(date)s, %(county)s, %(exp)s, %(seq)s ) RETURNING id",
                   {
                       "regno": reg_no,
                       "debtor": name_id,
                       "details": details_id,
                       'date': date,
                       'county': county_id,
                       'exp': expires_date,
                       'seq': version
                   })
    reg_id = cursor.fetchone()[0]
    return reg_no, reg_id


def mark_as_no_reveal_by_details(cursor, details_id, expired_date=None):
    if expired_date is None:
        expired_date = datetime.date.today()

    cursor.execute("UPDATE register SET expired_on=%(exp)s WHERE details_id=%(did)s", {
        "exp": expired_date, "did": details_id
    })


def mark_as_no_reveal(cursor, reg_no, date, expired_date=None):
    if expired_date is None:
        expired_date = datetime.date.today()

    cursor.execute("UPDATE register SET expired_on=%(exp)s WHERE registration_no=%(regno)s AND date=%(date)s", {
        "exp": expired_date, "regno": reg_no, "date": date
    })


def mark_as_no_reveal_by_id(cursor, register_id, expired_date=None):
    if expired_date is None:
        expired_date = datetime.date.today()

    cursor.execute("UPDATE register SET expired_on=%(exp)s WHERE id = %(id)s ", {
        "exp": expired_date, "id": register_id
    })


def insert_register_details(cursor, request_id, data, date, amends):
    additional_info = data['additional_information'] if 'additional_information' in data else None
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
    if 'parties' in data:
        for party in data['parties']:
            if party['type'] == 'Debtor':
                debtor = party

    if debtor is not None:
        legal_ref = debtor['case_reference']
    else:
        legal_ref = None

    is_priority_notice = None
    prio_notc_expires = None

    # logging.debug(data)
    if 'priority_notice' in data:
        is_priority_notice = True
        # if 'expires' in 'priority_notice':
        prio_notc_expires = data['priority_notice']['expires']
        # else:
        #     prio_notc_expires = data['prio_notice_expires']

    amend_info_type = None
    amend_info_details_orig = None
    amend_info_details_current = None

    amend_type = None
    if 'update_registration' in data:
        update = data['update_registration']
        amend_type = update['type']

        if amend_type == 'Part Cancellation':
            if 'part_cancelled' in update and update['part_cancelled'] != '':
                amend_info_type = 'part_cancelled'
                amend_info_details_current = update['part_cancelled']
            elif 'plan_attached' in update and update['plan_attached'] != '':
                amend_info_type = 'plan_attached'
                amend_info_details_current = update['plan_attached']
        elif amend_type == 'Rectification':
            if 'instrument' in update and update['instrument'] != '':
                amend_info_type = 'instrument'
                amend_info_details_orig = update['instrument']['original']
                amend_info_details_current = update['instrument']['current']
            elif 'chargee' in update and update['chargee'] != '':
                amend_info_type = 'chargee'
                amend_info_details_orig = update['chargee']['original']
                amend_info_details_current = update['chargee']['current']
        elif amend_type == 'Amendment':
            if 'pab' in update and update['pab'] != '':
                amend_info_type = 'PAB'
                amend_info_details_current = update['pab']

    cursor.execute("INSERT INTO register_details (request_id, class_of_charge, legal_body_ref, "
                   "amends, district, short_description, additional_info, amendment_type, priority_notice_no, "
                   "priority_notice_ind, prio_notice_expires, "
                   "amend_info_type, amend_info_details, amend_info_details_orig ) "
                   "VALUES (%(rid)s, %(coc)s, %(legal_ref)s, %(amends)s, %(dist)s, %(sdesc)s, %(addl)s, %(atype)s, "
                   "%(pno)s, %(pind)s, %(pnx)s, %(amd_type)s, "
                   "%(amd_detl_c)s, %(amd_detl_o)s ) "
                   "RETURNING id", {
                       "rid": request_id, "coc": data['class_of_charge'],
                       "legal_ref": legal_ref, "amends": amends, "dist": district,
                       "sdesc": short_description, "addl": additional_info, "atype": amend_type,
                       "pno": priority_notice, 'pind': is_priority_notice, "pnx": prio_notc_expires,
                       "amd_type": amend_info_type, "amd_detl_c": amend_info_details_current,
                       "amd_detl_o": amend_info_details_orig
                   })
    return cursor.fetchone()[0]


# pylint: disable=too-many-arguments
def insert_request(cursor, user_id, applicant, application_type, date, original_data=None):
    if original_data is not None:
        cursor.execute("INSERT INTO ins_bankruptcy_request (request_data) VALUES (%(json)s) RETURNING id",
                       {"json": json.dumps(original_data)})
        ins_request_id = cursor.fetchone()[0]
    else:
        ins_request_id = None

    if 'address_type' in applicant:
        addr_type = applicant['address_type']
    else:
        addr_type = ''

    app_time = datetime.datetime.now().strftime('%H:%M:%S')
    logging.info("INSERT REQUEST AT " + app_time)
    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, "
                   " application_time, " +
                   "ins_request_id, customer_name, customer_address, customer_addr_type, caseworker_uid) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(app_time)s, %(ins_id)s, " +
                   "%(cust_name)s, %(cust_addr)s , %(cust_addr_type)s, %(user)s) RETURNING id",
                   {
                       "key": applicant['key_number'], "app_type": application_type, "app_ref": applicant['reference'],
                       "app_date": date, "app_time": app_time,  "ins_id": ins_request_id,
                       "cust_name": applicant['name'],
                       "cust_addr": applicant['address'], "cust_addr_type": addr_type, 'user': user_id
                   })
    return cursor.fetchone()[0]


def insert_party(cursor, details_id, party):
    occupation = None
    date_of_birth = None
    residence_withheld = False

    if 'occupation' in party:
        occupation = party['occupation']

    if party['type'] == 'Debtor':
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

        if 'addresses' in party:
            for address in party['addresses']:
                insert_address(cursor, address, party_id)

        for name in party['names']:
            name_info = insert_party_name(cursor, party_id, name)
            if party['type'] == 'Debtor':
                names.append(name_info)

    # party_trading
    if debtor_id is not None:
        if 'trading_name' in debtor:
            trading_name = debtor['trading_name']
            cursor.execute("INSERT INTO party_trading (party_id, trading_name) " +
                           "VALUES ( %(party)s, %(trading)s ) RETURNING id",
                           {"party": debtor_id, "trading": trading_name})
    return names, register_details_id


def calc_five_year_expiry(date):
    cdate = datetime.datetime.strptime(date, "%Y-%m-%d")
    if cdate.month == 2 and cdate.day == 29: # leap year fix
        cdate = datetime.datetime(cdate.year + 5, 3, 1)
    else:
        cdate = datetime.datetime(cdate.year + 5, cdate.month, cdate.day)
    cdate += datetime.timedelta(days=10)
    return cdate


def insert_bankruptcy_regn(cursor, details_id, names, date, orig_reg_no):
    logging.debug('Inserting banks reg')
    exdate = calc_five_year_expiry(date)
    reg_nos = []
    if len(names) == 0:  # Migration case only...
        reg_no, reg_id = insert_registration(cursor, details_id, None, date, None, orig_reg_no, exdate)
        reg_nos.append({
            'number': reg_no,
            'date': date,
            'name': None
        })
    
    else:    
        logging.debug(names)
        for name in names:
            reg_no, reg_id = insert_registration(cursor, details_id, name['id'], date, None, orig_reg_no, exdate)
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


def insert_landcharge_regn(cursor, details_id, class_of_charge, names, county_ids, date, orig_reg_no):
    logging.debug('Inserting LC reg')
    if len(names) > 1:
        raise RuntimeError("Invalid number of names: {}".format(len(names)))

    expires_on = None
    if class_of_charge in ['PA', 'DA', 'WO']:
        expires_on = calc_five_year_expiry(date)

    reg_nos = []
    if len(county_ids) == 0:  # can occur on migration or a registration against NO COUNTY
        if len(names) > 0:
            name = names[0]['id']
        else:
            name = None
                
        reg_no, reg_id = insert_registration(cursor, details_id, name, date, None, orig_reg_no, expires_on)
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
                
            reg_no, reg_id = insert_registration(cursor, details_id, name, date, county['id'], orig_reg_no, expires_on)

            reg_nos.append({
                'number': reg_no,
                'date': date,
                'county': county['name'],
            })

    return reg_nos


def insert_counties(cursor, details_id, counties):
    if len(counties) == 1 and (counties[0].upper() == 'NO COUNTY' or counties[0] == ""):
        return []

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
        reg_nos = insert_landcharge_regn(cursor, register_details_id, data['class_of_charge'],
                                         names, county_ids, date, orig_reg_no)

    return reg_nos, register_details_id


def insert_new_registration(cursor, user_id, data):
    # document = None
    # if 'document_id' in data:
    #     document = data['document_id']

    date = datetime.datetime.now().strftime('%Y-%m-%d')

    # request
    original = None
    if 'original_request' in data:
        original = data['original_request']

    request_id = insert_request(cursor, user_id, data['applicant'], 'New registration', date, original)

    if 'dev_registration' in data:
        date = data['dev_registration']['date']

    reg_nos, details_id = insert_record(cursor, data, request_id, date, None, None)
    return reg_nos, details_id, request_id


def get_county_registration_map(cursor, details_id):
    cursor.execute("SELECT r.registration_no, c.name, r.county_id, r.date "
                   "FROM register r, county c "
                   "WHERE register.county_id = county.id "
                   "AND r.details_id=%(detl)s", {'detl': details_id})
    rows = cursor.fetchall()
    result = {}
    for row in rows:
        result[row['name']] = {
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d')
        }
    return result


def update_previous_details(cursor, detl_id, original_detl_id):
    cursor.execute("UPDATE register_details SET cancelled_by = %(canc)s WHERE " +
                   "id = %(id)s AND cancelled_by IS NULL",
                   {
                       "canc": detl_id, "id": original_detl_id
                   })


def set_amends(cursor, new_detl_id, original_detl_id):
    print("setting amends on ", new_detl_id, original_detl_id)
    cursor.execute("UPDATE register_details SET amends = %(original_detl_id)s WHERE " +
                   "id = %(new_detl_id)s AND cancelled_by IS NULL",
                   {
                       "original_detl_id": original_detl_id, "new_detl_id": new_detl_id
                   })


def get_alteration_type(original_details, data):
    # The first three types of alteration correspond to the legacy 'rectification types'. Types 4 and 5
    # are added for this system. Apologies for just giving these numbers. They are:
    # 1: Alters an existing registration entry; implemented by creating a second version, plus chaining a
    # pseudo-entry to hold the details of the rectification. Only the 'second version' is revealed [Rectifications only]
    # 2: Adds a new registration and keeps the original around [Rectifications, amends and renewals]
    # 3: Adds a new registration and 'removes' (as in set no-reveal) the original [Rectifications and Amendments]
    # 4: Alters an existing registration entry; implemented by creating a second version. Only the 'second
    #       version' is revealed [Corrections]
    # 5: Makes no change to the original, but creates a pseudo-entry (not revealed) that effects the additional
    #       information generated. [Part Cancellations of the non-C4/D2 variety]
    if data['update_registration']['type'] == 'Rectification':
        return get_rectification_type(original_details, data)  # will be 1, 2 or 3
    elif data['update_registration']['type'] == 'Renewal':
        return 2
    elif data['update_registration']['type'] == 'Amendment':
        return get_rectification_type(original_details, data)  # amendments are back to 2 or 3!
    elif data['update_registration']['type'] == 'Correction':
        return 4
    elif data['update_registration']['type'] == 'Part Cancellation':
        return 5
    else:
        raise RuntimeError("Unknown alteration type")


def insert_rectification(cursor, user_id, rect_reg_no, rect_reg_date, data, pab_amendment=None):
    # This method is also used for Amendments as they perform the same action!
    logging.debug("Insert rectification called with: " + json.dumps(data))

    # Handle the details records first
    original_details = get_registration_details(cursor, rect_reg_no, rect_reg_date)
    original_details_id = get_register_details_id(cursor, rect_reg_no, rect_reg_date)
    original_regs = get_all_registration_nos(cursor, original_details_id)

    for reg in original_regs:
        reg['details'] = get_registration_details(cursor, reg['number'], reg['date'])

    alter_type = get_alteration_type(original_details, data)

    date_today = datetime.datetime.now().strftime('%Y-%m-%d')
    if 'dev_registration' in data:
        date_today = data['dev_registration']['date']

    request_id = insert_request(cursor, user_id, data['applicant'], data['update_registration']['type'], datetime.datetime.today())

    new_details_id = None
    pseudo_details_id = None
    updated_details_id = None
    pseudo_names = None

    logging.debug("Alteration type is %d", alter_type)

    if alter_type == 1:
        mark_as_no_reveal(cursor, rect_reg_no, rect_reg_date)
        updated_names, updated_details_id = insert_details(cursor, request_id, data, rect_reg_date, original_details_id)
        pseudo_names, pseudo_details_id = insert_details(cursor, request_id, data, date_today, updated_details_id)

    elif alter_type == 2:
        new_names, new_details_id = insert_details(cursor, request_id, data, date_today, original_details_id)
        # if data["update_registration"]["type"] == "Renewal":
        update_previous_details(cursor, request_id, original_details_id)  # set cancelled_by but leave reveal

    elif alter_type == 3:
        mark_as_no_reveal(cursor, rect_reg_no, rect_reg_date)
        new_names, new_details_id = insert_details(cursor, request_id, data, date_today, original_details_id)
        update_previous_details(cursor, request_id, original_details_id)

    elif alter_type == 4:
        # mark_as_no_reveal(cursor, rect_reg_no, rect_reg_date)
        mark_as_no_reveal_by_details(cursor, original_details_id)
        updated_names, updated_details_id = insert_details(cursor, request_id, data, rect_reg_date, original_details_id)

    elif alter_type == 5:
        pseudo_names, pseudo_details_id = insert_details(cursor, request_id, data, date_today, original_details_id)
    # ---- Done with details records -------------------

    # Now apply registrations to everything; updated_ & new_ are always reveal: true; pseudo_ always reveal: false
    reg_nos = []
    if updated_details_id is not None:
        logging.debug('Updated details...')
        # version = original_regs[0]['sequence'] + 1  # Assumed: the sequence numbers always match
        upd_reg_nos = []
        if data['class_of_charge'] not in ['PAB', 'WOB']:
            upd_counties = insert_counties(cursor, updated_details_id, data['particulars']['counties'])
            logging.debug(upd_counties)
            logging.debug(original_regs)
            for index, reg in enumerate(original_regs):  # TODO: account for county added
                county = upd_counties[index]
                name = updated_names[0]['id'] if len(updated_names) > 0 else None
                reg_no, reg_id = insert_registration(cursor, updated_details_id, name, rect_reg_date, county['id'],
                                                     reg['number'])
                upd_reg_nos.append({'number': reg_no, 'date': rect_reg_date, 'county': county['name']})

        else:
            #logging.debug(updated_names)
            #logging.debug(original_details)
            #logging.debug(original_regs)
            # logging.debug('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
            # logging.debug("Link {} to {}".format(rect_reg_no, updated_names[0]['name']['private']['forenames'][0]))
            insert_registration(cursor, updated_details_id, updated_names[0]['id'], rect_reg_date, None, rect_reg_no)
            remaining_names = updated_names[1:]  # Assumes the order returned from DB is consistent... which it now is...

            ni = 0
            for index, reg in enumerate(original_regs):  # For the AKAs...
                if reg['number'] == rect_reg_no:
                    continue

                name = remaining_names[ni]
                ni += 1

                # logging.debug(name)
                # logging.debug(name['id'])
                # logging.debug(name['name'])
                # logging.debug(name['name']['private'])
                # logging.debug(name['name']['private']['forenames'])
                # logging.debug(name['name']['private']['forenames'][0])
                # logging.debug(reg['number'])
                #
                # logging.debug("Link {} to {}".format(reg['number'], name['name']['private']['forenames'][0]))
                reg_no, reg_id = insert_registration(cursor, updated_details_id, name['id'], rect_reg_date, None, reg['number'])
                if 'forenames' in name:
                    upd_reg_nos.append({'number': reg_no, 'date': rect_reg_date, 'forenames': name['forenames'], 'surname': name['surname']})
                else:
                    upd_reg_nos.append({'number': reg_no, 'date': rect_reg_date, 'name': name['name']})
            logging.debug('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')



    if new_details_id is not None:
        logging.debug('New details...')
        if data['class_of_charge'] not in ['PAB', 'WOB']:
            if len(original_details['particulars']['counties']) < len(data['particulars']['counties']):
                # Probably a county addition; TODO: ensure. Also, challenge assumption that -1 is the added county
                # county = [data['particulars']['counties'][-1]]
                county = data['particulars']['counties']
                new_counties = insert_counties(cursor, new_details_id, county) # i_c expect array of str

                reg_no, reg_id = insert_registration(cursor, new_details_id, None, date_today,
                                                     new_counties[-1]['id'], None)
                new_reg_nos = [{"number": reg_no, "date": date_today}]
            else:
                new_counties = insert_counties(cursor, new_details_id, data['particulars']['counties'])
                new_reg_nos = insert_landcharge_regn(cursor, new_details_id, data['class_of_charge'], new_names,
                                                     new_counties, date_today, None)
        else:
            new_reg_nos = insert_bankruptcy_regn(cursor, new_details_id, new_names, date_today, None)
            new_ex_date = calc_five_year_expiry(date_today)
            for regn in original_regs:
                logging.debug('Expire ' + str(regn['number']) + ' on ' + str(new_ex_date))
                mark_as_no_reveal(cursor, regn['number'], regn['date'], new_ex_date)

            for name in new_names:
                oreg = None
                for regn in original_regs:
                    if names_match(regn['details']['parties'][0]['names'][0], name['name']):
                        oreg = regn
                        break

                if oreg is not None:
                    # The name is the same as it's predecessor
                    logging.debug('EXPIRE ' + str(oreg['number']))
                    mark_as_no_reveal(cursor, oreg['number'], oreg['date'])

        reg_nos = new_reg_nos

    if pseudo_details_id is not None:
        logging.debug('Pseudo details...')
        if data['class_of_charge'] not in ['PAB', 'WOB']:
            pseudo_counties = insert_counties(cursor, pseudo_details_id, data['particulars']['counties'])
            pseudo_reg_nos = insert_landcharge_regn(cursor, pseudo_details_id, data['class_of_charge'], pseudo_names, pseudo_counties, date_today, None)
        else:
            pseudo_reg_nos = insert_bankruptcy_regn(cursor, pseudo_details_id, pseudo_names, date_today, None)

        for reg in pseudo_reg_nos:
            mark_as_no_reveal(cursor, reg['number'], reg['date'])
        reg_nos = pseudo_reg_nos
    # --- Done with registrations

    if data['update_registration']['type'] == "Amendment":
        # A combined PAB/WOB amendment... we need to mark the PAB as no-reveal and cancelled by the incoming request
        logging.debug(data['update_registration'])
        if 'pab' in data['update_registration']:
            matcher = re.match("(\d+)\((\d{4}\-\d{1,2}\-\d{1,2})\)", data['update_registration']['pab'])

            pab_reg_no = matcher.group(1)
            pab_date = matcher.group(2)
            pab_details_id = get_register_details_id(cursor, pab_reg_no, pab_date)
            pab = get_registration_details_by_id(cursor, pab_details_id)

            if party_a_is_subset_of_b(pab['parties'][0], data['parties'][0]):
                mark_as_no_reveal_by_details(cursor, pab_details_id)
            else:
                # Oh, if the PAB stays revealed, we must extend it's life...
                pab_ex_date = calc_five_year_expiry(rect_reg_date)
                mark_as_no_reveal_by_details(cursor, pab_details_id, pab_ex_date)

            update_previous_details(cursor, request_id, pab_details_id)

    logging.debug('End of insert rectification')
    return original_regs, reg_nos, request_id


def get_register_details_id(cursor, reg_no, date, class_of_charge=None):
    params = {"regno": reg_no, "date": date}
    if class_of_charge is None:
        sql = "SELECT details_id FROM register WHERE registration_no = %(regno)s AND date=%(date)s "
    else:  # deal with multiple registers having duplicate reg_no and date
        sql = "SELECT details_id FROM register r, register_details rd" \
              " WHERE registration_no = %(regno)s AND date=%(date)s and r.details_id = rd.id " \
              " and rd.class_of_charge = %(class_of_charge)s "
        params["class_of_charge"] = class_of_charge
    sql += " ORDER BY reg_sequence_no DESC FETCH FIRST 1 ROW ONLY"
    logging.debug(sql)
    cursor.execute(sql, params)

    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    elif len(rows) > 1:
        raise RuntimeError("Too many rows retrieved")
    else:
        return rows[0]['details_id']


def get_all_registration_nos(cursor, details_id):
    logging.debug("Get reg nos for {}".format(details_id))
    cursor.execute("SELECT registration_no, date, reg_sequence_no, debtor_reg_name_id FROM register WHERE details_id = %(details)s order by registration_no",
                   {"details": details_id})
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            'number': str(row['registration_no']),
            'date': row['date'].strftime('%Y-%m-%d'),
            'sequence': row['reg_sequence_no'],
            'name_id': row['debtor_reg_name_id']
        })
    logging.debug(results)
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
        raise RuntimeError("No registration found for details {}".format(details_id))
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


def get_corrections_by_date(cursor, date):
    cursor.execute("select r.registration_no, r.date, d.class_of_charge, d.amends, d.cancelled_by, d.request_id, d.amendment_type "
                   "from register r, register_details d, request q "
                   "where r.details_id = d.id and d.request_id = q.id and q.application_type='Correction' "
                   "and q.application_date=%(date)s", {'date': date})
    rows = cursor.fetchall()
    results = []
    for row in rows:
        request_id = row['request_id']
        item = None
        for r in results:
            if r['id'] == request_id:
                item = r
                break
        if item is None:
            item = {
                'application': '',
                'id': request_id,
                'data': []
            }
            results.append(item)

        if row['amends'] is None:
            item['application'] = 'new'
        else:
            item['application'] = row['amendment_type']  # 'amend'

        item['data'].append({
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'class_of_charge': row['class_of_charge']
        })
    return results

        
def get_registrations_by_date(cursor, date):
    cursor.execute('select r.registration_no, r.date, d.class_of_charge, d.amends, d.cancelled_by, d.request_id, '
                   'd.amendment_type '
                   'from register r, register_details d '
                   'where r.details_id = d.id and r.date=%(date)s', {'date': date})
    rows = cursor.fetchall()

    results = []
    for row in rows:
        request_id = row['request_id']
        item = None
        for r in results:
            if r['id'] == request_id:
                item = r
                break
        if item is None:
            item = {
                'application': '',
                'id': request_id,
                'data': []
            }
            results.append(item)

        if row['amends'] is None:
            item['application'] = 'new'
        else:
            item['application'] = row['amendment_type']  # 'amend'

        item['data'].append({
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'class_of_charge': row['class_of_charge']
        })
    return results + get_corrections_by_date(cursor, date)


def read_names(cursor, party, party_id, lead_debtor_id):
    cursor.execute('select n.id, forename, middle_names, surname, complex_number, complex_name, '
                   'name_type_ind, company_name, local_authority_name, local_authority_area, '
                   'other_name, searchable_string, subtype '
                   'from party_name n, party_name_rel pn '
                   'where n.id = pn.party_name_id and pn.party_id = %(id)s order by n.id', {
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
        if name_type == 'Private Individual':
            fornames = [row['forename']]
            middle = row['middle_names']
            if middle is not None and middle != "":
                fornames += middle.split(' ')

            name['private'] = {
                'forenames': fornames,
                'surname': row['surname']
            }
        elif name_type == 'Rural Council' or name_type == 'Parish Council' \
                or name_type == 'County Council' or name_type == 'Other Council':
            name['local'] = {
                'name': row['local_authority_name'],
                'area': row['local_authority_area']
            }
        elif name_type == 'Development Corporation' or name_type == 'Other' or name_type == 'Coded Name':
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

        name['search_key'] = row['searchable_string']
        name['subtype'] = row['subtype']

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

        if 'address_lines' not in address:
            address['address_lines'] = [address['address_string']]
            address['postcode'] = ''
            address['county'] = ''

        party['addresses'].append(address)


def read_parties(cursor, data, details_id, legal_ref, lead_debtor_id):
    cursor.execute("SELECT id, party_type, occupation, date_of_birth, residence_withheld "
                   "FROM party "
                   "WHERE register_detl_id = %(id)s and party_type != 'Court' ", {
                       'id': details_id
                   })
    rows = cursor.fetchall()
    data['parties'] = []
    for row in rows:
        party = {
            'type': row['party_type']
        }

        if row['occupation']:
            party['occupation'] = row['occupation']

        if party['type'] == 'Debtor':

            if row['date_of_birth'] is not None:
                party['date_of_birth'] = row['date_of_birth'].strftime('%Y-%m-%d')
            else:
                party['date_of_birth'] = None
            party['residence_withheld'] = row['residence_withheld']
            party['case_reference'] = legal_ref
            read_addresses(cursor, party, row['id'])

        data['parties'].append(party)
        read_names(cursor, party, row['id'], lead_debtor_id)


def get_lc_counties(cursor, details_id, lead_county_id):
    cursor.execute("SELECT name FROM county WHERE id=%(id)s", {'id': lead_county_id})
    row = cursor.fetchone()
    
    if row is None:  # This is a migrated record with no recorded county
        counties = []
    else:
        counties = [row['name']]

        cursor.execute("select dcr.county_id, c.name  from detl_county_rel dcr, county c " +
                       "where dcr.details_id = %(id)s and dcr.county_id = c.id ", {'id': details_id})
        rows = cursor.fetchall()

        if len(rows) != 0:
            for row in rows:
                cty = row['name']
                if cty not in counties:
                    counties.append(cty)

    return counties


def get_details_from_rows(cursor, rows, fetch_amend_detail=False):
    assert len(rows) > 0
    details_id = rows[0]['id']
    lead_county = rows[0]['county_id']
    lead_debtor_id = rows[0]['debtor_reg_name_id']
    request_id = rows[0]['request_id']

    add_info = ''
    if rows[0]['additional_info'] is not None:
        add_info = rows[0]['additional_info']

    data = {
        'registration': {
            'number': rows[0]['registration_no'],
            'date': rows[0]['date'].strftime('%Y-%m-%d'),
            'sequence': rows[0]['reg_sequence_no']
        },
        'details_id': details_id,
        'class_of_charge': rows[0]['class_of_charge'],
        'status': 'current',
        'entered_addl_info': add_info
        # 'additional_information': add_info
    }

    if rows[0]['expired_on'] is None:
        data['expired_date'] = None
    else:
        data['expired_date'] = rows[0]['expired_on'].strftime("%Y-%m-%d")

    if data['class_of_charge'] not in ['PAB', 'WOB']:
        if rows[0]['priority_notice_ind']:
            data['priority_notice'] = {
                "expires": rows[0]['prio_notice_expires'].strftime('%Y-%m-%d')
            }

        data['particulars'] = {
            'counties': get_lc_counties(cursor, details_id, lead_county),
            'district': rows[0]['district'],
            'description': rows[0]['short_description']
        }

        if rows[0]['priority_notice_no']:
            data['particulars']['priority_notice'] = rows[0]['priority_notice_no']

    register_id = rows[0]['register_id']
    data['register_id'] = rows[0]['register_id']
    if len(rows) > 1:
        data['alternate_register_ids'] = []
        for row in rows[1:]:
            data['alternate_register_ids'].append(row['register_id'])

    logging.debug('------------------')

    legal_ref = rows[0]['legal_body_ref']
    logging.debug(legal_ref)
    logging.debug(add_info)

    if legal_ref is not None and add_info is not None:
        if re.search("^\d+ OF \d{4}$", legal_ref, re.IGNORECASE) and re.search("\d+ OF \d{4}", add_info, re.IGNORECASE):
            # loading migration record
            legal_ref = add_info

    if rows[0]['amends'] is not None:
        amend_of = get_registration_no_from_details_id(cursor, rows[0]['amends'])
        if not fetch_amend_detail and (amend_of['number'] == data['registration']['number'] and amend_of['date'] == data['registration']['date']):
            pass  # Don't show 'amends_registration' where its an update to an existing regn

        else:
            data['amends_registration'] = amend_of
            data['amends_registration']['type'] = rows[0]['amendment_type']

            ait = rows[0]['amend_info_type']
            if ait in ['instrument', 'chargee']:
                data['amends_registration'][ait] = {
                    'original': rows[0]['amend_info_details_orig'],
                    'current': rows[0]['amend_info_details']
                }
            else:
                data['amends_registration'][ait] = rows[0]['amend_info_details']

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

    cursor.execute("select key_number, application_reference, customer_name, customer_address, "
                   "customer_addr_type FROM "
                   "request WHERE id=%(rid)s", {'rid': request_id})
    rows = cursor.fetchall()
    if len(rows) > 0:
            data['applicant'] = {
                'name': rows[0]['customer_name'],
                'address': rows[0]['customer_address'],
                'key_number': rows[0]['key_number'],
                'reference': rows[0]['application_reference'],
                'address_type': rows[0]['customer_addr_type'],
            }

    cursor.execute("SELECT extra_data, original_regn_no FROM migration_status WHERE register_id=%(id)s", {
        "id": register_id
    })
    rows = cursor.fetchall()
    if len(rows) > 0:
        data['migrated'] = {
            'original_number': rows[0]['original_regn_no'],
            'extra_data': rows[0]['extra_data']
        }

    # name, address, keyn, ref
    return data


def get_registration_details_by_id(cursor, details_id, fetch_amend_detail=False):
    cursor.execute("SELECT r.registration_no, r.date, r.expired_on, rd.class_of_charge, rd.id, r.id as register_id, "
                   "rd.legal_body_ref, rd.cancelled_by, rd.amends, rd.request_id, rd.additional_info, "
                   "rd.district, rd.short_description, r.county_id, r.debtor_reg_name_id, rd.amendment_type, "
                   "rd.priority_notice_ind, rd.prio_notice_expires, "
                   "rd.request_id, rd.amend_info_type, rd.amend_info_details, rd.amend_info_details_orig, "
                   "r.reg_sequence_no, rd.priority_notice_no "
                   "from register r, register_details rd "
                   "where r.details_id = rd.id and r.details_id = %(did)s ", {
                       'did': details_id
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return get_details_from_rows(cursor, rows, fetch_amend_detail)


def get_addl_class(cursor, data):
    # Determing whether to use new reg no or original...

    if data['registration']['sequence'] > 1:  # This data can only exist for migrated records
        return

    if 'migrated' in data and data['migrated']['original_number'] != data['registration']['number']:
        cursor.execute("SELECT class_of_charge FROM addl_class_of_charge WHERE "
                       "orig_number =%(no)s AND date=%(date)s ",
                       {
                           "no": data['migrated']['original_number'],
                           "date": data['registration']['date']
                       })
    else:
        cursor.execute("SELECT class_of_charge FROM addl_class_of_charge WHERE "
                       "number=%(no)s AND date=%(date)s ",
                       {
                           "no": data['registration']['number'],
                           "date": data['registration']['date']
                       })
    rows = cursor.fetchall()
    classes = []
    for row in rows:
        classes.append(row['class_of_charge'])

    if len(classes) > 0:
        data['additional_classes'] = classes


def get_registration_details_by_register_id(cursor, register_id):

    sql = "SELECT r.registration_no, r.date, r.expired_on, rd.class_of_charge, rd.id, r.id as register_id, " \
          "rd.legal_body_ref, rd.cancelled_by, rd.amends, rd.request_id, rd.additional_info, rd.district, " \
          "rd.short_description, r.county_id, r.debtor_reg_name_id, rd.amendment_type, rd.priority_notice_ind, " \
          "rd.prio_notice_expires, rd.request_id, rd.amend_info_type, " \
          "rd.amend_info_details, rd.amend_info_details_orig, r.reg_sequence_no, rd.priority_notice_no " \
          "from register r, register_details rd " \
          "where r.id=%(regid)s and r.details_id = rd.id "

    cursor.execute(sql, {'regid': register_id})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    data = get_details_from_rows(cursor, rows)
    get_addl_class(cursor, data)
    return data


def get_registration_details(cursor, reg_no, date, class_of_charge=None):
    params = {'reg_no': reg_no, 'date': date}
    sql = "SELECT r.registration_no, r.date, r.expired_on, rd.class_of_charge, rd.id, r.id as register_id, " \
          "rd.legal_body_ref, rd.cancelled_by, rd.amends, rd.request_id, rd.additional_info, rd.district, " \
          "rd.short_description, r.county_id, r.debtor_reg_name_id, rd.amendment_type, rd.priority_notice_ind, " \
          "rd.prio_notice_expires, rd.request_id, rd.amend_info_type, " \
          "rd.amend_info_details, rd.amend_info_details_orig, r.reg_sequence_no, rd.priority_notice_no " \
          "from register r, register_details rd " \
          "where r.registration_no=%(reg_no)s and r.date=%(date)s and r.details_id = rd.id " 

    if class_of_charge is not None:
        sql += " and rd.class_of_charge = %(class_of_charge)s "
        params["class_of_charge"] = class_of_charge

    sql += "ORDER BY r.reg_sequence_no DESC FETCH FIRST ROW ONLY"  # put this back temporarily

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    data = get_details_from_rows(cursor, rows)
    get_addl_class(cursor, data)
    return data


def get_head_of_chain(cursor, reg_no, date, follow_part_cans=False):
    # reg_no/date could be anywhere in the 'chain', though typically would be the start
    # as cancelled_by is a request_id, navigate by request_ids until we find the uncancelled
    # head entry
    cursor.execute('SELECT d.request_id, d.id FROM register r, register_details d '
                   'WHERE registration_no=%(reg)s AND date=%(date)s AND r.details_id = d.id ' +
                   'ORDER BY r.reg_sequence_no DESC ' +
                   'FETCH FIRST 1 ROW ONLY',
                   {"reg": reg_no, "date": date})
    row = cursor.fetchone()
    detail_id = row['id']  # row['request_id']

    # start at request id; get id where amends_id = this-id

    next_id = detail_id
    while True:
        # This is nasty, but the part cans exclusion was added to fix one bug, but in turn has broken
        # additional information generation
        if follow_part_cans:
            cursor.execute('SELECT id FROM register_details WHERE amends = %(id)s', {"id": next_id})
        else:
            cursor.execute("SELECT id FROM register_details WHERE amends = %(id)s "
                           " and amendment_type <> 'Part Cancellation' ", {"id": next_id})
        rows = cursor.fetchall()

        if len(rows) == 0:
            return next_id

        if len(rows) > 1:
            raise RuntimeError('Unexpected multiple amendment in get_head_of_chain')

        next_id = rows[0]['id']


def get_request_id(cursor, details_id):
    sql = "SELECT request_id FROM register_details WHERE id = %(id)s"
    params = {"id": details_id}
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    elif len(rows) > 1:
        raise RuntimeError("Too many rows retrieved")
    else:
        return rows[0]['request_id']


def supersede_register(cursor, registration_no, registration_date, original_details_id, new_details_id):
    # get original row
    sql = " select * from register where registration_no = %(registration_no)s and date =%(date)s and " \
          " details_id = %(details_id)s " \
          " order by reg_sequence_no desc FETCH FIRST 1 ROW ONLY"
    cursor.execute(sql,
                   {
                       "registration_no": registration_no,
                       "date": registration_date,
                       "details_id": original_details_id
                   })
    rows = cursor.fetchall()
    orig_register_id = rows[0]["id"]
    debtor_reg_name_id = rows[0]["debtor_reg_name_id"]
    county_id = rows[0]["county_id"]
    seq_no = rows[0]["reg_sequence_no"]
    seq_no += 1
    # create a new row and associate it with the new details id.
    sql = "insert into register(registration_no, debtor_reg_name_id, details_id, date,  county_id, expired_on, " \
          " reg_sequence_no) values (%(registration_no)s, %(debtor_reg_name_id)s, %(details_id)s, %(date)s, " \
          " %(county_id)s, %(exp)s, %(reg_sequence_no)s)"
    cursor.execute(sql, {"registration_no": registration_no, "debtor_reg_name_id": debtor_reg_name_id,
                         "details_id": new_details_id, "date": registration_date, "county_id": county_id,
                         "exp": datetime.datetime.now().strftime('%Y-%m-%d'),
                         "reg_sequence_no": seq_no
                         })
    # mark the superseded row as no_reveal
    mark_as_no_reveal_by_id(cursor, orig_register_id)
    return rows[0]


def insert_cancellation(data, user_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        orig_registration_no = data["registration_no"]
        orig_date = data["registration"]["date"]
        if "class_of_charge" in data:
            orig_class_of_charge = data["class_of_charge"]
        else:
            orig_class_of_charge = None
        original_details_id = get_register_details_id(cursor, orig_registration_no, orig_date, orig_class_of_charge)
        latest_details_id = get_head_of_chain(cursor, orig_registration_no, orig_date, True)

        original_regs = get_all_registration_nos(cursor, original_details_id)
        canc_date = datetime.datetime.now().strftime('%Y-%m-%d')
        if 'dev_registration' in data:
            canc_date = data['dev_registration']['date']

        canc_request_id = \
            insert_request(cursor, user_id, data['applicant'], data['update_registration']['type'], canc_date)
        detl_data = get_registration_details(cursor, orig_registration_no, orig_date, orig_class_of_charge)

        # On full cancellation if there is more than 1 registration for the original register_details
        # we need to create a new "register_details" row and associate the register row of the register being cancelled
        # with the new details row this is to avoid all linked (i.e. multi count or multi AKA) registers being
        # cancelled in one go
        if len(original_regs) > 1:
            original_request_id = get_request_id(cursor, original_details_id)
            names, new_details_id = insert_details(cursor, original_request_id, detl_data, orig_date, None)

            latest_details_id = new_details_id
            if detl_data['class_of_charge']in ['PAB', 'WOB']:
                # set the name so only 1 register is cancelled.
                detl_data['parties'][0]['names'] = [detl_data['parties'][0]['names'][0]]
            else:
                # for a LC the whole list of counties from the original request is pulled back
                # we just need the one specifically linked to the entered reg number
                if detl_data['particulars']['counties']:
                    detl_data['particulars']['counties'] = get_county(cursor, orig_registration_no, orig_date)
                insert_counties(cursor, new_details_id, detl_data['particulars']['counties'])

            # add a new register row for the appn being cancelled with the next sequence number
            if data['update_registration']['type'] == "Cancellation":
                supersede_register(cursor, orig_registration_no, orig_date, original_details_id, new_details_id)
                original_details_id = new_details_id
        # update_registration contains part_cancelled and plan_attached data
        detl_data['update_registration'] = data['update_registration']
        reg_nos, canc_details_id = insert_record(cursor, detl_data, canc_request_id, canc_date, latest_details_id)
                                                 #original_details_id)

        # if full cancellation mark all rows as no reveal
        if data['update_registration']['type'] == "Cancellation":
            #for reg in original_regs:
            #    mark_as_no_reveal(cursor, reg['number'], reg['date'])

            # Mark all entries on the orig reg as no reveal
            # check this is a normal register, not a C4/D2 style one
            if orig_class_of_charge is not None:
                logging.debug('ORIG: ' + orig_class_of_charge)
                multi_reg = get_multi_registrations(cursor, orig_date, orig_registration_no)
                print("multi reg ", multi_reg)
                for m_regs in multi_reg:
                    for m_reg in m_regs["data"]:
                        if m_reg["class_of_charge"] == orig_class_of_charge:
                            mark_as_no_reveal_by_id(cursor, m_reg["register_id"])
            else:
                mark_as_no_reveal(cursor, orig_registration_no, orig_date)
            # Only set cancelled_by on full cancellation
            update_previous_details(cursor, canc_request_id, original_details_id)
        # Mark all cancellation registrations as no reveal.
        for reg in reg_nos:
            mark_as_no_reveal(cursor, reg['number'], reg['date'])
        logging.audit(format_message("Cancelled entry: %s"), json.dumps(reg_nos))
        complete(cursor)
        logging.info(format_message("Cancellation committed"))
    except:
        rollback(cursor)
        raise
    return len(reg_nos), reg_nos, canc_request_id


def insert_renewal(data, user_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        orig_registration_no = data["registration_no"]
        orig_date = data["registration"]["date"]
        orig_class_of_charge = data["class_of_charge"]
        detl_data = get_registration_details(cursor, orig_registration_no, orig_date, orig_class_of_charge)
        detl_data['update_registration'] = data['update_registration']
        detl_data['applicant'] = data['applicant']
        original_regs, reg_nos, renewal_request_id = \
            insert_rectification(cursor, user_id, orig_registration_no, orig_date, detl_data, None)

        logging.audit(format_message("Renewed entry: was %s, now %s"), json.dumps(original_regs), json.dumps(reg_nos))
        complete(cursor)
    except:
        rollback(cursor)
        raise
    return len(reg_nos), reg_nos, renewal_request_id, original_regs


def insert_lc_county(cursor, register_details_id, county):
    county_id = get_county_id(cursor, county)
    cursor.execute("INSERT INTO detl_county_rel (county_id, details_id) " +
                   "VALUES( %(county_id)s, %(details_id)s ) RETURNING id",
                   {
                       "county_id": county_id, "details_id": register_details_id
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        raise RuntimeError("Invalid county ID: {}".format(county))

    return rows[0], county_id


def get_county_id(cursor, county):
    cursor.execute("SELECT id FROM county WHERE UPPER(name) = %(county)s",
                   {
                       "county": county.upper()
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        raise RuntimeError("Invalid county: {}".format(county))
    return rows[0]['id']


def get_register_request_details(request_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    try:
        sql = " Select a.request_id, b.date as registration_date, b.registration_no, c.customer_name, " \
              " c.customer_address, c.key_number, c.customer_addr_type, c.transaction_fee, " \
              " c.application_type, c.application_reference, c.application_date " \
              " from register_details a, register b, request c " \
              " where a.request_id = %(request_id)s and a.id = b.details_id and a.request_id = c.id "

        cursor.execute(sql, {"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    registrations = []
    for row in rows:
        registration = {"request_id": row["request_id"], "registration_date": str(row["registration_date"]),
                        "registration_no": row["registration_no"], 'transaction_fee': row['transaction_fee'],
                        'application_type': row['application_type'], 'application_date': str(row['application_date']),
                        'applicant': {'name': row['customer_name'], 'address': row['customer_address'],
                                      'key_number': row['key_number'], 'address_type': row['customer_addr_type'],
                                      'reference': row['application_reference']}}

        registrations.append(registration)
    return registrations


def get_search_request_details(request_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

    try:
        sql = " Select a.id as request_id, b.id as search_details_id, b.search_timestamp, b.type, b.counties, " \
              " a.key_number, a.application_type, a.application_reference, a.application_date, a.customer_name, " \
              " a.customer_address, a.customer_addr_type, a.transaction_fee, b.certificate_date, b.expiry_date, " \
              " b.certificate_no " \
              " from request a, search_details b " \
              " where a.id = %(request_id)s and a.id = b.request_id "
        cursor.execute(sql, {"request_id": request_id})
        rows = cursor.fetchall()
    finally:
        complete(cursor)
    request = {}

    for row in rows:
        request = {'request_id': row['request_id'],
                   'certificate_date': str(row['certificate_date']), 'expiry_date': str(row['expiry_date']),
                   'application_date': str(row['application_date']), 'search_details_id': row['search_details_id'],
                   'search_timestamp': str(row['search_timestamp']), 'type': row['type'],
                   'counties': row['counties'], 'search_details': [],
                   'cert_no': row['certificate_no'],
                   'applicant': {'name': row['customer_name'], 'address': row['customer_address'],
                                 'key_number': row['key_number'], 'address_type': row['customer_addr_type'],
                                 'reference': row['application_reference']}}

        # Def causes an issue in test... result printer is happy for it to be absent, but not happy for it to be null
        if row['transaction_fee'] is not None:
            request['transaction_fee'] = row['transaction_fee']

        if request['search_details_id'] is None:
            request = {'noresult': 'nosearchdetlid'}
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
    for row in rows:  # for each name searched against
        name_data = {'id': row['search_name_id'],
                     'names': [{'type': row['name_type']}],
                     'year_from': row['year_from'], 'year_to': row['year_to'], 'results': []}
        name_type = row['name_type']
        if name_type == 'Private Individual':
            name_data['names'][0]['private'] = {'forenames': row['forenames'].split(), 'surname': row['surname']}
        elif name_type == 'Rural Council' or name_type == 'Parish Council' \
                or name_type == 'County Council' or name_type == 'Other Council':
            name_data['names'][0]['local'] = {
                'name': row['local_authority_name'],
                'area': row['local_authority_area']
            }
        elif name_type == 'Development Corporation' or name_type == 'Other' or name_type == 'Coded Name':
            name_data['names'][0]['other'] = row['other_name']
        elif name_type == 'Limited Company':
            name_data['names'][0]['company'] = row['company_name']
        elif name_type == 'Complex Name':
            name_data['names'][0]['complex'] = {
                'name': row['complex_name'],
                'number': row['complex_number']
            }
        results = []
        cursor = connect(cursor_factory=psycopg2.extras.DictCursor)

        res_id_list = sorted(set(row['result'])) #  workaround to remove duplicates in search_results.result
        for res_id in res_id_list:
            details = get_registration_details_from_register_id(res_id)

            results.append(details)

        name_data['results'] = results
        sn_data.append(name_data)
        complete(cursor)
    return sn_data


def get_registration_details_from_register_id(register_id):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    res_data = get_registration_details_by_register_id(cursor,register_id)
    if 'particulars' in res_data:
        if 'counties' in res_data['particulars']:
            if len(res_data['particulars']['counties']) > 1:
                county = get_county_by_reg_id(cursor, register_id)
                res_data['particulars']['counties'] = county
    addl_info = get_additional_info(cursor, res_data)
    if addl_info is not None:
        res_data['additional_information'] = addl_info
    data = [res_data]
    complete(cursor)

    # cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # sql = 'select registration_no, date from register where id = %(register_id)s '
    # cursor.execute(sql, {"register_id": register_id})
    # rows = cursor.fetchall()
    # complete(cursor)
    # results = []
    # for row in rows:
    #     results.append({
    #         'number': str(row['registration_no']),
    #         'date': str(row['date'])
    #     })
    # cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    # data = []
    # for res in results:
    #     res_data = get_registration_details(cursor, res['number'], res['date'])
    #     if 'particulars' in res_data:
    #         if 'counties' in res_data['particulars']:
    #             if len(res_data['particulars']['counties']) > 1:
    #                 county = get_county(cursor, res['number'], res['date'])
    #                 res_data['particulars']['counties'] = county
    #     addl_info = get_additional_info(cursor, res_data)
    #     if addl_info is not None:
    #         res_data['additional_information'] = addl_info
    #     data.append(res_data)
    # complete(cursor)
    return data


def get_k22_request_id(registration_no, registration_date):
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    sql = "select b.request_id from register a, register_details b where a.registration_no = %(registration_no)s " \
          " and a.date = %(registration_date)s and a.details_id = b.id ORDER BY a.reg_sequence_no DESC " \
          " FETCH FIRST 1 ROW ONLY"
    cursor.execute(sql, {"registration_no": registration_no, "registration_date": registration_date})
    rows = cursor.fetchall()
    complete(cursor)
    req_id = None
    for row in rows:
        req_id = row['request_id']

    data = {'request_id': req_id}
    cursor = connect(cursor_factory=psycopg2.extras.DictCursor)
    complete(cursor)
    return data


def get_entry_summary(cursor, details_id):
    cursor.execute('SELECT r.registration_no, r.date, r.reg_sequence_no, r.expired_on, d.amendment_type, d.amends, '
                   ' d.class_of_charge '
                   'FROM register r, register_details d '
                   'WHERE r.details_id = d.id AND d.id = %(did)s', {
                       'did': details_id
                   })
    rows = cursor.fetchall()

    if len(rows) == 0:
        raise RuntimeError('No rows returned for id {}'.format(details_id))

    # if len(rows) != 1:
    #     raise RuntimeError("Unexpected return row count in get_entry_summary")
    registrations = []
    for row in rows:
        registrations.append({
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'sequence': row['reg_sequence_no']
        })

    data = {
        'registrations': registrations,
        'id': details_id,
        'class_of_charge': rows[0]['class_of_charge'],
        'application': "New Registration" if rows[0]['amendment_type'] is None else rows[0]['amendment_type'],
        'amends': rows[0]['amends']
    }

    if rows[0]['expired_on'] is None:
        data['expired_date'] = None
    else:
        data['expired_date'] = rows[0]['expired_on'].strftime("%Y-%m-%d")

    return data


def get_registration_history_from_details(cursor, details_id):
    results = []
    entry = get_entry_summary(cursor, details_id)
    results.append(entry)

    while entry['amends'] is not None:
        entry = get_entry_summary(cursor, entry['amends'])
        results.append(entry)

    return results


def get_registration_history(cursor, reg_no, date):
    results = []
    cursor.execute('SELECT details_id '
                   'FROM register '
                   'WHERE registration_no=%(reg_no)s AND date = %(date)s' +
                   'ORDER BY reg_sequence_no DESC ' +
                   'FETCH FIRST 1 ROW ONLY', {
                       'date': date, 'reg_no': reg_no
                   })
    rows = cursor.fetchall()
    if len(rows) > 1:
        raise RuntimeError("Unexpected multiple return rows in get_registration_history")

    if len(rows) == 0:
        return []

    entry = get_entry_summary(cursor, rows[0]['details_id'])
    results.append(entry)
    while entry['amends'] is not None:
        entry = get_entry_summary(cursor, entry['amends'])
        results.append(entry)

    return results


# There's a convention on how the additional information is to be recorded on the various
# types of registration, rectification, part cancellation etc.
# These follow a fixed format, so there is no real need for people to actually type it in.
# With just a few parameters, we should be able to figure out the additional information
# for any record.


def reformat_date_string(date):
    return re.sub("(\d{4})\-(\d\d)\-(\d\d)", r"\3/\2/\1", date)


def get_update_information(cursor, reg_no, reg_date):
    return {
        'part_cancelled': 'that bit, there'
    }


def additional_info_index(addl_info, substring):
    for index, line in enumerate(addl_info):
        if substring in line:
            return index
    return -1


def get_part_cancellation_additional_info(cursor, details):
    update_info = get_update_information(cursor, details['registration']['number'], details['registration']['date'])

    # "amends_registration": {
    #   "plan_attached": "the land edged red",
    #   "number": 1007,
    #   "date": "2014-06-06",
    #   "type": "Part Cancellation"
    # },

    if 'part_cancelled' in details['amends_registration']:
        additional_info = 'PART CAN {} REGD {} SO FAR ONLY AS IT RELATES TO {} BEING PART OF LAND REGD.'.format(
            details['registration']['number'],
            reformat_date_string(details['registration']['date']),
            details['amends_registration']['part_cancelled'].upper()
        )
    elif 'plan_attached' in details['amends_registration']:
        additional_info = 'PART CAN {} REGD {} SO FAR ONLY AS IT RELATES TO {} AS DESC ON APPN TO CANCEL.'.format(
            details['registration']['number'],
            reformat_date_string(details['registration']['date']),
            details['amends_registration']['plan_attached'].upper()

        )
    else:
        raise RuntimeError('Invalid amendment information')

    return additional_info


def get_rectification_additional_info_prev(cursor, details, next_details):
    rect_type = get_rectification_type(details, next_details)
    infos = []

    if rect_type == 1:
        # In this case, prev and current have the same registration number; the amendment is recorded
        # by next, a non-revealed pseudo-entry (sigh)

        # logging.debug(next_details)

        if 'amended_by' in next_details:
            # Because 'next' is the same registration, we need to know the number that amended next
            amend_details = next_details['amended_by']
        else:
            logging.warning('Unable to proceed')
            return []  # not much we can do...

        # logging.debug('XXXXXXXXXXXX')
        # logging.debug(details)
        # logging.debug(next_details)
        # logging.debug('XXXXXXXXXXXX')

        if details['particulars']['description'].upper() != next_details['particulars']['description'].upper():
            infos.append('SHORT DESCRIPTION RECTIFIED FROM {} BY {} REGD {}.'.format(
                details['particulars']['description'].upper(), amend_details['number'],
                reformat_date_string(amend_details['date'])
            ))

        if details['particulars']['district'].upper() != next_details['particulars']['district'].upper():
            infos.append('DISTRICT RECTIFIED FROM {} BY {} REGD {}.'.format(
                details['particulars']['district'].upper(), amend_details['number'],
                reformat_date_string(amend_details['date'])
            ))

        if 'instrument' in next_details['amends_registration']:
            infos.append('DATE OF INSTRUMENT RECTIFIED FROM {} TO {} BY {} REGD {}.'.format(
                reformat_date_string(next_details['amends_registration']['instrument']['original'].upper()),
                reformat_date_string(next_details['amends_registration']['instrument']['current'].upper()),
                amend_details['number'],
                reformat_date_string(amend_details['date'])
            ))

        if 'chargee' in next_details['amends_registration']:
            infos.append('CHARGEE RECTIFIED TO {} FROM {} BY {} REGD {}.'.format(
                next_details['amends_registration']['chargee']['current'].upper(),
                next_details['amends_registration']['chargee']['original'].upper(),
                amend_details['number'],
                reformat_date_string(amend_details['date'])
            ))

    if rect_type in [2, 3]:  # == 2:
        this_name = eo_name_string(details).upper() if details is not None else None
        next_name = eo_name_string(next_details).upper() if next_details is not None else None

        if next_name is not None and next_name != this_name:
            infos.append('NAME PREVIOUSLY REGISTERED AS {} UNDER {} REGD {}.'.format(
                this_name.upper(),
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

    if rect_type == 2:
        counties = details['particulars']['counties']
        next_counties = next_details['particulars']['counties']
        if len(next_counties) > len(counties):
            # As there's no facility to remove counties, assume counties is a subset of next_counties
            infos.append('PREVIOUSLY REGISTERED ONLY IN COUNTY OF {} UNDER {} REGD {}.'.format(
                counties[0].upper(),
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

    if rect_type == 3:
        if details['particulars']['counties'][0].upper() != next_details['particulars']['counties'][0].upper():
            infos.append('COUNTY PREVIOUSLY REGD AS {} UNDER {} REGD {}.'.format(
                details['particulars']['counties'][0].upper(),
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

        if details['class_of_charge'] != next_details['class_of_charge']:
            infos.append('CLASS OF CHARGE PREVIOUSLY REGD AS {} UNDER {} REGD {}.'.format(
                details['class_of_charge'],
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

    return infos


def get_rectification_additional_info_next(cursor, details, prev_details):
    rect_type = get_rectification_type(prev_details, details)

    infos = []
    if rect_type in [2, 3]:
        prev_name = eo_name_string(prev_details) if prev_details is not None else None
        this_name = eo_name_string(details) if details is not None else None

        if prev_name is not None and prev_name != this_name:
            infos.append('NAME RECTIFIED TO {} BY {} REGD {}.'.format(
                this_name.upper(),
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

    if rect_type == 2:
        counties = details['particulars']['counties']
        prev_counties = prev_details['particulars']['counties']
        if len(prev_counties) < len(counties):
            # As there's no facility to remove counties, assume counties is a subset of next_counties
            infos.append('CHARGE PREVIOUSLY REGD SOLELY UNDER COUNTY OF {} NOW REGD IN ADDITIONAL COUNTY OF {} BY {} REGD {}.'.format(
                prev_counties[0].upper(),
                counties[0].upper(),
                details['registration']['number'],
                reformat_date_string(details['registration']['date'])
            ))

    return infos


def get_court_additional_info(cursor, details):
    debtor = None
    for party in details['parties']:
        if party['type'] == 'Debtor':
            debtor = party

    if debtor is None:
        # This can happen on placeholder regs
        return ''

    if debtor['case_reference'] is None:
        caseref = ''
    else:
        caseref = debtor['case_reference'].upper()
        m = re.match("^(.+)\s(\d+ OF \d{4})$", caseref)
        if m:
            caseref = "{} NO {}".format(m.group(1), m.group(2))
        else:
            m = re.match("^(\d+ OF \d{4})$", caseref)
            if m:
                caseref = "NO {}".format(m.group(1))
            else:
                caseref = 'ADJUDICATOR REF ' + caseref

    return caseref


def get_amend_additional_info_next(cursor, details, previous):
    # assume debtor is party one for now...
    name1 = details['parties'][0]['names'][0]
    name2 = previous['parties'][0]['names'][0]

    if not names_match(name1, name2):
        name = ' '.join(name1['private']['forenames']) + ' ' + name1['private']['surname']

        return "NAME OF DEBTOR AMENDED TO {} BY {} REGD {}.".format(
            name.upper(),
            details['registration']['number'],
            reformat_date_string(details['registration']['date'])
        )

    return ''


def get_amendment_additional_info(cursor, details, next_details):
    wob_fragment = "THIS REGISTRATION AMENDS {} DATED {}".format(
        details['registration']['number'],
        reformat_date_string(details['registration']['date'])
    )

    pab_fragment = ""
    if 'amends_registration' in next_details and 'PAB' in next_details['amends_registration']:
        matcher = re.match("(\d+)\((\d{4}\-\d{1,2}\-\d{1,2})\)", next_details['amends_registration']['PAB'])
        pab_reg_no = matcher.group(1)
        pab_date = matcher.group(2)
        pab_fragment = " & {} DATED {}".format(pab_reg_no, reformat_date_string(pab_date))

    return wob_fragment + pab_fragment + "."


def get_renewal_additional_info_prev(cursor, details, next, addl_info):
    index = additional_info_index(addl_info, 'RENEWED BY')

    if index != -1:
        addl_info.insert(index, "RENEWAL OF {} REGD {}".format(
            details['registration']['number'],
            reformat_date_string(details['registration']['date'])
        ))
    else:
        addl_info.append("RENEWAL OF {} REGD {}".format(
            details['registration']['number'],
            reformat_date_string(details['registration']['date'])
        ))


def get_renewal_additional_info_next(cursor, details, prev, addl_info):
    addl_info.insert(0, "RENEWED BY {} REGD {}".format(
        details['registration']['number'],
        reformat_date_string(details['registration']['date'])
    ))


def get_additional_info_text(addl_info):
    result = ''
    for index, line in enumerate(addl_info):
        logging.debug("{}: {}".format(index, line))
        if index == 0:
            result = line
        else:
            # previous_line = addl_info[index - 1]
            #
            # if 'RENEWED BY' in line and ('RENEWED BY' in previous_line or 'RENEWAL OF' in previous_line):
            #     result += ' NOW FURTHER ' + line
            #
            # elif 'RENEWAL OF' in line and 'RENEWAL OF' in previous_line:
            #     new_line = re.sub('RENEWAL OF', 'WHICH RENEWED', line)
            #     result += ' ' + new_line
            #
            # elif 'NAME RECTIFIED TO' in line and ('NAME RECTIFIED TO' in previous_line or 'NAME PREVIOUSLY REGISTERED' in previous_line):
            #     new_line = re.sub('NAME RECTIFIED TO', 'NOW FURTHER RECTIFIED TO', line)
            #     result += ' ' + new_line
            #
            # elif 'NAME PREVIOUSLY REGISTERED' in line and 'NAME PREVIOUSLY REGISTERED AS' in previous_line:
            #     new_line = re.sub('NAME PREVIOUSLY REGISTERED AS', 'AND LATER RECTIFIED TO', line)
            #     result += ' ' + new_line
            #
            # else:
            result += '  ' + line

    return result.strip()


def get_migration_info(cursor, reg_no, date):
    cursor.execute('SELECT m.extra_data FROM register r, migration_status m '
                   'WHERE r.registration_no=%(reg_no)s AND r.date=%(date)s AND r.id = m.register_id '
                   'ORDER BY r.reg_sequence_no DESC ' +
                   'FETCH FIRST 1 ROW ONLY', {
                       'date': date, 'reg_no': reg_no
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return rows[0]['extra_data']


def get_additional_info(cursor, details):
    migrated = get_migration_info(cursor, details['registration']['number'], details['registration']['date'])
    # if migrated is not None:
    #     if 'amend_info' in migrated:
    #         return migrated['amend_info']
    #     else:
    #         return ''

    # details is being passed in...
    head_details_id = get_head_of_chain(cursor, details['registration']['number'],
                                        details['registration']['date'], True)
    logging.debug('Head is ' + str(head_details_id))
    history = get_registration_history_from_details(cursor, head_details_id)
    # logging.debug(len(history))
    # logging.debug(history)

    register = []
    for record in history:
        register.append(get_registration_details_by_id(cursor, record['id'], True))

    logging.debug(len(register))

    addl_info = []
    forward = True
    court_added = False

    for index, entry in enumerate(register):
        this = register[index]
        prev = register[index + 1] if index < len(register) - 1 else None
        next = register[index - 1] if index > 0 else None
        # logging.info('------->')
        # logging.debug(this)
        # logging.debug(prev)
        # logging.debug(next)
        # logging.info('<------')


        if entry['entered_addl_info'] is not None and entry['entered_addl_info'] != '':
            a_info = entry['entered_addl_info'].upper()

            logging.debug(a_info)
            if re.search("NO \d+ OF \d{4}", a_info):
                pass  # Don't put on entered addl info if its a court reference
            else:
                addl_info.insert(0, a_info)

        if entry['details_id'] == details['details_id']:  # This is the record of interest
            logging.info('Switch')
            forward = False

            if entry['class_of_charge'] in ['PAB', 'WOB']:
                addl_info.insert(0, get_court_additional_info(cursor, entry))

        elif migrated is None:
            if not forward:
                logging.debug('BACKWARD')
                if 'amends_registration' in next and next['amends_registration']['type'] == 'Rectification':
                    next_migrated = get_migration_info(cursor,
                                                       next['amends_registration']['number'],
                                                       next['amends_registration']['date'])
                    if next_migrated is None:  # if the 'next' rectification was migrated don't build additional info.
                        addl_info = get_rectification_additional_info_prev(cursor, this, next) + addl_info
                    # addl_info.insert(0, get_rectification_additional_info_prev(cursor, this, next))

                if 'amends_registration' in next and next['amends_registration']['type'] == 'Amendment':
                    addl_info.append(get_amendment_additional_info(cursor, this, next))

                if 'amends_registration' in next and next['amends_registration']['type'] == 'Renewal':
                    get_renewal_additional_info_prev(cursor, this, next, addl_info)

                # if entry['entered_addl_info'] is not None and entry['entered_addl_info'] != '':
                #     addl_info.insert(0, entry['entered_addl_info'])

            else:
                logging.debug('FORWARD')
                if this is not None and 'amends_registration' in this and this['amends_registration']['type'] == \
                        'Rectification':
                    addl_info = get_rectification_additional_info_next(cursor, this, prev) + addl_info
                    # addl_info.insert(0, get_rectification_additional_info_next(cursor, this, prev))

                if this is not None and 'amends_registration' in this and this['amends_registration']['type'] == \
                        'Part Cancellation':
                    addl_info.append(get_part_cancellation_additional_info(cursor, this))

                if this is not None and 'amends_registration' in this and this['amends_registration']['type'] == \
                        'Renewal':
                    get_renewal_additional_info_next(cursor, this, prev, addl_info)

                if this is not None and 'amends_registration' in this and this['amends_registration']['type'] == \
                        'Amendment':
                    addl_info.append(get_amend_additional_info_next(cursor, this, prev))

    uniques = []
    for item in addl_info:
        if not item in uniques:
            uniques.append(item)

    logging.info({
        "array": uniques,
        "text": get_additional_info_text(uniques)
    })

    return get_additional_info_text(uniques)
    # Convienient debug array:
    # return {
    #     "array": addl_info,
    #     "text": get_additional_info_text(addl_info)
    # }


def get_multi_registrations(cursor, registration_date, registration_no):
    # when multiple registrations exist for the same reg no and date return the relevant data
    cursor.execute("select r.registration_no, r.date, r.reg_sequence_no, d.class_of_charge, d.amends, d.cancelled_by, "
                   "d.request_id, d.amendment_type, r.id as register_id "
                   " from register r, register_details d where r.details_id = d.id and "
                   "r.date=%(date)s and r.registration_no=%(registration_no)s and cancelled_by is null ",
                   {'date': registration_date, 'registration_no': registration_no})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return []

    results = []
    max_seq = -1
    for row in rows:
        if row['reg_sequence_no'] > max_seq:
            max_seq = row['reg_sequence_no']

        request_id = row['request_id']
        item = None
        for r in results:
            if r['id'] == request_id:
                item = r
                break
        if item is None:
            item = {
                'application': '',
                'id': request_id,
                'data': []
            }
            results.append(item)

        if row['amends'] is None:
            item['application'] = 'new'
        else:
            item['application'] = row['amendment_type']  # 'amend'

        item['data'].append({
            'number': row['registration_no'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'class_of_charge': row['class_of_charge'],
            'register_id': row["register_id"]
        })

    logging.debug('GET ADDITIONAL CLASSES')
    if max_seq == 1:
        cursor.execute("select r.registration_no, r.date, d.amends, "
                       "d.cancelled_by, d.request_id, d.amendment_type, r.id as register_id, a.class_of_charge "
                       "from register r, addl_class_of_charge a, register_details d "
                       "where r.details_id = d.id "
                       "and r.date = a.date and r.registration_no = a.number "
                       "and cancelled_by is null "
                       "and r.date=%(date)s and r.registration_no=%(no)s ",
                       {'no': registration_no, 'date': registration_date})
        rows = cursor.fetchall()
        for row in rows:
            request_id = row['request_id']

            item = {
                'application': '',
                'id': request_id,
                'data': []
            }
            results.append(item)

            if row['amends'] is None:
                item['application'] = 'new'
            else:
                item['application'] = row['amendment_type']  # 'amend'

            item['data'].append({
                'number': row['registration_no'],
                'date': row['date'].strftime('%Y-%m-%d'),
                'class_of_charge': row['class_of_charge'],
                'register_id': row["register_id"]
            })

    logging.debug(results)
    return results


def get_county_by_reg_id(cursor, reg_id):
    sql = "select a.name from county a, register b where b.id=%(reg)s " \
          " and b.county_id = a.id;"
    cursor.execute(sql, {"reg": reg_id})
    row = cursor.fetchone()
    county = row['name']
    return [county]


def get_county(cursor, reg_no, reg_date):
    sql = "select max(reg_sequence_no) as seq_no from register where registration_no=%(reg)s AND date=%(date)s"
    cursor.execute(sql, {"reg": reg_no, "date": reg_date})
    row = cursor.fetchone()
    seq_no = row['seq_no']
    sql = "select a.name from county a, register b where registration_no=%(reg)s AND date=%(date)s " \
          " and reg_sequence_no=%(seq_no)s and b.county_id = a.id;"
    cursor.execute(sql, {"reg": reg_no, "date": reg_date, "seq_no": seq_no})
    row = cursor.fetchone()
    county = row['name']
    logging.debug("county for %s - %s is %s", reg_no, reg_date, county)
    return [county]


def get_applicant_detl(cursor, request_id):
    applicant = {}
    sql = "select customer_name, customer_address, customer_addr_type from request where id =%(request_id)s "
    cursor.execute(sql, {"request_id": request_id})
    row = cursor.fetchone()
    if 'customer_name' in row:
        applicant["customer_name"] = row["customer_name"]
    if 'customer_address' in row:
        applicant["customer_address"] = row["customer_address"]
    if 'customer_addr_type' in row:
        applicant["customer_addr_type"] = row["customer_addr_type"]
    return applicant


