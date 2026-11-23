
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


IntentName = Literal[
    # Currently implemented
    "hospital_search",
    "doctor_search",
    "department_search",
    "bed_search",
    "facility_search",
    "price_search",
    "emergency_search",

    # Recognized, but not implemented yet
    "hospital_details",
    "doctor_details",
    "pharmacy_search",
    "medicine_search",
    "medicine_availability",
    "medicine_price",
    "hospital_comparison",
    "pharmacy_comparison",
    "medicine_comparison",
    "general_healthcare_info",
    "unknown",
]


class UserIntent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )

    intent: IntentName

    city: str | None = Field(default=None, max_length=100)
    hospital_name: str | None = Field(default=None, max_length=200)
    doctor_name: str | None = Field(default=None, max_length=180)
    department: str | None = Field(default=None, max_length=130)
    specialization: str | None = Field(default=None, max_length=130)
    bed_type: str | None = Field(default=None, max_length=170)
    facility: str | None = Field(default=None, max_length=170)
    service: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=110)

    max_price: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False
    )

    near_me: bool = False

    max_distance_km: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False
    )

    needs_clarification: bool = False
    clarification_question: str | None = Field(
        default=None,
        max_length=300
    )

    @field_validator(
        "city",
        "hospital_name",
        "doctor_name",
        "department",
        "specialization",
        "bed_type",
        "facility",
        "service",
        "category",
        "clarification_question"
    )
    @classmethod
    def empty_string_is_none(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value
