

CUSTOMER_SCHEMA = {
    "type": "object",
    "properties": {
        "key_number": {"type": "string"},
        "name": {"type": "string"},
        "address": {"type": "string"},
        "reference": {"type": "string"},
    },
    "required": ["name", "address"]
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
