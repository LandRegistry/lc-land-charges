import logging
import datetime
import json
import re


# TODO: the banks searches don't just search banks (needs more filtering)
def search_by_name(cursor, full_name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE UPPER(n.searchable_string) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id "
                   "  AND r.details_id = rd.id "
                   "  AND rd.cancelled_by is null"
                   "  AND rd.class_of_charge in ('PA(B)', 'WO(B)', 'PA', 'WO', 'DA')",
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
                       "Where UPPER(pn.searchable_string)=%(name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and (extract(year from rd.registration_date) between %(from_date)s and %(to_date)s " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'name': full_name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, " +
                       "detl_county_rel dcr, county c, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and rd.id=dcr.details_id " +
                       "and dcr.county_id=c.id " +
                       "and ((UPPER(c.name) = ANY(%(counties)s) "
                       "    and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s) " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'name': full_name.upper(), 'from_date': year_from, 'to_date': year_to,
                           'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_by_company(cursor, name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE UPPER(n.searchable_string) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id "
                   "  AND r.details_id = rd.id "
                   "  AND rd.cancelled_by is null"
                   "  AND rd.class_of_charge in ('PA(B)', 'WO(B)', 'PA', 'WO', 'DA')",
                   {
                       'name': name.upper()
                   })
    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_full_by_company(cursor, name, counties, year_from, year_to):
    if counties[0] == 'ALL':
        logging.info("all counties search")
        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(company_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and (extract(year from rd.registration_date) between %(from_date)s and %(to_date)s " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'company_name': name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, " +
                       "detl_county_rel dcr, county c, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(company_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and rd.id=dcr.details_id " +
                       "and dcr.county_id=c.id " +
                       "and ((UPPER(c.name) = ANY(%(counties)s) "
                       "    and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s) " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'company_name': name.upper(), 'from_date': year_from, 'to_date': year_to,
                           'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_by_local_authority(cursor, name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE UPPER(n.searchable_string) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id "
                   "  AND r.details_id = rd.id "
                   "  AND rd.cancelled_by is null"
                   "  AND rd.class_of_charge in ('PA(B)', 'WO(B)', 'PA', 'WO', 'DA')",
                   {
                       'name': name.upper()
                   })
    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_full_by_local_authority(cursor, name, counties, year_from, year_to):
    if counties[0] == 'ALL':
        logging.info("all counties search")
        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(loc_name)s " +
                       "and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and (extract(year from rd.registration_date) between %(from_date)s and %(to_date)s " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'loc_name': name.upper(),
                           'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, " +
                       "detl_county_rel dcr, county c, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(loc_name)s " +
                       "and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and rd.id=dcr.details_id " +
                       "and dcr.county_id=c.id " +
                       "and ((UPPER(c.name) = ANY(%(counties)s) "
                       "    and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s) " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'loc_name': name.upper(),
                           'from_date': year_from, 'to_date': year_to, 'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_by_other_name(cursor, name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE UPPER(n.searchable_string) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id "
                   "  AND r.details_id = rd.id "
                   "  AND rd.cancelled_by is null"
                   "  AND rd.class_of_charge in ('PA(B)', 'WO(B)', 'PA', 'WO', 'DA')",
                   {
                       'name': name.upper()
                   })
    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_full_by_other_name(cursor, name, counties, year_from, year_to):
    if counties[0] == 'ALL':
        logging.info("all counties search")
        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(other_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and (extract(year from rd.registration_date) between %(from_date)s and %(to_date)s " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'other_name': name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, " +
                       "detl_county_rel dcr, county c, register_details rd " +
                       "Where UPPER(pn.searchable_string)=%(other_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and rd.id=dcr.details_id " +
                       "and dcr.county_id=c.id " +
                       "and ((UPPER(c.name) = ANY(%(counties)s) "
                       "    and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s) " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'other_name': name.upper(), 'from_date': year_from, 'to_date': year_to,
                           'counties': uc_counties
                       })

    rows = cursor.fetchall()
    result = [row['id'] for row in rows]
    return result


def search_by_complex_name(cursor, complex_name):
    cursor.execute("SELECT r.id "
                   "FROM party_name n, register r, register_details rd "
                   "WHERE UPPER(n.complex_name) = %(name)s "
                   "  AND r.debtor_reg_name_id = n.id "
                   "  AND r.details_id = rd.id "
                   "  AND rd.cancelled_by is null"
                   "  AND rd.class_of_charge in ('PA(B)', 'WO(B)', 'PA', 'WO', 'DA')",
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
                       "and (extract(year from rd.registration_date) between %(from_date)s and %(to_date)s " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
                       {
                           'complex_name': complex_name.upper(), 'from_date': year_from, 'to_date': year_to
                       })
    else:
        logging.info("not all counties search")
        uc_counties = [c.upper() for c in counties]

        cursor.execute("SELECT DISTINCT(r.id) " +
                       "FROM party_name pn, register r, party_name_rel pnr, party p, " +
                       "detl_county_rel dcr, county c, register_details rd " +
                       "Where UPPER(pn.complex_name)=%(complex_name)s and r.debtor_reg_name_id=pn.id " +
                       "and pnr.party_name_id = pn.id and pnr.party_id=p.id " +
                       "and p.register_detl_id=rd.id " +
                       "and rd.id=dcr.details_id " +
                       "and dcr.county_id=c.id " +
                       "and ((UPPER(c.name) = ANY(%(counties)s) "
                       "    and extract(year from rd.registration_date) between %(from_date)s and %(to_date)s) " +
                       " or rd.class_of_charge in ('PA', 'WO', 'DA')) " +
                       "and rd.cancelled_by is null",
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
    search_type = data['parameters']['search_type']
    counties = data['parameters']['counties']

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
    cursor.execute("INSERT INTO search_details (request_id, search_timestamp, type, counties) "
                   "VALUES ( %(request_id)s, current_timestamp, %(type)s, %(counties)s ) RETURNING id",
                   {
                       'request_id': request_id, 'type': search_type, 'counties': counties
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


def perform_search(cursor, parameters):
    if "counties" not in parameters:
        parameters["counties"] = []

    if len(parameters['counties']) == 0:
        parameters['counties'].append('ALL')

    search_results = []
    if parameters['search_type'] == 'full':
        logging.info('Perform full search')
        for item in parameters['search_items']:
            if item['name_type'] == "Complex":
                build_results = []
                # Do complex name search
                # Search against the variations of the complex name
                for name in item['name']['complex_variations']:
                    comp_results = (search_full_by_complex_name(cursor,
                                                                name['complex_name'],
                                                                parameters['counties'],
                                                                item['year_from'],
                                                                item['year_to']))

                    if len(comp_results) > 0:
                        for ids in comp_results:
                            build_results.append(ids)
                search_results.append({'name_result': build_results, 'name_id': item['name_id']})
            elif item['name_type'] == "Private Individual":
                # Do full search by name
                name_string = "{} {}".format(item['name']['forenames'], item['name']['surname'])
                search_name = get_searchable_string(name_string, ' ', ' ', ' ', ' ')
                search_results.append({'name_result': search_full_by_name(cursor, search_name,
                                                                          parameters['counties'],
                                                                          item['year_from'],
                                                                          item['year_to']),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Company":
                # Do full search by Company
                search_name = get_searchable_string(' ', item['name']['company_name'], ' ', ' ', ' ')
                search_results.append({'name_result': search_full_by_company(cursor,search_name,
                                                                             parameters['counties'],
                                                                             item['year_from'],
                                                                             item['year_to']),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Local Authority":
                # Do full search by Local Authority
                loc_auth = item['name']['local_authority_name']
                loc_area = item['name']['local_authority_area']
                search_name = get_searchable_string(' ', ' ', loc_auth, loc_area, ' ')
                search_results.append({'name_result': search_full_by_local_authority(cursor, search_name,
                                                                                     parameters['counties'],
                                                                                     item['year_from'],
                                                                                     item['year_to']),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Other":
                # Do full search by Other
                search_name = get_searchable_string(' ', ' ', ' ', ' ', item['name']['other_name'])
                search_results.append({'name_result': search_full_by_other_name(cursor, search_name,
                                                                                parameters['counties'],
                                                                                item['year_from'],
                                                                                item['year_to']),
                                       'name_id': item['name_id']})

    else:
        logging.info('Perform bankruptcy search')
        for item in parameters['search_items']:
            if item['name_type'] == "Complex":
                build_results = []
                # Do complex name search
                # Search against the variations of the complex name
                for name in item['name']['complex_variations']:
                    comp_results = (search_by_complex_name(cursor, name['complex_name']))

                    if len(comp_results) > 0:
                        for ids in comp_results:
                            build_results.append(ids)
                search_results.append({'name_result': build_results, 'name_id': item['name_id']})
            elif item['name_type'] == "Private Individual":
                # Do full search by name
                name_string = "{} {}".format(item['name']['forenames'], item['name']['surname'])
                search_name = get_searchable_string(name_string, ' ', ' ', ' ', ' ')
                search_results.append({'name_result': search_by_name(cursor, search_name),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Company":
                # Do full search by Company
                search_name = get_searchable_string(' ', item['name']['company_name'], ' ', ' ', ' ')
                search_results.append({'name_result': search_by_company(cursor, search_name),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Local Authority":
                # Do full search by Local Authority
                loc_auth = item['name']['local_authority_name']
                loc_area = item['name']['local_authority_area']
                search_name = get_searchable_string(' ', ' ', loc_auth, loc_area, ' ')
                search_results.append({'name_result': search_by_local_authority(cursor, search_name),
                                       'name_id': item['name_id']})

            elif item['name_type'] == "Other":
                # Do full search by Other
                search_name = get_searchable_string(' ', ' ', ' ', ' ', item['name']['other_name'])
                search_results.append({'name_result': search_by_other_name(cursor, search_name),
                                       'name_id': item['name_id']})

    return search_results

    
def read_searches(cursor,nonissued):
    # TODO: handle the unprinted/unissued thing
    cursor.execute("SELECT id, request_id, parameters, result FROM search_details")
    # Generate the results here...
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            "result": row['result'],
        })
    return results


def get_searchable_string(name_string=None, company=None, local_auth=None, local_auth_area=None, other=None):
    name = ''
    print('name_string is', name_string)
    if name_string is not None and name_string != ' ':
        print('name string not none', name_string)
        name = get_abbrev_name(name_string)
    elif company is not None and company != ' ':
        print('company not none', company)
        name = get_abbrev_name(company)
    elif local_auth is not None and local_auth != ' ':
        print('local auth not none', local_auth)
        loc_name = get_abbrev_name(local_auth)
        loc_area = get_abbrev_name(local_auth_area)
        name = get_abbrev_name(loc_name + " " + loc_area)
    elif other is not None and other != ' ':
        print('other not none', other)
        name = get_abbrev_name(other)

    searchable_string = re.sub('[^A-Za-z0-9]+', '', name)
    return searchable_string


def get_abbrev_name(name):
    abbrev_list = []
    common_names = [
        'ASS', 'ASSOC', 'ASSOCS', 'ASSOCIATE', 'ASSOCIATED', 'ASSOCIATES', 'ASSOCIATION', 'ASSOCIATIONS',
        'LD', 'PUBLIC LIMITED COMPANY', 'CWMNI CYFYNGEDIG CYHOEDDUS', 'CWMNI CYF CYHOEDDUS', 'LTD', 'LIMITED',
        'CYFYNGEDIG', 'CYF', 'CCC', 'C C C', 'PLC', 'P L C',
        'SOC', 'SOCS', 'SOCY', 'SOCYS', 'SOCIETY', 'SOCIETYS', 'SOCIETIES',
        'ST', 'STREET', 'SAINT',
        'CO', 'COS', 'COY', 'COMP', 'COYS', 'COMPS', 'COMPANY', 'COMPANIES',
        'DR', 'DOC', 'DOCTOR',
        'BRO', 'BROS', 'BROTHER', 'BROTHERS',
        '&', 'AND',
        'BROKERS', 'BUILDERS', 'COLLEGES', 'COMMISSIONERS', 'CONSTRUCTIONS', 'CONTRACTORS', 'DECORATORS',
        'DEVELOPERS', 'DEVELOPMENTS',
        'ENTERPRISES', 'ESTATES', 'GARAGES', 'HOLDINGS', 'HOTELS', 'INVESTMENTS', 'MOTORS', 'PRODUCTIONS',
        'SCHOOLS', 'SONS', 'STORES', 'TRUSTS', 'WARDENS', 'CHARITIES', 'PROPERTIES', 'INDUSTRIES'
    ]

    replace_names = [
        'ASS', 'ASS', 'ASS', 'ASS', 'ASS', 'ASS', 'ASS', 'ASS',
        'LD', 'LD', 'LD', 'LD', 'LD', 'LD',
        'LD', 'LD', 'LD', 'LD', 'LD', 'LD',
        'SOC', 'SOC', 'SOC', 'SOC', 'SOC', 'SOC', 'SOC',
        'ST', 'ST', 'ST',
        'CO', 'CO', 'CO', 'CO', 'CO', 'CO', 'CO', 'CO',
        'DR', 'DR', 'DR',
        'BRO', 'BRO', 'BRO', 'BRO',
        'AND', 'AND',
        'BROKER', 'BUILDER', 'COLLEGE', 'COMMISSIONER', 'CONSTRUCTION', 'CONTRACTOR', 'DECORATOR',
        'DEVELOPER', 'DEVELOPMENT',
        'ENTERPRISE', 'ESTATE', 'GARAGE', 'HOLDING', 'HOTEL', 'INVESTMENT', 'MOTOR', 'PRODUCTION',
        'SCHOOL', 'SON', 'STORE', 'TRUST', 'WARDEN', 'CHARITY', 'PROPERTY', 'INDUSTRY'
    ]

    problem_names = [
        'PUBLIC LIMITED COMPANY', 'CWMNI CYFYNGEDIG CYHOEDDUS', 'CWMNI CYF CYHOEDDUS', 'C C C', 'P L C'
    ]

    name = name.upper()
    for names in problem_names:
        if names in name:
            name = name.replace(names, 'LD')

    print('this is the name', name)
    for word in name.split():
        print('this is the word', word)
        if word in common_names:
            x = common_names.index(word)
            print(x)
            curr_name = replace_names[x]
            abbrev_list.append(curr_name)
        else:
            abbrev_list.append(word)

    abbrev_name = "".join(abbrev_list)
    print('this is the abbrev name', abbrev_name)
    return abbrev_name