"""Optional exact-facility-by-hospital filtering not supported by old router."""
from backend.services.query_utils import fetch_rows


def search_facilities_extended(*, facility=None, city=None, hospital_name=None):
    query = """SELECT h.id AS hospital_id,h.name AS hospital_name,
            f.name AS facility_name,hf.source_label,hf.availability_notes,
            sd.original_filename AS source_document,hf.source_page
            FROM hospital_facilities hf
            JOIN hospitals h ON h.id=hf.hospital_id
            JOIN facilities f ON f.id=hf.facility_id
            LEFT JOIN source_documents sd ON sd.id=hf.source_document_id
            WHERE 1=1"""
    params = []
    if facility:
        query += " AND (f.name LIKE %s OR hf.source_label LIKE %s)"
        term = f"%{facility.strip()}%"
        params.extend([term, term])
    if city:
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")
    if hospital_name:
        query += " AND h.name LIKE %s"
        params.append(f"%{hospital_name.strip()}%")
    query += " ORDER BY h.name, f.name LIMIT 100"
    return fetch_rows(query, tuple(params))
