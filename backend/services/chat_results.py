"""Convert search-service outputs into JSON-safe, clearly labeled API responses."""
from decimal import Decimal
from datetime import date, datetime


def json_safe(value):
    if isinstance(value, Decimal):
        return str(value)  # preserve currency precision
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(x) for x in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def notice(intent, status, message):
    return {"intent": intent, "status": status, "message": message,
            "count": 0, "results": []}


from typing import Any


def standardize(result: dict[str, Any]) -> dict[str, Any]:

    # Convert database values into JSON-safe values.
    clean = json_safe(result)

    # Ensure the result is a dictionary.
    if not isinstance(clean, dict):
        raise TypeError(
            "Expected a dictionary from the search router"
        )

    # Give the dictionary an explicit, flexible value type.
    normalized: dict[str, Any] = dict(clean)

    # Ensure the results field contains a list.
    rows = normalized.get("results")

    if not isinstance(rows, list):
        rows = []
        normalized["results"] = rows

    # Add the result count if it does not already exist.
    if "count" not in normalized:
        normalized["count"] = len(rows)

    return normalized
