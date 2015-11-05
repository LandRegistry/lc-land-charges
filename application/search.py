import logging
import datetime
import json


# TODO: the banks searches don't just search banks (needs more filtering)
def search_by_name(cursor, full_name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r "
                   "WHERE UPPER(n.party_name) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id",
                   {
                       'name': full_name.upper()
                   })
    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_full_by_name(cursor, full_name, counties, year_from, year_to):
    if counties[0] == 'ALL':
        logging.info("all counties search")
        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd " +
                       "Where UPPER(pn.party_name)=%(fullname)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s",
                       {
                           'fullname': full_name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, party_address pa, address a, " +
                       "address_detail ad, register_details rd " +
                       "Where UPPER(pn.party_name)=%(fullname)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id and p.id=pa.party_id " +
                       "and pa.address_id=a.id and a.detail_id=ad.id " +
                       # "and UPPER(ad.county) IN ('" + "', '".join((str(n) for n in counties)) + "') " +
                       "and UPPER(ad.county) = ANY(%(counties)s) "
                       "and p.register_detl_id=rd.id " +
                       "and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s",
                       {
                           'fullname': full_name.upper(), 'from_date': year_from, 'to_date': year_to,
                           'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_by_complex_name(cursor, complex_name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r "
                   "WHERE UPPER(n.complex_name) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id",
                   {
                       'name': complex_name.upper()
                   })
    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_full_by_complex_name(cursor, complex_name, counties, year_from, year_to):
    if counties[0] == 'ALL':
        logging.info("all counties search")
        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd " +
                       "Where UPPER(pn.complex_name)=%(complex_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s",
                       {
                           'complex_name': complex_name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, party_address pa, address a, " +
                       "address_detail ad, register_details rd " +
                       "Where UPPER(pn.complex_name)=%(complex_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id and p.id=pa.party_id " +
                       "and pa.address_id=a.id and a.detail_id=ad.id " +
                       # "and UPPER(ad.county) IN ('" + "', '".join((str(n) for n in counties)) + "') " +
                       "and UPPER(ad.county) = ANY(%(counties)s) "
                       "and p.register_detl_id=rd.id " +
                       "and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s",
                       {
                           'complex_name': complex_name.upper(), 'from_date': year_from, 'to_date': year_to,
                           'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def store_search_request(cursor, data):
    # row on request
    reference = data['customer']['reference']
    key_number = data['customer']['key_number']
    cust_name = data['customer']['name']
    cust_address = data['customer']['address']
    date = datetime.datetime.now()
    ins_request_id = None
    document = data['document_id']

    cursor.execute("INSERT INTO request (key_number, application_type, application_reference, application_date, " +
                   "ins_request_id, document_ref, customer_name, customer_address) " +
                   "VALUES ( %(key)s, %(app_type)s, %(app_ref)s, %(app_date)s, %(ins_id)s, %(doc)s, "
                   " %(name)s, %(addr)s ) RETURNING id",
                   {
                       "key": key_number, "app_type": "SEARCH", "app_ref": reference,
                       "app_date": date, "ins_id": ins_request_id, "doc": document,
                       "name": cust_name, "addr": cust_address
                   })
    request_id = cursor.fetchone()[0]

    # Row on search details
    cursor.execute("INSERT INTO search_details (request_id, parameters) "
                   "VALUES ( %(request_id)s, %(params)s )",
                   {
                       'request_id': request_id, 'params': json.dumps(data['parameters'])
                   })

    return request_id


def store_search_result(cursor, search_request_id, data):

    # Row on search details
    cursor.execute("UPDATE search_details "
                   "SET result=%(result)s "
                   "WHERE request_id=%(request_id)s;",
                   {
                       'request_id': search_request_id, 'result': json.dumps(data)
                   })


def perform_search(cursor, parameters):
    if len(parameters['counties']) == 0:
        parameters['counties'].append('ALL')

    print("search parameters : " + str(parameters))
    search_results = []
    if parameters['search_type'] == 'full':
        logging.info('Perform full search')
        for item in parameters['search_items']:
            if 'complex_no' in item:
                # Do complex name search
                search_results.append({item['name']: search_full_by_complex_name(cursor, item['name'],
                                                                                 parameters['counties'],
                                                                                 item['year_from'],
                                                                                 item['year_to'])})
            else:
                # Do full search by name
                search_results.append({item['name']: search_full_by_name(cursor, item['name'],
                                                                         parameters['counties'],
                                                                         item['year_from'],
                                                                         item['year_to'])})
    else:
        logging.info('Perform bankruptcy search')
        for item in parameters['search_items']:
            if 'complex_no' in item:
                # Do complex name search
                search_results.append({item['name']: search_by_complex_name(cursor, item['name'])})
            else:
                # Do search by name
                search_results.append({item['name']: search_by_name(cursor, item['name'])})

    return search_results
