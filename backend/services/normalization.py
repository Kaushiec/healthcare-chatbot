
from backend.schemas import UserIntent


FACILITY_ALIASES = {
    "cat scan": "CT Scan",
    "ct scan": "CT Scan",
    "ct": "CT Scan",
    "usg": "Ultrasound",
    "ultrasonography": "Ultrasound",
    "ultrasound scan": "Ultrasound",
}


DEPARTMENT_ALIASES = {
    "ear nose throat": "ENT",
    "ear nose and throat": "ENT",
    "ent": "ENT",
    "heart department": "Cardiology",
    "cardiac department": "Cardiology",
}


def normalize_term(value: str, aliases: dict) -> str:
    key = " ".join(value.casefold().split())
    return aliases.get(key, value.strip())


def normalize_intent_filters(parsed: UserIntent) -> UserIntent:

    updates = {}

    if parsed.facility:
        updates["facility"] = normalize_term(
            parsed.facility,
            FACILITY_ALIASES
        )

    if parsed.department:
        updates["department"] = normalize_term(
            parsed.department,
            DEPARTMENT_ALIASES
        )

    if parsed.specialization:
        updates["specialization"] = normalize_term(
            parsed.specialization,
            DEPARTMENT_ALIASES
        )

    if not updates:
        return parsed

    return parsed.model_copy(update=updates)
