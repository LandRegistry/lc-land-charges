from jsonschema import Draft4Validator


DATE_SCHEMA = {
    "type": "string",
    "pattern": "^([0-9]{4}-[0-9]{2}-[0-9]{2})$"
}


PRIVATE_INDIVIDUAL_SCHEMA = {
    "type": "object",
    "properties": {
        "forenames": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "surname": {"type": "string"}
    },
    "required": ["forenames", "surname"],
    "additionalProperties": False
}

AUTHORITY_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "area": {"type": "string"}
    },
    "required": ["name", "area"],
    "additionalProperties": False
}

COMPLEX_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "number": {"type": "integer"}
    },
    "required": ["name", "number"],
    "additionalProperties": False
}


NAME_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "Private Individual",
                "County Council",
                "Parish Council",
                "Rural Council",
                "Other Council",
                "Development Corporation",
                "Limited Company",
                "Complex Name",
                "Other"
            ]
        },
        "private": PRIVATE_INDIVIDUAL_SCHEMA,
        "local": AUTHORITY_SCHEMA,
        "other": {"type": "string"},
        "company": {"type": "string"},
        "complex": COMPLEX_SCHEMA
    },
    "required": ["type"],
    "oneOf": [
        {"required": ["private"]},
        {"required": ["local"]},
        {"required": ["company"]},
        {"required": ["other"]},
        {"required": ["complex"]}
    ],
    "additionalProperties": False
}


ADDRESS_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["Residence", "Business", "Investment"]
        },
        "address_lines": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "county": {"type": "string"},
        "postcode": {"type": "string"},
        "address_string": {"type": "string"}
    },
    "required": ["type", "address_lines", "postcode", "county"],
    "additionalProperties": False
}


MIGRATED_ADDRESS_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["Residence", "Business", "Investment"]
        },
        "address_string": {"type": "string"}
    },
    "required": ["type", "address_string"],
    "additionalProperties": False
}


MIGRATED_PARTY_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "Debtor",
                "Estate Owner",
                "Court"
            ]
        },
        "names": {
            "type": "array",
            "items": NAME_SCHEMA
        },
        "addresses": {
            "type": "array",
            "items": MIGRATED_ADDRESS_SCHEMA,
        },
        "occupation": {"type": "string"},
        "trading_name": {"type": "string"},
        "residence_withheld": {"type": "boolean"},
        "case_reference": {"type": "string"},
        "date_of_birth": DATE_SCHEMA
    },
    "required": ["type", "names"],
    "additionalProperties": False
}


PARTY_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "Debtor",
                "Estate Owner",
                "Court"
            ]
        },
        "names": {
            "type": "array",
            "items": NAME_SCHEMA
        },
        "addresses": {
            "type": "array",
            "items": ADDRESS_SCHEMA,
        },
        "occupation": {"type": "string"},
        "trading_name": {"type": "string"},
        "residence_withheld": {"type": "boolean"},
        "case_reference": {"type": "string"},
        "date_of_birth": DATE_SCHEMA
    },
    "required": ["type", "names"],
    "additionalProperties": True
}

PARTICULARS_SCHEMA = {
    "type": "object",
    "properties": {
        "counties": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "district": {"type": "string"},
        "description": {"type": "string"},
        "priority_notice": {"type": "string"}  # This is a reference to a priority notice
    },
    "required": ["counties", "district", "description"],
    "additionalProperties": False
}

MIGRATED_PARTICULARS_SCHEMA = {
    "type": "object",
    "properties": {
        "counties": {
            "type": "array",
            "items": {"type": "string"}
        },
        "district": {"type": "string"},
        "description": {"type": "string"}
    },
    "required": ["counties", "district", "description"],
    "additionalProperties": False
}

DEBTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "occupation": {"type": "string"},
        "trading_name": {"type": "string"},
        "residence_withheld": {"type": "boolean"},
        "legal_reference": {"type": "string"},
        "date_of_birth": DATE_SCHEMA

    },
    "required": [
        "occupation", "trading_name", "residence_withheld", "legal_reference"
    ],
    "additionalProperties": False
}

APPLICANT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": {"type": "string"},
        "key_number": {
            "type": "string",
            "pattern": "(^\d{3,7}$)|(^$)"
        },
        "reference": {
            "type": "string"
        }
    },
    "required": [
        "name", "address", "key_number", "reference"
    ],
    "additionalProperties": False
}


UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ['Rectification', 'Correction', 'Amendment']
        }
    },
    "required": [
        "type"
    ],
    "additionalProperties": False
}

REGISTRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "update_registration": UPDATE_SCHEMA,
        "parties": {
            "type": "array",
            "items": PARTY_SCHEMA
        },
        "class_of_charge": {
            "type": "string",
            "enum": ["C1", "C2", "C3", "C4", "D1", "D2", "D3", "A", "B", "E", "F", "PA", "WO", "DA",
                     "ANN", "LC", "PAB", "WOB"]
        },
        "particulars": PARTICULARS_SCHEMA,
        "applicant": APPLICANT_SCHEMA,
        "additional_information": {
            "type": "string"
        },
        "priority_notice": {  # This means that the registration is a priority notice
            "type": "object",
            "properties": {
                "expires": DATE_SCHEMA
            }
        },
        "original_request": {"type": "string"}
    },
    "required": [
        "parties", "class_of_charge", "applicant"
    ],
    "additionalProperties": False
}

MIGRATED_REGISTRATION_ITEM = {
    "type": "object",
    "properties": {
        "registration": {
            "type": "object",
            "properties": {
                "registration_no": {"type": "string"},
                "date": DATE_SCHEMA            
            }
        },
        "parties": {
            "type": "array",
            "items": MIGRATED_PARTY_SCHEMA
        },
        "type": {
            "type": "string",
            "enum": ["NR", "AM", "CN", "CP", "RN", "PN", "RC"]
        },
        "class_of_charge": {
            "type": "string",
            "enum": ["C1", "C2", "C3", "C4", "D1", "D2", "D3", "A", "B", "E", "F", "PA", "WO", "DA",
                     "ANN", "LC", "PAB", "WOB"]
        },
        "particulars": MIGRATED_PARTICULARS_SCHEMA,
        "applicant": APPLICANT_SCHEMA,
        "additional_information": {
            "type": "string"
        },
        "migration_data": {
            "type": "object"        
        }
    },
    "required": [
        "parties", "class_of_charge", "applicant"
    ],
    "additionalProperties": False
}

MIGRATED_REGISTRATION_SCHEMA = {
    "type": "array",
    "items": MIGRATED_REGISTRATION_ITEM
}


PARAMETER_SCHEMA = {
    "type": "object",
    "properties": {
        "name_type": {"type": "string"},
        "name": {"type": "object",
                 "properties": {
                     "forenames": {"type": "string"},
                     "surname": {"type": "string"},
                     "complex_name": {"type": "string"},
                     "complex_number": {"type": "integer"},
                     "complex_variations": {"type": "array",
                                            "items": COMPLEX_SCHEMA},
                     "local_authority_name": {"type": "string"},
                     "local_authority_area": {"type": "string"},
                     "other_name": {"type": "string"},
                 },
                 },
        "year_from": {"type": "integer", "minimum": 0},
        "year_to": {"type": "integer", "minimum": 0},
    },
    "required": ["name", "name_type"]
}


SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "customer": APPLICANT_SCHEMA,
        "document_id": {"type": "integer"},
        "expiry_date": DATE_SCHEMA,
        "search_date": DATE_SCHEMA,
        "parameters": {
            "type": "object",
            "properties": {
                "search_type": {"type": "string", "enum": ["full", "banks"]},
                "counties": {"type": "array", "items": {"type": "string"}},
                "search_items": {
                    "type": "array",
                    "items": PARAMETER_SCHEMA
                }
            },
            "required": ["search_type", "search_items"]
        }
    },
    "required": ["customer", "parameters", "expiry_date", "search_date"]
}


def validate_migration(data):
    val = Draft4Validator(MIGRATED_REGISTRATION_SCHEMA)
    errors = []
    for error in val.iter_errors(data):
        path = "$"
        while len(error.path) > 0:
            item = error.path.popleft()
            if isinstance(item, int):  # This is an assumption!
                path += "[" + str(item) + "]"
            else:
                path += "." + item
        if path == '$':
            path = '$.'
        print(error.message + "|" + path)
        errors.append({
            "location": path,
            "error_message": error.message
        })

    return errors


def validate_update(data):
    errors = validate_generic_registration(data)
    if 'update_registration' not in data:
        errors.append({'error_message': "Attribute 'update_registration' is required"})
    if 'priority_notice' in data:
        errors.append({'error_message': "Attribute 'priority_notice' is not allowed"})
    return errors


def validate_registration(data):
    errors = validate_generic_registration(data)
    if 'update_registration' in data:
        errors.append({'error_message': "Attribute 'update_registration' is not allowed"})
    return errors


def validate_generic_registration(data):
    val = Draft4Validator(REGISTRATION_SCHEMA)
    errors = []
    for error in val.iter_errors(data):
        path = "$"
        while len(error.path) > 0:
            item = error.path.popleft()
            if isinstance(item, int):  # This is an assumption!
                path += "[" + str(item) + "]"
            else:
                path += "." + item
        if path == '$':
            path = '$.'
        print(error.message + "|" + path)
        errors.append({
            "location": path,
            "error_message": error.message
        })

    # Fail before performing in-depth checks
    if len(errors) > 0:
        return errors

    debtor = None
    estate_owner = None
    for party in data['parties']:
        if party['type'] == 'Debtor':
            debtor = party
        else:
            if party['type'] == 'Estate Owner':
                estate_owner = party

            if 'addresses' in party:
                errors.append({'error_message': 'Addresses not allowed on non-debtor party'})

            if len(party['names']) > 1:
                errors.append({'error_message': 'Multiple names not allowed on non-debtor party'})

    # Bankruptcy specific validation
    if data['class_of_charge'] in ['PAB', 'WOB']:
        if estate_owner is not None:
            errors.append({'error_message': "Party of type 'Estate Owner' not allowed for bankruptcy"})

        if 'priority_notice' in data:
            errors.append({'error_message': "priority_notice not allowed for bankruptcy"})

        if debtor is None:
            errors.append({'error_message': "Party of type 'Debtor' required for bankruptcy"})
        else:
            for item in ['occupation', 'trading_name', 'residence_withheld', 'case_reference']:
                if item not in debtor:
                    errors.append({'error_message': "Attribute '{}' required for bankruptcy debtor".format(item)})

            if 'residence_withheld' in debtor:
                if debtor['residence_withheld'] == True and len(debtor['addresses']) > 0:
                    errors.append({'error_message': 'Debtor residence_withheld is true and addresses are present'})

                if debtor['residence_withheld'] == False and len(debtor['addresses']) == 0:
                    errors.append({'error_message': 'Debtor residence_withheld is false but addresses are missing'})

    # TODO ensure update_registration is not present - somehow - validate update uses this method
    # Land Charge specific validation
    if data['class_of_charge'] not in ['PAB', 'WOB']:
        if debtor is not None:
            errors.append({'error_message': "Party of type 'Debtor' not allowed for land charge"})

        if 'particulars' not in data:
            errors.append({'error_message': "Attribute 'particulars' required for land charge"})
        if estate_owner is None:
            errors.append({'error_message': "Party of type 'Estate Owner' required for land charge"})

    # Check that party types and name structure supplied match
    for party in data['parties']:
        for name in party['names']:
            if name['type'] == 'Private Individual' and 'private' not in name:
                errors.append({'error_message': "Attribute 'private' required for private individual"})

            if name['type'] == "County Council" and 'local' not in name:
                errors.append({'error_message': "Attribute 'local' required for county council"})

            if name['type'] == "Parish Council" and 'local' not in name:
                errors.append({'error_message': "Attribute 'local' required for parish council"})

            if name['type'] == "Rural Council" and 'local' not in name:
                errors.append({'error_message': "Attribute 'local' required for rural council"})

            if name['type'] == "Other Council" and 'local' not in name:
                errors.append({'error_message': "Attribute 'local' required for other council"})

            if name['type'] == "Development Corporation" and 'other' not in name:
                errors.append({'error_message': "Attribute 'other' required for development corporation"})

            if name['type'] == "Limited Company" and 'company' not in name:
                errors.append({'error_message': "Attribute 'company' required for limited company"})

            if name['type'] == "Complex Name" and 'complex' not in name:
                errors.append({'error_message': "Attribute 'complex' required for complex names"})

            if name['type'] == "Other" and 'other' not in name:
                errors.append({'error_message': "Attribute 'other' required for other"})

    return errors

    
def validate(data, schema):
    val = Draft4Validator(schema)
    errors = []
    for error in val.iter_errors(data):
        path = "$"
        while len(error.path) > 0:
            item = error.path.popleft()
            if isinstance(item, int):  # This is an assumption!
                path += "[" + str(item) + "]"
            else:
                path += "." + item
        if path == '$':
            path = '$.'
        print(error.message + "|" + path)
        errors.append({
            "location": path,
            "error_message": error.message
        })

    # Fail before performing in-depth checks
    if len(errors) > 0:
        return errors
