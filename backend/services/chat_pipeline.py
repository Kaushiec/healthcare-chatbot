"""Parts 23–37: controlled orchestration of the Ollama + MySQL hospital chatbot.
Model output is validated intent data, never executable SQL or arbitrary tool calls.
"""

import os
import re
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool

from backend.schemas import UserIntent
from backend.llm.intent import extract_intent
from backend.services.router import execute_intent
from backend.services.chat_reply import generate_grounded_answer
from backend.services.chat_results import notice, standardize
from backend.services.location import find_nearby_hospitals
from backend.services.comparison import compare_service_prices
from backend.services.search_extensions import search_facilities_extended
from backend.services.emergency import search_emergency_hospitals
from backend.services.normalization import normalize_intent_filters
from backend.services.chat_memory import (
    get_or_create_session,
    read_context,
    save_exchange,
)


def _memory_enabled():
    return os.getenv("ENABLE_CHAT_MEMORY", "0").strip() == "1"


def apply_followup(message: str, parsed: UserIntent, previous: dict | None):
    """Merge narrow, explicit follow-ups with previous context."""
    if not previous:
        return parsed

    prompt = message.strip().lower()
    is_short_followup = len(message) <= 100 and bool(
        re.match(
            r"^(what about|how about|and (?:at |in |for )?|same (?:for|at)|there\b)",
            prompt,
        )
    )
    if not is_short_followup:
        return parsed

    prev = UserIntent.model_validate(previous)
    if prev.intent not in {
        "hospital_search",
        "doctor_search",
        "department_search",
        "bed_search",
        "facility_search",
        "price_search",
    }:
        return parsed

    if parsed.intent not in ("unknown", "hospital_search", prev.intent):
        return parsed

    joined = prev.model_dump()
    for key, value in parsed.model_dump().items():
        if key == "intent":
            continue
        if value is not None and (not isinstance(value, bool) or value):
            joined[key] = value

    joined["intent"] = prev.intent
    joined["needs_clarification"] = False
    joined["clarification_question"] = None
    return UserIntent.model_validate(joined)


def answer_pending(message: str, pending: dict | None):
    """Resolve narrow follow-ups to clarification questions."""
    if not pending:
        return None

    base = UserIntent.model_validate(pending)
    msg = message.strip()

    amount_match = re.fullmatch(
        r"(?:under|below|upto|up to|maximum|max)?\s*"
        r"(?:₹|rs\.?\s*)?\s*([\d,]+)(?:\s*(?:rupees|inr))?",
        msg,
        re.IGNORECASE,
    )
    if amount_match and base.max_price is None:
        amount = float(amount_match.group(1).replace(",", ""))
        if amount < 0 or amount > 10_000_000:
            return None
        return base.model_copy(
            update={
                "max_price": amount,
                "needs_clarification": False,
                "clarification_question": None,
            }
        )

    if base.intent == "hospital_comparison" and base.service is None:
        # A request for proximity isn't a service name to compare by fee.
        if re.search(
            r"\b(nearby|near me|nearest|closest|distance|within)\b",
            msg,
            re.IGNORECASE,
        ):
            return None

        # Accept a service name alone ("CBC") or a full reply
        # such as "Compare CBC test prices.".
        candidate = re.sub(r"[.!?]+$", "", msg).strip()
        candidate = re.sub(
            r"^(?:please\s+)?(?:compare|show(?:\s+me)?|check)\s+",
            "",
            candidate,
            flags=re.IGNORECASE,
        )
        candidate = re.sub(
            r"\s+(?:test\s+)?(?:prices?|charges?|fees?|costs?)$",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        candidate = re.sub(r"\s+test$", "", candidate, flags=re.IGNORECASE).strip()

        if candidate and len(candidate) <= 100 and re.fullmatch(r"[\w /()&+.-]+", candidate):
            return base.model_copy(
                update={
                    "service": candidate,
                    "needs_clarification": False,
                    "clarification_question": None,
                }
            )

    return None


def route_with_new_features(parsed: UserIntent, location: dict | None):
    if parsed.needs_clarification:
        return notice(
            parsed.intent,
            "needs_clarification",
            parsed.clarification_question or "What additional details should I use?",
        )

    if parsed.intent == "hospital_comparison":
        if parsed.near_me or parsed.max_distance_km is not None:
            return notice(
                parsed.intent,
                "needs_clarification",
                "Distance-based hospital comparisons are not supported yet. "
                "Specify one medical service to compare by fee.",
            )
        if any(
            (
                parsed.hospital_name,
                parsed.doctor_name,
                parsed.department,
                parsed.specialization,
                parsed.bed_type,
                parsed.facility,
                parsed.category,
            )
        ):
            return notice(
                parsed.intent,
                "needs_clarification",
                "This comparison currently accepts one medical service and "
                "optional maximum fee, not additional filters.",
            )
        # Preserve the user's city constraint when comparing fees.
        if parsed.city:
            return compare_service_prices(
                parsed.service or "", max_price=parsed.max_price, city=parsed.city
            )
        return compare_service_prices(parsed.service or "", max_price=parsed.max_price)

    if parsed.near_me or parsed.max_distance_km is not None:
        if parsed.intent != "hospital_search":
            return notice(
                parsed.intent,
                "not_implemented",
                "Near-me/distance search currently supports hospitals only.",
            )
        unsupported = (
            parsed.doctor_name,
            parsed.specialization,
            parsed.bed_type,
            parsed.facility,
            parsed.service,
            parsed.category,
            parsed.max_price,
        )
        if any(value is not None for value in unsupported):
            return notice(
                parsed.intent,
                "needs_clarification",
                "For now, nearby search supports hospital name, city, and department only.",
            )
        if not location:
            return notice(
                parsed.intent,
                "needs_location",
                "Select 'Use my location' and permit browser geolocation, "
                "then resend your request.",
            )
        radius = parsed.max_distance_km if parsed.max_distance_km is not None else 25.0
        if not 0 < radius <= 200:
            return notice(
                parsed.intent,
                "needs_clarification",
                "Choose a search radius greater than 0 km and at most 200 km.",
            )
        return find_nearby_hospitals(
            location["latitude"],
            location["longitude"],
            radius_km=radius,
            city=parsed.city,
            department=parsed.department,
            name=parsed.hospital_name,
        )

    if parsed.intent == "facility_search" and parsed.hospital_name:
        unsupported = (
            parsed.doctor_name,
            parsed.department,
            parsed.specialization,
            parsed.bed_type,
            parsed.service,
            parsed.category,
            parsed.max_price,
        )
        if any(value is not None for value in unsupported):
            return notice(
                parsed.intent,
                "needs_clarification",
                "Unsupported facility search filter combination.",
            )
        rows = search_facilities_extended(
            facility=parsed.facility,
            city=parsed.city,
            hospital_name=parsed.hospital_name,
        )
        return {
            "intent": parsed.intent,
            "status": "ok" if rows else "no_results",
            "message": "Matching facilities found." if rows else "No matching facilities found.",
            "count": len(rows),
            "results": rows,
        }

    
    if parsed.intent == "emergency_search":

        # Distance filtering is not supported by this
        # particular emergency-service function.
        if parsed.near_me or parsed.max_distance_km is not None:
            return notice(
                parsed.intent,
                "not_implemented",
                "Nearby emergency-service filtering is not "
                "implemented yet. Search by city instead."
            )

        # Reject unrelated filters rather than silently
        # ignoring them.
        unsupported = (
            parsed.doctor_name,
            parsed.department,
            parsed.specialization,
            parsed.bed_type,
            parsed.service,
            parsed.category,
            parsed.max_price
        )

        if any(value is not None for value in unsupported):
            return notice(
                parsed.intent,
                "needs_clarification",
                "Emergency-service search currently supports "
                "city, hospital name, and the 24x7 ambulance filter."
            )

        if parsed.facility and (
            "ambulance" not in parsed.facility.lower()
        ):
            return notice(
                parsed.intent,
                "needs_clarification",
                "Please specify whether you want emergency "
                "services or 24x7 ambulance availability."
            )

        rows = search_emergency_hospitals(
            city=parsed.city,
            hospital_name=parsed.hospital_name,
            ambulance_required=bool(parsed.facility)
        )

        return {
            "intent": parsed.intent,
            "status": "ok" if rows else "no_results",
            "message": (
                "Hospitals listing 24x7 emergency services "
                "were found."
                if rows
                else
                "No matching reported 24x7 emergency-service "
                "records were found."
            ),
            "count": len(rows),
            "results": rows
        }


    return execute_intent(parsed)


async def process_chat(
    message: str,
    session_id: str | None = None,
    location: dict | None = None,
):
    """Run a chat request, then return an API response (never fall through to None)."""
    if _memory_enabled():
        sid = await run_in_threadpool(get_or_create_session, session_id)
        context = await run_in_threadpool(read_context, sid)
    else:
        sid = session_id or str(uuid4())
        context = {"history": [], "last_intent": None, "pending_intent": None}

    parsed = answer_pending(message, context.get("pending_intent"))
    if parsed is None:
        parsed = await extract_intent(
            message,
            history=context.get("history"),
            last_intent=context.get("last_intent"),
        )
        parsed = apply_followup(message, parsed, context.get("last_intent"))
    parsed = normalize_intent_filters(parsed)

    # Clarify vague "cheap" requests that have no numeric budget.
    vague_price_words = re.search(
        r"\b(cheap|cheaper|affordable|low.cost|budget.friendly)\b",
        message,
        re.IGNORECASE,
    )
    if (
        parsed.intent in {"doctor_search", "bed_search", "price_search"}
        and parsed.max_price is None
        and vague_price_words
    ):
        parsed = parsed.model_copy(
            update={
                "needs_clarification": True,
                "clarification_question": "What is your maximum budget in rupees?",
            }
        )

    
    # Handle vague best-hospital requests even if
    # the LLM classifies them as unknown.

    if (
        re.search(r"\bbest\b", message, re.IGNORECASE)
        and (
            parsed.intent in {
                "hospital_search",
                "hospital_comparison",
                "facility_search"
            }
            or (
                parsed.intent == "unknown"
                and re.search(
                    r"\bhospitals?\b",
                    message,
                    re.IGNORECASE
                )
            )
        )
        and not parsed.service
    ):
        parsed = parsed.model_copy(
            update={
                "intent": "hospital_comparison",
                "needs_clarification": True,
                "clarification_question": (
                    "What would you like to prioritize: "
                    "the fee for a particular medical service, "
                    "distance from your location, "
                    "or availability of a particular facility?"
                )
            }
        )


    
    # ==========================================
    # Prevent consultation budgets from being
    # misinterpreted as geographic distances.
    # ==========================================

    distance_requested = bool(
        re.search(
            r"\b("
            r"near\s+me|nearby|nearest|closest|"
            r"around\s+me|distance|"
            r"within\s+\d+(?:\.\d+)?\s*"
            r"(?:km|kilometers|kilometres)"
            r")\b",
            message,
            re.IGNORECASE
        )
    )

    # Preserve context for short follow-up questions.
    is_followup = bool(
        re.match(
            r"^\s*("
            r"what about|how about|"
            r"same (?:for|at)|"
            r"and (?:at|in|for)|"
            r"there\b"
            r")",
            message,
            re.IGNORECASE
        )
    )

    # A doctor-search request containing a fee
    # but no distance expression must not
    # inherit invented location parameters.
    if (
        parsed.intent == "doctor_search"
        and not distance_requested
        and not is_followup
    ):
        parsed = parsed.model_copy(
            update={
                "near_me": False,
                "max_distance_km": None
            }
        )

    
    # Previously missing: route, answer, memory save, and final return.
    routing = standardize(
        await run_in_threadpool(route_with_new_features, parsed, location)
    )
    answer = await generate_grounded_answer(message, routing)

    pending = (
        parsed.model_dump(mode="json")
        if routing.get("status") == "needs_clarification"
        else None
    )
    last = (
        parsed.model_dump(mode="json")
        if routing.get("status")
        in {"ok", "no_results", "unverified_comparison", "insufficient_data", "not_comparable"}
        else context.get("last_intent")
    )

    if _memory_enabled():
        await run_in_threadpool(
            save_exchange,
            sid,
            message,
            answer,
            last,
            pending,
        )

    return {
        "session_id": sid,
        "answer": answer,
        "intent": parsed.intent,
        "status": routing["status"],
        "count": routing.get("count", 0),
        "results": routing.get("results", []),
        "message": routing.get("message", ""),
        "filters": parsed.model_dump(mode="json", exclude_none=True),
    }
