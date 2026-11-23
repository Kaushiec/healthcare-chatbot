
from backend.services.query_utils import fetch_rows


def search_emergency_hospitals(
    city: str | None = None,
    hospital_name: str | None = None,
    ambulance_required: bool = False
) -> list[dict]:

    query = """
        SELECT
            h.id,
            h.name,
            h.address,
            h.city,
            h.phone,
            h.emergency_24x7,
            h.ambulance_24x7

        FROM hospitals AS h

        WHERE h.emergency_24x7 = 1
    """

    params = []

    if city and city.strip():
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")

    if hospital_name and hospital_name.strip():
        query += " AND h.name LIKE %s"
        params.append(f"%{hospital_name.strip()}%")

    if ambulance_required:
        query += " AND h.ambulance_24x7 = 1"

    query += " ORDER BY h.name ASC LIMIT 50"

    return fetch_rows(query, tuple(params))
