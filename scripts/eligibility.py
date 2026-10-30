"""Small, sourced PM-KISAN pre-screen; never an official eligibility decision."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


RULE_SOURCE_TITLE = "PM-KISAN official scheme page"
RULE_SOURCE_URL = "https://pmkisan.gov.in/"
RULES_CHECKED_AT = "2026-10-29"

REQUIRED_FIELDS = {
    "landholding_farmer": "Does a member of your PM-KISAN family own cultivable land recorded by the State/UT?",
}

EXCLUSION_FIELDS = {
    "institutional_landholder": "Is the landholder an institution?",
    "constitutional_post_holder": "Has any family member held a constitutional post?",
    "political_or_local_office_holder": (
        "Has any family member been a minister, MP, MLA/MLC, municipal corporation mayor, "
        "or district panchayat chairperson?"
    ),
    "non_exempt_government_employee": (
        "Is any family member a serving/retired government, PSU, autonomous-institution, "
        "or regular local-body employee other than MTS/Class IV/Group D?"
    ),
    "pension_10000_or_more": (
        "Does any family member receive a monthly government pension of ₹10,000 or more, "
        "other than an MTS/Class IV/Group D pensioner?"
    ),
    "income_tax_payer": "Did any family member pay income tax in the last assessment year?",
    "practicing_registered_professional": (
        "Is any family member a registered doctor, engineer, lawyer, chartered accountant, "
        "or architect currently practising?"
    ),
}

CAUTION_FIELDS = {
    "ownership_after_2019_02_01": "Was the cultivable land acquired after 1 February 2019?",
    "multiple_family_recipients": "Are multiple members of the family receiving PM-KISAN benefits?",
}

ALL_FIELDS = {**REQUIRED_FIELDS, **EXCLUSION_FIELDS, **CAUTION_FIELDS}


def _yes_no(value: Any) -> bool | None:
    if value is True or (isinstance(value, str) and value.strip().casefold() in {"yes", "true", "1"}):
        return True
    if value is False or (isinstance(value, str) and value.strip().casefold() in {"no", "false", "0"}):
        return False
    return None


def check_pm_kisan(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Apply only the explicitly published portal criteria to user-provided facts."""
    answers = {name: _yes_no(facts.get(name)) for name in ALL_FIELDS}
    missing = [
        {"field": name, "question": ALL_FIELDS[name]}
        for name in (*REQUIRED_FIELDS, *EXCLUSION_FIELDS)
        if answers[name] is None
    ]
    exclusions = [name for name in EXCLUSION_FIELDS if answers[name] is True]
    cautions = [name for name in CAUTION_FIELDS if answers[name] is True]

    if exclusions:
        status = "possible_exclusion"
        message = (
            "One or more answers match a published PM-KISAN exclusion category. "
            "This is a preliminary screen, not an official decision."
        )
    elif answers["landholding_farmer"] is False:
        status = "landholding_requirement_not_confirmed"
        message = (
            "The answer provided does not match the scheme's landholding requirement. "
            "Confirm the land record and family details with the official portal or local authority."
        )
    elif missing:
        status = "needs_more_information"
        message = "Some required facts are unknown, so this screen cannot reach a complete result."
    else:
        status = "no_listed_exclusion_found"
        message = (
            "No listed exclusion was identified from the answers provided. This does not confirm "
            "eligibility, registration, payment status, or approval."
        )

    caution_messages = []
    if "ownership_after_2019_02_01" in cautions:
        caution_messages.append(
            "The official portal says suspected cases where land ownership was acquired after "
            "1 February 2019 may have benefits withheld until physical verification."
        )
    if "multiple_family_recipients" in cautions:
        caution_messages.append(
            "The official portal says suspected cases with multiple family members receiving "
            "benefits may be withheld until physical verification."
        )

    return {
        "status": status,
        "message": message,
        "missing_information": missing,
        "matched_exclusions": exclusions,
        "cautions": caution_messages,
        "source_title": RULE_SOURCE_TITLE,
        "source_url": RULE_SOURCE_URL,
        "rules_checked_at": RULES_CHECKED_AT,
        "family_definition": "The portal defines the farmer's family as husband, wife, and minor children.",
        "disclaimer": (
            "This is not an official eligibility or payment decision. The State/UT administration identifies beneficiaries; "
            "confirm current criteria and status with the official portal or local authority."
        ),
    }
