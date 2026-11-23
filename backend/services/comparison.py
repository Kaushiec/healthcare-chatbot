"""Compare only deliberately aligned service tariffs and matching fee units.
Ranking requires unambiguous fixed, dated prices from at least two hospitals.
"""
from decimal import Decimal
from backend.services.query_utils import fetch_rows
from backend.services.chat_results import notice


SERVICE_ALIASES = {
    "cbc": "cbc",
    "cbc test": "cbc",
    "cbc test price": "cbc",
    "cbc test prices": "cbc",
    "complete blood count": "cbc",
    "complete blood count test": "cbc",
    "complete blood count (cbc)": "cbc",
    "compare cbc test prices": "cbc",
}


def normalize_service_name(service: str) -> str:
    key = " ".join(
        service.strip().lower().split()
    )

    key = key.rstrip(".?!").strip()

    return SERVICE_ALIASES.get(key, key)



def compare_service_prices(service: str, max_price=None, city: str | None = None):
    if not service or not service.strip():
        return notice("hospital_comparison", "needs_clarification",
                      "Which specific medical service or test should I compare (for example, CBC)?")
    key = normalize_service_name(service)
    query = """SELECT h.id AS hospital_id, h.name AS hospital_name,
                 s.source_name AS service_name, s.category, s.comparison_key,
                 r.price_min, r.price_max, r.fee_unit, r.last_verified,
                 r.price_status, sd.original_filename AS source_document
                 FROM hospital_service_rates r
                 JOIN hospitals h ON h.id=r.hospital_id
                 JOIN medical_services s ON s.id=r.service_id
                 JOIN source_documents sd ON sd.id=r.source_document_id
                 WHERE r.price_status='quoted'
                   AND r.price_min IS NOT NULL AND r.price_max IS NOT NULL
                   AND (LOWER(s.comparison_key)=%s OR LOWER(s.source_name)=%s)
                 """
    params = [key, key]
    if city and city.strip():
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")
    query += " ORDER BY h.name, r.id LIMIT 150"
    rows = fetch_rows(query, tuple(params))
    if max_price is not None:
        rows = [r for r in rows if Decimal(str(r["price_max"])) <= Decimal(str(max_price))]
    if not rows:
        return notice("hospital_comparison", "no_results",
                      "No source-quoted charges matched that exact service/comparison key. Verify service equivalence first.")
    
    units = {
        str(r.get("fee_unit") or "").strip().lower()
        for r in rows
    }

    hospital_ids = [
        r["hospital_id"] for r in rows
    ]

    comparison_keys = {
        str(r.get("comparison_key") or "").strip().lower()
        for r in rows
    }

    services_aligned = (
        len(comparison_keys) == 1
        and "" not in comparison_keys
    )

    units_known = (
        len(units) == 1
        and next(iter(units)) not in {
            "unknown", "unspecified", ""
        }
    )

    fixed = all(
        Decimal(str(r["price_min"])) ==
        Decimal(str(r["price_max"]))
        for r in rows
    )

    dated = all(
        r.get("last_verified") is not None
        for r in rows
    )

    if (
        not services_aligned
        or not units_known
        or len(set(hospital_ids)) != len(hospital_ids)
        or not fixed
    ):
        status = "not_comparable"
        explanation = (
            "The records have unmatched comparison keys, "
            "different or unknown fee units, ambiguous "
            "listings, or price ranges. "
            "A reliable ranking cannot be provided."
        )

    elif len(set(hospital_ids)) < 2:
        status = "insufficient_data"
        explanation = (
            "Only one hospital has a matching charge. "
            "A comparison requires at least two hospitals."
        )

    elif not dated:
        status = "unverified_comparison"
        explanation = (
            "These are source-listed charges, but their "
            "verification dates are missing. "
            "Confirm current prices with the hospitals."
        )

    else:
        status = "ok"
        explanation = (
            "Comparable dated fixed fees, sorted from "
            "lowest to highest. Confirm current charges "
            "with the hospitals before use."
        )

        rows.sort(
            key=lambda r: Decimal(str(r["price_min"]))
        )

    return {
        "intent": "hospital_comparison",
        "status": status,
        "message": explanation,
        "count": len(rows),
        "results": rows
    }

