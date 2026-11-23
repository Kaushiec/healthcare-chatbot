
from backend.schemas import UserIntent

from backend.services.hospitals import (
    search_hospitals,
    search_departments,
    search_beds,
    search_facilities
)

from backend.services.doctors import search_doctors
from backend.services.prices import search_prices


IMPLEMENTED = {
    "hospital_search",
    "doctor_search",
    "department_search",
    "bed_search",
    "facility_search",
    "price_search"
}


def _notice(
    intent: str,
    status: str,
    message: str
) -> dict:

    return {
        "intent": intent,
        "status": status,
        "message": message,
        "count": 0,
        "results": []
    }


def execute_intent(parsed: UserIntent) -> dict:

    name = parsed.intent

    # 1. Never execute an unimplemented operation.

    if name not in IMPLEMENTED:
        return _notice(
            name,
            "not_implemented",
            "That request is not supported in the "
            "hospital-only prototype yet."
        )

    # 2. Honor clarification requests.

    if parsed.needs_clarification:
        return _notice(
            name,
            "needs_clarification",
            parsed.clarification_question
            or "Could you provide more details?"
        )

    # 3. Do not pretend that distance search works.

    if parsed.near_me or parsed.max_distance_km is not None:
        return _notice(
            name,
            "needs_location",
            "Near-me and distance filtering are not "
            "available in this phase. Please search "
            "by city or hospital name where supported."
        )

    # 4. Define the filters each existing function supports.

    accepted_filters = {
        "hospital_search": {
            "city", "hospital_name", "department"
        },
        "doctor_search": {
            "hospital_name", "department",
            "specialization", "max_price"
        },
        "department_search": {
            "city", "department"
        },
        "bed_search": {
            "hospital_name", "bed_type", "max_price"
        },
        "facility_search": {
            "city", "facility"
        },
        "price_search": {
            "hospital_name", "service",
            "category", "max_price"
        }
    }

    all_filters = {
        "city", "hospital_name", "doctor_name",
        "department", "specialization",
        "bed_type", "facility", "service",
        "category", "max_price"
    }

    data = parsed.model_dump()

    ignored_filters = sorted(
        key
        for key in all_filters - accepted_filters[name]
        if data[key] is not None
    )

    if ignored_filters:
        return _notice(
            name,
            "needs_clarification",
            "This search cannot apply these filters yet: "
            + ", ".join(ignored_filters)
            + ". Please try a supported combination."
        )

    # 5. Execute only an approved Python search function.

    if name == "hospital_search":

        rows = search_hospitals(
            city=parsed.city,
            department=parsed.department,
            name=parsed.hospital_name
        )

    elif name == "doctor_search":

        rows = search_doctors(
            specialization=(
                parsed.specialization or parsed.department
            ),
            hospital=parsed.hospital_name,
            max_price=parsed.max_price
        )

    elif name == "department_search":

        rows = search_departments(
            city=parsed.city,
            department=parsed.department
        )

    elif name == "bed_search":

        rows = search_beds(
            hospital=parsed.hospital_name,
            bed_type=parsed.bed_type,
            max_price=parsed.max_price
        )

    elif name == "facility_search":

        rows = search_facilities(
            facility=parsed.facility,
            city=parsed.city
        )

    elif name == "price_search":

        rows = search_prices(
            service=parsed.service,
            hospital=parsed.hospital_name,
            category=parsed.category,
            max_price=parsed.max_price
        )

    else:
        return _notice(
            name,
            "not_implemented",
            "Unsupported search intent."
        )

    # 6. Return structured factual results.

    return {
        "intent": name,
        "status": "ok" if rows else "no_results",
        "message": (
            "Matching records were found."
            if rows
            else
            "No matching records were found "
            "in the current database."
        ),
        "count": len(rows),
        "results": rows
    }
