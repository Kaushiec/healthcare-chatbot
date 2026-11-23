import json

from backend.services.hospitals import (
    search_hospitals,
    search_departments,
    search_beds,
    search_facilities
)

from backend.services.doctors import search_doctors
from backend.services.prices import search_prices


def preview(label, rows):
    print(f"\n=== {label}: {len(rows)} results ===")
    print(json.dumps(
        rows[:2],
        indent=2,
        ensure_ascii=False,
        default=str
    ))


if __name__ == "__main__":
    preview(
        "Hospitals",
        search_hospitals(city="Kokrajhar")
    )

    preview(
        "Doctors",
        search_doctors()
    )

    preview(
        "Departments",
        search_departments()
    )

    preview(
        "Beds",
        search_beds()
    )

    preview(
        "Facilities",
        search_facilities()
    )

    preview(
        "Service Prices",
        search_prices()
    )