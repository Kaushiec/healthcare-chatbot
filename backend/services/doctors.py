from backend.services.query_utils import fetch_rows


def search_doctors(
    specialization: str | None = None,
    hospital: str | None = None,
    max_price: float | None = None
) -> list[dict]:

    query = """
        SELECT
            hd.id AS hospital_doctor_id,
            d.id AS doctor_id,
            d.display_name AS doctor_name,
            d.qualifications,
            d.provider_type,
            dep.name AS department_name,
            h.id AS hospital_id,
            h.name AS hospital_name,
            hd.consultation_fee,
            hd.availability_notes
        FROM hospital_doctors AS hd

        JOIN doctors AS d
            ON d.id = hd.doctor_id

        JOIN hospitals AS h
            ON h.id = hd.hospital_id

        LEFT JOIN departments AS dep
            ON dep.id = hd.department_id

        WHERE 1 = 1
    """

    params = []

    if specialization and specialization.strip():
        query += " AND dep.name LIKE %s"
        params.append(f"%{specialization.strip()}%")

    if hospital and hospital.strip():
        query += " AND h.name LIKE %s"
        params.append(f"%{hospital.strip()}%")

    if max_price is not None:
        query += " AND hd.consultation_fee <= %s"
        params.append(max_price)

    query += " ORDER BY h.name, d.display_name LIMIT 100"

    return fetch_rows(query, tuple(params))