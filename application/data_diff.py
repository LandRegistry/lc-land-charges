import logging


def names_match(a, b):
    if a['type'] != b['type']:
        return False

    # TODO: Consider case sensitivity implications
    if a['type'] in ['County Council', 'Parish Council', 'Rural Council', 'Other Council']:
        return a['local']['area'] == b['local']['area'] and a['local']['name'] == b['local']['name']
    elif a['type'] in ['Development Corporation', 'Other']:
        return a['other'] == b['other']
    elif a['type'] == 'Limited Company':
        return a['company'] == b['company']
    elif a['type'] == 'Complex Name':
        return a['complex']['name'] == b['complex']['name'] and a['complex']['number'] == a['complex']['number']
    elif a['type'] == 'Private Individual':
        if len(a['private']['forenames']) != len(b['private']['forenames']):
            return False

        if a['private']['surname'] != b['private']['surname']:
            return False

        return ' '.join(a['private']['forenames']) == ' '.join(b['private']['forenames'])

    else:
        raise RuntimeError("Unknown name type: {}".format(a['type']))


def is_name_change_type3(before, after):

    if len(before['forenames']) == 0 and len(after['forenames']) > 0 and \
            before['surname'] == after['surname']:
        # Forenames have been added to surname-only name
        return True

    if len(before['forenames']) == len(after['forenames']):
        for index, name in enumerate(before['forenames']):
            # if any name is other than X => XXXXX, return False

            after_name = after['forenames'][index]
            if len(name) > 1:  # Before is not initial
                return False

            if len(name) == 1 and len(after_name) == 1:  # Initial remains as initial
                return False

            if name[0].upper() != after_name[0].upper():  # Before is not the initial of after
                return False
    else:
        if len(before['forenames']) == 0:
            return True
        else:
            return False

    return True


def is_county_added(before, after):
    if len(before) >= len(after):
        return False

    return set(before).issubset(set(after))


def arrays_match(before, after):
    return set(before) == set(after)


def get_rectification_type(original_data, new_data):
    # There are three types of rectification, depending on what's been changed. The rules
    # are odd, but set out, so we can determine this automatically.
    # Type 1: change of details not effecting search results
    # Type 2: change of details effecting search results where both old and new must be revealed
    # Type 3: change of details effecting search results where only the new must be revealed
    # Note: type 1 and 3 have the same effect under the hood, so we only need to determine 2 from 1/3
    # But: we'll distinguish 1 from 3 in case there's some significance later on
    logging.debug(original_data)
    logging.debug(new_data)

    # {'amended_by': {'number': 1000, 'date': '2016-02-08 00:00:00', 'type': None}, 'registration':
    # {'number': 1003, 'date': '2014-08-01'}, 'particulars': {'description': '1 The Lane, Some Village',
    # 'district': 'South Hams', 'counties': ['Devon']}, 'class_of_charge': 'C1', 'status': 'superseded',
    # 'parties': [{'names': [{'private': {'forenames': ['Jo', 'John'], 'surname': 'Johnson'}, 'type':
    # 'Private Individual'}], 'type': 'Estate Owner'}]}

    # {'class_of_charge': 'C1', 'applicant': {'address': "Bob's address", 'reference': 'abc123',
    # 'key_number': '1123456', 'name': 'Bob the Applicant'}, 'update_registration': {'type': 'Rectification'},
    # 'parties': [{'names': [{'private': {'forenames': ['Jo', 'John'], 'surname': 'Johnson'}, 'type':
    # 'Private Individual'}], 'type': 'Estate Owner'}], 'particulars': {'description': '1 The Lane, Some Village',
    # 'district': 'South Hams', 'counties': ['Devon']}}

    is_amend = False
    if 'update_registration' in new_data:  # case of 'new_data' being incoming update data
        is_amend = new_data['update_registration']['type'] == 'Amendment'

    if 'amends_registration' in new_data:  # case of comparing data items at rest
        is_amend = new_data['amends_registration']['type'] == 'Amendment'

    if is_amend:  # new_data['update_registration']['type'] == 'Amendment':
        # loop through the names in original and new and then compare
        new_names = []
        for names in new_data['parties'][0]['names']:
            forenames = names['private']['forenames']
            surname = names['private']['surname']
            new_names.append({'forenames': forenames, 'surname': surname})

        # orig_names = []
        for names in original_data['parties'][0]['names']:
            forenames = names['private']['forenames']
            surname = names['private']['surname']
            orig_names = {'forenames': forenames, 'surname': surname}
            if orig_names not in new_names:
                return 2

        # if ((len(orig_names) == len(new_names)) and
        #        (all(i in new_names for i in orig_names))):
        #    return 1
        # else:
        #    return 2

        return 1

    names_are_the_same = names_match(original_data['parties'][0]['names'][0],
                                     new_data['parties'][0]['names'][0])

    # TODO: we assume type-3 only possible for Private Individuals here... this is being checked
    if not names_are_the_same:
        if new_data['parties'][0]['names'][0]['type'] == 'Private Individual':
            if is_name_change_type3(original_data['parties'][0]['names'][0]['private'],
                                    new_data['parties'][0]['names'][0]['private']):
                return 3
        return 2

    # Name hasn't been changed
    if is_county_added(original_data['particulars']['counties'], new_data['particulars']['counties']):
        return 2

    if not arrays_match(original_data['particulars']['counties'], new_data['particulars']['counties']):
        return 3

    if original_data['class_of_charge'] != new_data['class_of_charge']:
        return 3

    # At this point we know: class_of_charge, name and counties are all unchanged
    # Therefore:
    return 1
