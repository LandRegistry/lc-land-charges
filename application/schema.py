from jsonschema import Draft4Validator

CUSTOMER_SCHEMA = {
    "type": "object",
    "properties": {
        "key_number": {"type": "string"},
        "name": {"type": "string"},
        "address": {"type": "string"},
        "reference": {"type": "string"},
    },
    "required": ["name", "address", "reference", "key_number"]
}


PARAMETER_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "year_from": {"type": "integer", "minimum": 1925},
        "year_to": {"type": "integer", "minimum": 1925},
    },
    "required": ["name"]
}


SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "customer": CUSTOMER_SCHEMA,
        "document_id": {"type": "integer"},
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
    "required": ["customer", "parameters"]
}

NAME_SCHEMA = {
    "type": "object",
    "properties": {
        "forenames": {
            "type": "array",
            "items": {"type": "string"}
        },
        "surname": {"type": "string"}
    },
    "required": ["forenames", "surname"]
}

ADDRESS_SCHEMA = {
    "type": "object",
    "properties": {
        "address_lines": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "county": {"type": "string"},
        "postcode": {"type": "string"}
    },
    "required": ["address_lines", "postcode", "county"]
}

DATE_SCHEMA = {
    "type": "string",
    "pattern": "^([0-9]{4}-[0-9]{2}-[0-9]{2})$"
}

BANKRUPTCY_SCHEMA = {
    "type": "object",
    "properties": {
        "key_number": {
            "type": "string",
            "pattern": "^\d+$"
        },
        "application_type": {
            "type": "string",
            "enum": ["PA(B)", "WO(B)"]
        },
        "application_ref": {"type": "string"},
        "date": DATE_SCHEMA,
        "debtor_names": {
            "type": "array",
            "items": NAME_SCHEMA
        },
        "gender": {"type": "string"},
        "occupation": {"type": "string"},
        "trading_name": {"type": "string"},
        "residence": {
            "type": "array",
            "items": ADDRESS_SCHEMA
        },
        "residence_withheld": {"type": "boolean"},
        "business_address": {
            "type": "array",
            "items": ADDRESS_SCHEMA
        },
        "date_of_birth": DATE_SCHEMA,
        "investment_property": {
            "type": "array",
            "items": ADDRESS_SCHEMA
        },
        "original_request": {
            "type": "string"
        }
    },
    "required": ["key_number", "application_type", "application_ref", "date", "debtor_names",
                 "residence_withheld"]
}

LANDCHARGE_SCHEMA = {
    "type": "object",
    "properties": {
        "key_number": {
            "type": "string",
            "pattern": "^\d+$"
        },
        "class_of_charge": {
            "type": "string"
        },
        "application_ref": {"type": "string"},
        "date": DATE_SCHEMA,
        "gender": {"type": "string"},
        "occupation": {"type": "string"}
    },
    "required": ["key_number", "class_of_charge", "application_ref", "date"]
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
    return errors

# {'date': '2016-01-01', 'residence_withheld': False, 'key_number': '1234567',
#  'occupation': 'Civil Servant', 'original_request': '{"key_number":"1234567",'
# "application_ref":"APP01","application_type":"PA(B)","application_date":"2016-01-01",\n
# "debtor_names":[{"forenames":["Bob","Oscar","Francis"],"surname":"Howard"}, {"forenames":
# ["Robert"], "surname": "Howard"}],\n\n"gender":"Unknown",\n"occupation":"Civil Servant",
# "trading_name":"","residence_withheld":false,"date_of_birth":"1980-01-01",\n\n
# "residence":[{"address_lines": ["1 The Street","The Town"],"postcode":"AA1 1AA","county":
#     "The County"},\n    {"address_lines": ["2 The Road","The Village"],"postcode":"AA2 2AA",
#                          "county":"The County"}\n    ]\n    \n}', 'debtor_names':' \
#  [{'forenames': ['Bob', 'Oscar', 'Francis'], 'surname': 'Howard'}, {'forenames': ['Robert'],
# 'surname': 'Howard'}], 'date_of_birth': '1980-01-01', 'application_ref': 'APP01', 'trading_name': '', 'gender': 'Unknown', 'residence': [{'county': 'The County', 'postcode': 'AA1 1AA', 'address_lines': ['1 The Street', 'The Town']}, {'county': 'The County', 'postcode': 'AA2 2AA', 'address_lines': ['2 The Road', 'The Village']}], 'application_type': 'PA(B)'}