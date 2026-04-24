import json
from pathlib import Path
from typing import Any, Dict, List

from client import LinkedInClient
from config import get_settings
from logging_setup import configure_logging, get_logger


LOGGER = get_logger(__name__)


def _redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Payloads can contain public profile data. We keep the shape intact and
    # only remove obvious auth/session keys if LinkedIn ever includes them.
    redacted = dict(payload)
    for key in ("Cookie", "csrf-token", "li_at", "JSESSIONID"):
        redacted.pop(key, None)
    return redacted


def _first_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    elements = payload.get("elements")
    if isinstance(elements, list) and elements:
        first = elements[0]
        return first if isinstance(first, dict) else {}

    data = payload.get("data")
    if isinstance(data, dict):
        data_elements = data.get("elements")
        if isinstance(data_elements, list) and data_elements:
            first = data_elements[0]
            return first if isinstance(first, dict) else {}

    return {}


def _section_count(profile: Dict[str, Any], keys: List[str]) -> int:
    total = 0
    for key in keys:
        section = profile.get(key)
        if isinstance(section, dict):
            elements = section.get("elements")
            if isinstance(elements, list):
                total += len(elements)
        elif isinstance(section, list):
            total += len(section)
    return total


def _section_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = _first_profile(payload)
    return {
        "payload_keys": list(payload.keys())[:12],
        "profile_keys": list(profile.keys())[:40],
        "experience_count": _section_count(profile, ["profilePositionGroups"]),
        "education_count": _section_count(profile, ["profileEducations"]),
        "certification_count": _section_count(
            profile,
            [
                "profileCertifications",
                "profileLicensesAndCertifications",
                "profileLicenseAndCertifications",
            ],
        ),
        "top_skill_count": _section_count(profile, ["profileTopSkills", "topSkills", "profileSkills"]),
    }


def dump_url(url: str, output_path: str) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, verbose=settings.verbose_logging)

    client = LinkedInClient(settings)
    LOGGER.info("Verifying LinkedIn session...")
    client.verify_session()
    LOGGER.info("LinkedIn session verified.")

    payload = client.get_json(url, context="diagnostic dump")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_redact_payload(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Wrote payload: %s", path)
    return 0


def dump_profile(linkedin_url: str, output_path: str) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, verbose=settings.verbose_logging)

    client = LinkedInClient(settings)
    LOGGER.info("Verifying LinkedIn session...")
    client.verify_session()
    LOGGER.info("LinkedIn session verified.")

    payload = client.get_profile_payload(linkedin_url)
    summary = _section_summary(payload)
    LOGGER.info(
        "Profile payload summary: experiences=%s educations=%s certifications=%s top_skills=%s",
        summary["experience_count"],
        summary["education_count"],
        summary["certification_count"],
        summary["top_skill_count"],
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "summary": summary,
                "payload": _redact_payload(payload),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    LOGGER.info("Wrote profile payload: %s", path)
    return 0
