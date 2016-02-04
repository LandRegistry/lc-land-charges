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
    "required": ["local", "area"],
    "additionalProperties": False
}

COMPLEX_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "number": {"type": "string"}
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
    "additionalProperties": False
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
            "pattern": "^\d{7}$"
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

REGISTRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "parties": {
            "type": "array",
            "items": PARTY_SCHEMA
        },
        # "debtor_addresses": {
        #     "type": "array",
        #     "items": ADDRESS_SCHEMA
        # },
        "class_of_charge": {
            "type": "string",
            "enum": ["C1", "C2", "C3", "C4", "D1", "D2", "D3", "A", "B", "E", "F", "PA", "WO", "DA",
                     "ANN", "LC", "PAB", "WOB"]
        },
        "particulars": PARTICULARS_SCHEMA,
        #"debtor": DEBTOR_SCHEMA,
        "applicant": APPLICANT_SCHEMA,
        "additional_information": {
            "type": "string"
        }
    },
    "required": [
        "parties", "class_of_charge", "applicant"
    ],
    "additionalProperties": False
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
        "year_from": {"type": "integer", "minimum": 1925},
        "year_to": {"type": "integer", "minimum": 1925},
    },
    "required": ["name"]
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
                "search_type": {"type": "string"},
                "counties": {"type": "array", "items": {"type": "string"}},
                "search_items": {
                    "type": "array",
                    "items": PARAMETER_SCHEMA
                }
            }
        }
    },
    "required": ["customer", "parameters", "expiry_date", "search_date"]
}


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

    # Ensure PAB/WOB has a 'debtor' entry (already assured that class_of_charge is valid)
    # if data['class_of_charge'] in ['PAB', 'WOB'] and 'debtor' not in data:
    #     errors.append({'error_message': "Attribute 'debtor' required for bankruptcy"})
    # TODO ensure debtor party present on bankruptcy
    # TODO ensure occupation, trading, res_wh & ref on debtor party
    # TODO ensure consistency of addresses and res_wh on debtor party
    # TODO ensure only addresses on Debtor party
    # TODO allow aliases only on Debtor party
    # If not a PAB/WOB, it's a land charge - make sure it has a 'particulars' entry
    if data['class_of_charge'] not in ['PAB', 'WOB'] and 'particulars' not in data:
        errors.append({'error_message': "Attribute 'particulars' required for land charge"})

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
