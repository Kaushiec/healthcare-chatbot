from backend.services.query_utils import fetch_rows


def search_prices(
    service: str | None = None,
    hospital: str | None = None,
    category: str | None = None,
    max_price: float | None = None
) -> list[dict]:

    query = """
        SELECT
            r.id AS rate_id,
            h.name AS hospital_name,
            s.source_name AS service_name,
            s.category,
            s.comparison_key,
            r.price_min,
            r.price_max,
            r.fee_unit,
            r.original_price_text,
            r.price_status,
            r.last_verified,
            r.notes,
            sd.original_filename AS source_document,
            r.source_page

        FROM hospital_service_rates AS r

        JOIN hospitals AS h
            ON h.id = r.hospital_id

        JOIN medical_services AS s
            ON s.id = r.service_id

        JOIN source_documents AS sd
            ON sd.id = r.source_document_id

        WHERE r.price_status = 'quoted'
          AND (
              r.price_min IS NOT NULL
              OR r.price_max IS NOT NULL
          )
    """

    params = []

    if service and service.strip():
        query += " AND s.source_name LIKE %s"
        params.append(f"%{service.strip()}%")

    if hospital and hospital.strip():
        query += " AND h.name LIKE %s"
        params.append(f"%{hospital.strip()}%")

    if category and category.strip():
        query += " AND s.category LIKE %s"
        params.append(f"%{category.strip()}%")

    if max_price is not None:
        query += """
            AND COALESCE(r.price_max, r.price_min) <= %s
        """
        params.append(max_price)

    query += """
        ORDER BY s.source_name, h.name, r.id
        LIMIT 100
    """

    return fetch_rows(query, tuple(params))