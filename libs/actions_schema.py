"""
Jsonschema to validate the actions.json.
"""
fields_schema = {
    "type": "array",
    "items": {
        "type": "array",
        "items": [
            {
                "type": "string"
            },
            {
                "type": "string"
            },
            {
                "type": "string",
                "enum": ["button", "checkbox", "color", "date", "datetime-local", "email", "file", "hidden",
                         "image", "month", "number", "password", "radio", "range", "reset", "search",
                         "submit", "tel", "text", "time", "url", "week"]
            },
        ],
        "additionalItems": False,
        "minItems": 3,
        "maxItems": 3
    },
    "uniqueItems": True
}

extended_fields_schema = {
    "type": "array",
    "items": {
        "type": "array",
        "items": [
            {
                "type": "string"
            },
            {
                "type": "string"
            },
            {
                "type": "string",
                "enum": ["button", "checkbox", "color", "date", "datetime-local", "email", "file", "hidden",
                         "image", "month", "number", "password", "radio", "range", "reset", "search",
                         "submit", "tel", "text", "time", "url", "week"]
            },
            {
                "type": "string"
            }
        ],
        "additionalItems": False,
        "minItems": 3,
        "maxItems": 4
    },
    "uniqueItems": True
}

actions_schema = {
    "$schema": "http://json-schema.org/draft/2019-09/schema#",
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "fields": fields_schema,
            "groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "display_name": {"type": "string"},
                        "area": {"type": "string", "enum": ["global", "local"]},
                        "fields": fields_schema
                    },
                    "required": ["name"],
                    "additionalProperties": False
                }
            },
            "updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "function": {"type": "string"},
                        "fields": extended_fields_schema
                    },
                    "required": ["function"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["filename"],
        "additionalProperties": False
    }
}
