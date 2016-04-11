import logging
import datetime
import json
import time
from application.search_key import create_search_keys


def load_county_dictionary(cursor):
    cursor.execute('SELECT name, welsh_name FROM county WHERE welsh_name is not NULL');
    rows = cursor.fetchall()

    welsh_dict = {}
    for row in rows:
        welsh_dict[row['welsh_name'].upper()] = row['name'].upper()
    return welsh_dict


def store_search_request(cursor, data):
    # row on request
    logging.debug(data)

    username = ''
    if 'user_id' in data:
        username = data['user_id']

    reference = data['customer']['reference']
    key_number = data['customer']['key_number']
    cust_name = data['customer']['name']
    cust_address = data['customer']['address']
    cust_address_type = data['customer']['address_type']
    date = datetime.datetime.now()
    ins_request_id = None
    # document = data['document_id']
    search_type = data['parameters']['search_type']
    counties = []
    if 'counties' in data['parameters']:
        counties = data['parameters']['counties']

    app_time = datetime.datetime.now().strftime('%H:%M:%S')
    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, application_time, " +
                   "ins_request_id, customer_name, customer_address, customer_addr_type, caseworker_uid) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(app_time)s, %(ins_id)s, "
                   " %(name)s, %(addr)s , %(addr_type)s, %(cwuid)s ) RETURNING id",
                   {
                       "key": key_number, "app_type": "SEARCH", "app_ref": reference,
                       "app_date": date, "app_time": app_time, "ins_id": ins_request_id,
                       "name": cust_name, "addr": cust_address, "addr_type": cust_address_type,
                       'cwuid': username
                   })
    request_id = cursor.fetchone()[0]

    # Row on search details
    cursor.execute("INSERT INTO search_details (request_id, search_timestamp, type, counties, certificate_date,"
                   " expiry_date, certificate_no) "
                   "VALUES ( %(request_id)s, current_timestamp, %(type)s, %(counties)s, %(cdate)s, %(edate)s, "
                   "%(cert_no)s ) RETURNING id",
                   {
                       'request_id': request_id, 'type': search_type, 'counties': json.dumps(counties),
                       'cdate': data['search_date'], 'edate': data['expiry_date'], 'cert_no': data['cert_no']
                   })
    details_id = cursor.fetchone()[0]

    for count, item in enumerate(data['parameters']['search_items']):
        name_type = item['name_type']
        forenames = item['name']['forenames'] if 'forenames' in item['name'] else None
        surname = item['name']['surname'] if 'surname' in item['name'] else None
        complex_name = item['name']['complex_name'] if 'complex_name' in item['name'] else None
        complex_number = item['name']['complex_number'] if 'complex_number' in item['name'] else None
        company = item['name']['company_name'] if 'company_name' in item['name'] else None
        local_auth_name = item['name']['local_authority_name'] if 'local_authority_name' in item['name'] else None
        local_auth_area = item['name']['local_authority_area'] if 'local_authority_area' in item['name'] else None
        other = item['name']['other_name'] if 'other_name' in item['name'] else None
        year_from = item['year_from'] if 'year_from' in item else None
        year_to = item['year_to'] if 'year_to' in item else None

        cursor.execute("INSERT INTO search_name (details_id, name_type, forenames, surname, " +
                       "complex_name, complex_number, company_name, local_authority_name, local_authority_area, " +
                       "other_name, year_from, year_to) "
                       "VALUES ( %(details_id)s, %(name_type)s, %(forenames)s, %(surname)s, " +
                       "%(complex_name)s, %(complex_number)s, %(company)s, %(loc_auth_name)s, " +
                       "%(loc_auth_number)s, %(other)s, %(year_from)s, %(year_to)s ) RETURNING id",
                       {
                           'details_id': details_id, 'name_type': name_type, 'forenames': forenames,
                           'surname': surname, 'complex_name': complex_name, 'complex_number': complex_number,
                           'company': company, 'loc_auth_name': local_auth_name, 'loc_auth_number': local_auth_area,
                           'other': other, 'year_from': year_from, 'year_to': year_to
                       })
        search_name_id = cursor.fetchone()[0]
        data['parameters']['search_items'][count]['name_id'] = search_name_id
    return request_id, details_id, data


def store_search_result(cursor, request_id, details_id, name_id, data):

    # Row on search details
    cursor.execute("INSERT INTO search_results (request_id, search_details_id, name_id, result)"
                   "VALUES ( %(request_id)s, %(details_id)s, %(name_id)s, %(result)s ) ",
                   {
                       'request_id': request_id, 'details_id': details_id, 'name_id': name_id,
                       'result': json.dumps(data)
                   })


# search banks
# search full - all counties
# search full - limited counties
def merge_lists(a, b):
    result = a + [x for x in b if x not in a]
    return result


def perform_bankruptcy_search(cursor, name_type, keys, cert_date):
    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name n, register r, register_details rd, party p, party_name_rel pnr "
                   "WHERE n.searchable_string = ANY(%(keys)s) "
                   "  AND n.id = pnr.party_name_id "
                   "  AND pnr.party_id = p.id "
                   "  and p.party_type != 'Court' "
                   "  AND p.register_detl_id = rd.id "
                   "  AND r.details_id = rd.id "
                   "  AND r.date <= %(date)s "
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on) "
                   "  AND rd.class_of_charge in ('PAB', 'WOB', 'PA', 'WO', 'DA') "
                   "  AND n.name_type_ind = %(nametype)s", {
                       "keys": keys, "date": cert_date, "nametype": name_type
                   })
    rows = cursor.fetchall()
    result = [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]
    return result


def perform_bankruptcy_search_complex_name(cursor, name_type, keys, number, cert_date):
    # use perform_bankruptcy_search
    # use SQL on number
    # merge results
    name_results = perform_bankruptcy_search(cursor, name_type, keys, cert_date)

    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE n.complex_number = %(number)s "
                   "  AND n.id = pnr.party_name_id "
                   "  AND pnr.party_id = p.id "
                   "  and p.party_type != 'Court' "
                   "  AND p.register_detl_id = rd.id "
                   "  AND r.details_id = rd.id "
                   "  AND r.date <= %(date)s"
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on)"
                   #"  AND r.reveal='t'"
                   "  AND rd.class_of_charge in ('PAB', 'WOB', 'PA', 'WO', 'DA') "
                   "  AND n.name_type_ind = 'Complex Name' ", {
                       "number": number, "date": cert_date, "nametype": name_type
                   })
    rows = cursor.fetchall()
    result = [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]
    return merge_lists(name_results, result)


def perform_full_search_all_counties(cursor, name_type, keys, year_from, year_to, cert_date):
    logging.debug('Full search: %s %s', name_type, keys[0])
    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd "
                   "WHERE pn.searchable_string = ANY(%(keys)s) "
                   "  and pnr.party_name_id = pn.id and pnr.party_id=p.id "
                   "  and p.party_type != 'Court' "
                   "  and p.register_detl_id=rd.id "
                   "  and rd.id=r.details_id "
                   #"  and pn.name_type_ind = %(nametype)s "
                   "  and (r.debtor_reg_name_id is null or r.debtor_reg_name_id = pn.id) "
                   "  and ("
                   "      rd.priority_notice_ind='f' "
                   "      or rd.priority_notice_ind IS NULL "
                   "      or (priority_notice_ind='y' and rd.prio_notice_expires >= %(exdate)s) "
                   "  )"
                   "  and ( "
                   "     extract(year from r.date) between %(from_date)s and %(to_date)s "
                   "     or rd.class_of_charge in ('PA', 'WO', 'DA', 'PAB', 'WOB')"
                   "  ) "
                   "  and r.date <= %(date)s "
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on)",
                   #"   and r.reveal='t'",
                   {
                       'keys': keys, 'from_date': year_from, 'to_date': year_to,
                       'date': cert_date, 'exdate': cert_date, 'nametype': name_type
                   })
    rows = cursor.fetchall()
    logging.debug("%d rows returned", len(rows))
    return [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]


def perform_full_search(cursor, name_type, keys, counties, year_from, year_to, cert_date):
    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd "
                   "FULL OUTER JOIN detl_county_rel dcr on rd.id = dcr.details_id "
                   "FULL OUTER JOIN county c on dcr.county_id = c.id "
                   "WHERE pn.searchable_string= ANY(%(keys)s) "
                   "  and pnr.party_name_id = pn.id and pnr.party_id=p.id "
                   "  and p.party_type != 'Court' "
                   "  and p.register_detl_id=rd.id "
                   "  and rd.id=r.details_id "
                   #"  and pn.name_type_ind = %(nametype)s "
                   "  and (r.debtor_reg_name_id is null or r.debtor_reg_name_id = pn.id) "
                   "  and ("
                   "      rd.priority_notice_ind='f' "
                   "      or rd.priority_notice_ind IS NULL "
                   "      or (priority_notice_ind='y' and rd.prio_notice_expires >= %(exdate)s) "
                   "  )"
                   "  AND ("
                   "      rd.class_of_charge in ('PA', 'WO', 'DA', 'PAB', 'WOB' ) "
                   "      OR ( "
                   "          extract(year from r.date) between %(from_date)s and %(to_date)s "
                   "          AND ( "
                   "              rd.class_of_charge = 'A' "
                   "              OR UPPER(c.name) = ANY(%(counties)s) "
                   "              OR c.name IS NULL"
                   "          ) "
                   "      ) "
                   "  ) "
                   " and r.date <= %(date)s "
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on)",
                   #" and r.reveal='t'",
                   {
                       'keys': keys, 'from_date': year_from, 'to_date': year_to,
                       'counties': counties, 'date': cert_date, 'exdate': cert_date,
                       'nametype': name_type
                   })
    rows = cursor.fetchall()
    return [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]


def perform_full_search_complex_name_all_counties(cursor, name_type, keys, number, year_from, year_to, cert_date):
    name_results = perform_full_search_all_counties(cursor, name_type, keys, year_from, year_to, cert_date)
    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd "
                   "WHERE pn.complex_number = %(number)s "
                   "  and pnr.party_name_id = pn.id and pnr.party_id=p.id "
                   "  and p.party_type != 'Court' "
                   "  and p.register_detl_id=rd.id "
                   "  and rd.id=r.details_id "
                   #"  and pn.name_type_ind = 'Complex Name' "
                   "  and (r.debtor_reg_name_id is null or r.debtor_reg_name_id = pn.id) "
                   "  and ("
                   "      rd.priority_notice_ind='f' "
                   "      or rd.priority_notice_ind IS NULL "
                   "      or (priority_notice_ind='y' and rd.prio_notice_expires >= %(exdate)s) "
                   "  )"
                   "  and ( "
                   "     extract(year from r.date) between %(from_date)s and %(to_date)s "
                   "     or rd.class_of_charge in ('PA', 'WO', 'DA', 'PAB', 'WOB')"
                   "  ) "
                   "  and r.date <= %(date)s "
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on)",
                   #"  and r.reveal='t'",
                   {
                       'number': number, 'from_date': year_from, 'to_date': year_to,
                       'date': cert_date, 'exdate': cert_date, 'nametype': name_type
                   })
    rows = cursor.fetchall()
    result = [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]
    return merge_lists(name_results, result)


def perform_full_search_complex_name(cursor, name_type, keys, number, counties, year_from, year_to, cert_date):
    name_results = perform_full_search(cursor, name_type, keys, counties, year_from, year_to, cert_date)
    cursor.execute("SELECT r.id, r.date, rd.class_of_charge "
                   "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd "
                   "FULL OUTER JOIN detl_county_rel dcr on rd.id = dcr.details_id "
                   "FULL OUTER JOIN county c on dcr.county_id = c.id "
                   "WHERE pn.complex_number = %(number)s "
                   "  and pnr.party_name_id = pn.id and pnr.party_id=p.id "
                   "  and p.register_detl_id=rd.id "
                   "  and rd.id=r.details_id "
                   "  and pn.name_type_ind = %(nametype)s "
                   "  and (r.debtor_reg_name_id is null or r.debtor_reg_name_id = pn.id) "
                   "  and ("
                   "      rd.priority_notice_ind='f' "
                   "      or rd.priority_notice_ind IS NULL "
                   "      or (priority_notice_ind='y' and rd.prio_notice_expires >= %(exdate)s) "
                   "  )"
                   "  AND ("
                   "      rd.class_of_charge in ('PA', 'WO', 'DA', 'PAB', 'WOB' ) "
                   "      OR ( "
                   "          extract(year from r.date) between %(from_date)s and %(to_date)s "
                   "          AND ( "
                   "              rd.class_of_charge = 'A' "
                   "              OR UPPER(c.name) = ANY(%(counties)s) "
                   "              OR c.name IS NULL"
                   "          ) "
                   "      ) "
                   "  ) "
                   "and r.date <= %(date)s "
                   "  AND (r.expired_on is NULL OR %(date)s < r.expired_on)",
                   #"and r.reveal='t'",
                   {
                       'number': number, 'from_date': year_from, 'to_date': year_to,
                       'counties': counties, 'date': cert_date, 'exdate': cert_date,
                       'nametype': name_type
                   })
    rows = cursor.fetchall()
    result = [{"id": row['id'], "date": row['date'], "class": row['class_of_charge']} for row in rows]
    return merge_lists(name_results, result)


def process_search_result(result):
    res = []
    for item in result:
        res.append(item['id'])
    return res


def perform_search(cursor, parameters, cert_date):
    welsh = load_county_dictionary(cursor)

    if "counties" not in parameters:
        parameters["counties"] = []

    if len(parameters['counties']) == 0:
        parameters['counties'].append('ALL')

    search_results = []

    counties = []
    # Capitalise and substitute English names for Welsh counties
    for c in parameters['counties']:
        cu = c.upper()
        if cu in welsh:
            logging.debug("%s is welsh", c)
            counties.append(welsh[cu])
        else:
            logging.debug("%s is english", c)
            counties.append(cu)

    for item in parameters['search_items']:
        keys = create_search_keys(cursor, item['name_type'], item['name'])
        logging.debug('Search keys:')
        logging.debug(keys)

        if item['name_type'] == 'Complex Name':
            cnumber = item['name']['complex_number']

            if parameters['search_type'] == 'full':
                if parameters['counties'][0] == 'ALL':
                    name_result = perform_full_search_complex_name_all_counties(cursor, item['name_type'], keys, cnumber, item['year_from'], item['year_to'], cert_date)
                else:
                    name_result = perform_full_search_complex_name(cursor, item['name_type'], keys, cnumber, counties, item['year_from'], item['year_to'], cert_date)
            else:
                name_result = perform_bankruptcy_search_complex_name(cursor, item['name_type'], keys, cnumber, cert_date)
        else:
            if parameters['search_type'] == 'full':
                if parameters['counties'][0] == 'ALL':
                    name_result = perform_full_search_all_counties(cursor, item['name_type'], keys, item['year_from'], item['year_to'], cert_date)
                else:
                    name_result = perform_full_search(cursor, item['name_type'], keys, counties, item['year_from'], item['year_to'], cert_date)
            else:
                name_result = perform_bankruptcy_search(cursor, item['name_type'], keys, cert_date)

        search_results.append({'name_result': process_search_result(name_result), 'name_id': item['name_id']})
    # search_results.append({'name_result': results_array, 'name_id': item['name_id']})

    return search_results


def get_search_by_request_id(cursor, id):
    cursor.execute("SELECT sr.result " +
                   "FROM search_results r "
                   "where r.request_id = %(id)s", {'id': id})

    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            "result": row['result'],
        })
    return results


def read_searches(cursor, name):
    cursor.execute("SELECT sr.result " +
                   "FROM search_name sn, search_results sr " +
                   "WHERE (UPPER(sn.forenames||' '||sn.surname)=%(name)s " +
                   " or UPPER(sn.complex_name)=%(name)s " +
                   " or UPPER(sn.company_name)=%(name)s " +
                   " or UPPER(sn.local_authority_name)=%(name)s " +
                   " or UPPER(sn.other_name)=%(name)s) " +
                   "and sn.id=sr.name_id",
                   {
                       'name': name.upper()
                   })
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            "result": row['result'],
        })
    return results


def get_search_ids_by_date(cursor, date):
    cursor.execute("SELECT id, request_id " +
                   "FROM search_details " +
                   "WHERE date(search_timestamp)=%(date)s",
                   {
                       'date': date
                   })
    rows = cursor.fetchall()
    results = []
    if len(rows) > 0:
        for row in rows:
            results.append({
                "search_id": row['id'],
                "request_id": row['request_id']
            })
    else:
        results = None
    return results
