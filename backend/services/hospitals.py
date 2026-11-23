from backend.services.query_utils import fetch_rows


def search_hospitals(
    city: str | None = None,
    department: str | None = None,
    name: str | None = None
) -> list[dict]:

    query = """
        SELECT
            h.id,
            h.name,
            h.address,
            h.city,
            h.phone,
            h.emergency_24x7,
            h.ambulance_24x7,
            h.total_beds_min,
            h.total_beds_max,
            h.capacity_notes
        FROM hospitals AS h
        WHERE 1 = 1
    """

    params = []

    if city and city.strip():
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")

    if name and name.strip():
        query += " AND h.name LIKE %s"
        params.append(f"%{name.strip()}%")

    if department and department.strip():
        query += """
            AND EXISTS (
                SELECT 1
                FROM hospital_departments AS hd
                JOIN departments AS d
                    ON d.id = hd.department_id
                WHERE hd.hospital_id = h.id
                  AND d.name LIKE %s
            )
        """

        params.append(f"%{department.strip()}%")

    query += " ORDER BY h.name ASC LIMIT 50"

    return fetch_rows(query, tuple(params))


def search_departments(
    city: str | None = None,
    department: str | None = None
) -> list[dict]:

    query = """
        SELECT
            h.id AS hospital_id,
            h.name AS hospital_name,
            d.id AS department_id,
            d.name AS department_name,
            hd.availability_type,
            hd.availability_notes
        FROM hospital_departments AS hd

        JOIN hospitals AS h
            ON h.id = hd.hospital_id

        JOIN departments AS d
            ON d.id = hd.department_id

        WHERE 1 = 1
    """

    params = []

    if city and city.strip():
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")

    if department and department.strip():
        query += " AND d.name LIKE %s"
        params.append(f"%{department.strip()}%")

    query += " ORDER BY d.name, h.name LIMIT 100"

    return fetch_rows(query, tuple(params))


def search_beds(
    hospital: str | None = None,
    bed_type: str | None = None,
    max_price: float | None = None
) -> list[dict]:

    query = """
        SELECT
            h.id AS hospital_id,
            h.name AS hospital_name,
            b.id AS bed_record_id,
            b.bed_type,
            b.reported_bed_count,
            b.reported_room_count,
            b.available_beds AS unverified_available_beds,
            b.price_min,
            b.price_max,
            b.price_unit,
            b.notes,
            sd.original_filename AS source_document,
            b.source_page

        FROM hospital_bed_types AS b

        JOIN hospitals AS h
            ON h.id = b.hospital_id

        LEFT JOIN source_documents AS sd
            ON sd.id = b.source_document_id

        WHERE 1 = 1
    """

    params = []

    if hospital and hospital.strip():
        query += " AND h.name LIKE %s"
        params.append(f"%{hospital.strip()}%")

    if bed_type and bed_type.strip():
        query += " AND b.bed_type LIKE %s"
        params.append(f"%{bed_type.strip()}%")

    if max_price is not None:
        query += """
            AND COALESCE(b.price_max, b.price_min) <= %s
        """
        params.append(max_price)

    query += " ORDER BY h.name, b.bed_type LIMIT 100"

    return fetch_rows(query, tuple(params))


def search_facilities(
    facility: str | None = None,
    city: str | None = None
) -> list[dict]:

    query = """
        SELECT
            h.id AS hospital_id,
            h.name AS hospital_name,
            f.name AS facility_name,
            hf.source_label,
            hf.availability_notes,
            sd.original_filename AS source_document,
            hf.source_page

        FROM hospital_facilities AS hf

        JOIN hospitals AS h
            ON h.id = hf.hospital_id

        JOIN facilities AS f
            ON f.id = hf.facility_id

        LEFT JOIN source_documents AS sd
            ON sd.id = hf.source_document_id

        WHERE 1 = 1
    """

    params = []

    if facility and facility.strip():
        query += """
            AND (
                f.name LIKE %s
                OR hf.source_label LIKE %s
            )
        """

        term = f"%{facility.strip()}%"
        params.extend([term, term])

    if city and city.strip():
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")

    query += " ORDER BY f.name, h.name LIMIT 100"

    return fetch_rows(query, tuple(params))