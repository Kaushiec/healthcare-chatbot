"""Straight-line distance only. Does not estimate road travel time or routing."""
from math import atan2, cos, radians, sin, sqrt
from backend.services.query_utils import fetch_rows
from backend.services.chat_results import notice


def haversine_km(lat1, lon1, lat2, lon2):
    for lat in (lat1, lat2):
        if not -90 <= float(lat) <= 90:
            raise ValueError("latitude out of bounds")
    for lon in (lon1, lon2):
        if not -180 <= float(lon) <= 180:
            raise ValueError("longitude out of bounds")
    a1, a2 = radians(float(lat1)), radians(float(lat2))
    da = a2 - a1
    dl = radians(float(lon2) - float(lon1))
    a = sin(da/2)**2 + cos(a1)*cos(a2)*sin(dl/2)**2
    return 6371.0088 * (2 * atan2(sqrt(a), sqrt(max(0.0, 1-a))))


def find_nearby_hospitals(latitude, longitude, *, radius_km=25.0,
                          city=None, department=None, name=None):
    if not 0 < radius_km <= 200:
        raise ValueError("radius_km must be greater than 0 and at most 200")
    query = """SELECT h.id, h.name, h.address, h.city, h.phone, h.latitude,
            h.longitude, h.emergency_24x7, h.total_beds_min, h.total_beds_max
            FROM hospitals h WHERE h.latitude IS NOT NULL
            AND h.longitude IS NOT NULL"""
    params = []
    if city:
        query += " AND h.city LIKE %s"
        params.append(f"%{city.strip()}%")
    if name:
        query += " AND h.name LIKE %s"
        params.append(f"%{name.strip()}%")
    if department:
        query += """ AND EXISTS (SELECT 1 FROM hospital_departments hd
                     JOIN departments d ON d.id=hd.department_id
                     WHERE hd.hospital_id=h.id AND d.name LIKE %s)"""
        params.append(f"%{department.strip()}%")
    query += " LIMIT 500"
    rows = fetch_rows(query, tuple(params))
    if not rows:
        return notice("hospital_search", "missing_coordinates",
                      "No matching hospitals have verified coordinates yet. Add valid latitude and longitude first.")
    results = []
    for row in rows:
        dist = haversine_km(latitude, longitude, row["latitude"], row["longitude"])
        if dist <= radius_km:
            # Avoid exposing user latitude/longitude in response.
            result = {k: v for k, v in row.items() if k not in ("latitude", "longitude")}
            result["distance_km"] = round(dist, 2)
            result["distance_kind"] = "straight_line"
            results.append(result)
    results.sort(key=lambda item: item["distance_km"])
    return {"intent": "hospital_search", "status": "ok" if results else "no_results",
            "message": ("Nearby hospital records with verified coordinates." if results
                        else "No coordinate-verified hospitals within that straight-line radius."),
            "count": len(results), "results": results[:50]}
