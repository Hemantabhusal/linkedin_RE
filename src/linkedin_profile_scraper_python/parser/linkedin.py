import json
from typing import Any, Dict, List, Optional

from linkedin_profile_scraper_python.logging_setup import get_logger
from linkedin_profile_scraper_python.models import ExperienceRecord, ProfileResult


LOGGER = get_logger(__name__)


def _format_date(date_value: Optional[Dict[str, Any]]) -> str:
    if not date_value:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month = date_value.get("month")
    year = date_value.get("year")
    if not year:
        return ""
    if month:
        return "%s %s" % (months[month - 1], year)
    return str(year)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in ("text", "name", "localizedName", "defaultLocalizedName", "value"):
            nested_value = value.get(key)
            if isinstance(nested_value, str) and nested_value:
                return nested_value
        return ""
    return ""


def _extract_experiences(profile_position_groups: Optional[Dict[str, Any]]) -> List[ExperienceRecord]:
    experiences = []
    elements = (profile_position_groups or {}).get("elements") or []
    for group in elements:
        company = group.get("company") or {}
        employee_count_range = company.get("employeeCountRange") or {}
        company_size = ""
        if employee_count_range.get("start") is not None:
            company_size = "%s-%s" % (
                employee_count_range.get("start", ""),
                employee_count_range.get("end", ""),
            )

        positions = ((group.get("profilePositionInPositionGroup") or {}).get("elements")) or []
        for position in positions:
            skills = []
            for skill in ((position.get("profileTaxonomySkills") or {}).get("elements")) or []:
                name = ((skill.get("skill") or {}).get("name")) or skill.get("name")
                if name:
                    skills.append(name)

            experiences.append(
                ExperienceRecord(
                    company_name=_as_text(group.get("companyName")),
                    company_linkedin_url=_as_text(company.get("url")),
                    company_linkedin_id=(company.get("entityUrn", "").split(":")[-1] if company.get("entityUrn") else ""),
                    company_size=company_size,
                    company_tenure_start=_format_date((group.get("timePeriod") or {}).get("startDate")),
                    company_tenure_end=_format_date((group.get("timePeriod") or {}).get("endDate")) or "Present",
                    title=_as_text(position.get("title")),
                    employment_type=_as_text(position.get("employmentType")),
                    start_date=_format_date((position.get("timePeriod") or {}).get("startDate")),
                    end_date=_format_date((position.get("timePeriod") or {}).get("endDate")) or "Present",
                    location=_as_text(position.get("geoLocationName")) or _as_text(position.get("locationName")),
                    location_type=(
                        "Remote"
                        if position.get("workRemoteAllowed")
                        else ("On-site" if "On-site" in _as_text(position.get("locationName")) else "")
                    ),
                    description=_as_text(position.get("description")),
                    skills=", ".join(skills),
                )
            )
    return experiences


def _extract_profile(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    elements = payload.get("elements")
    if isinstance(elements, list) and elements:
        return elements[0]

    data = payload.get("data")
    if isinstance(data, dict):
        data_elements = data.get("elements")
        if isinstance(data_elements, list) and data_elements:
            return data_elements[0]

    included = payload.get("included")
    if isinstance(included, list):
        for entry in included:
            if not isinstance(entry, dict):
                continue
            has_identity = isinstance(entry.get("publicIdentifier"), str) or isinstance(entry.get("firstName"), str)
            has_profile_content = any(key in entry for key in ("headline", "summary", "profilePositionGroups"))
            if has_identity and has_profile_content:
                return entry
    return None


def _payload_summary(payload: Dict[str, Any]) -> str:
    summary = {
        "keys": list(payload.keys())[:8],
        "elements_length": len(payload.get("elements", [])) if isinstance(payload.get("elements"), list) else None,
        "included_length": len(payload.get("included", [])) if isinstance(payload.get("included"), list) else None,
    }
    return json.dumps(summary, ensure_ascii=True)


def parse_profile_payload(linkedin_url: str, payload: Dict[str, Any], log_payload_samples: bool) -> ProfileResult:
    profile = _extract_profile(payload)
    if not profile:
        if log_payload_samples:
            LOGGER.debug("Unexpected profile payload summary=%s", _payload_summary(payload))
        raise RuntimeError("No profile data returned for: %s" % linkedin_url)

    educations = ((profile.get("profileEducations") or {}).get("elements")) or []
    latest_education = educations[0] if educations else {}
    first_group = (((profile.get("profilePositionGroups") or {}).get("elements")) or [None])[0] or {}
    first_position = ((((first_group.get("profilePositionInPositionGroup") or {}).get("elements")) or [None])[0]) or {}

    company = first_position.get("company") or {}
    company_range = company.get("employeeCountRange") or {}
    current_company_range = None
    if company_range.get("start") is not None:
        current_company_range = "%s-%s" % (company_range.get("start", ""), company_range.get("end", ""))

    experiences = _extract_experiences(profile.get("profilePositionGroups"))
    entity_urn = profile.get("entityUrn") or ""

    return ProfileResult(
        linkedin_url=linkedin_url,
        first_name=_as_text(profile.get("firstName")) or None,
        last_name=_as_text(profile.get("lastName")) or None,
        headline=_as_text(profile.get("headline")) or None,
        summary=_as_text(profile.get("summary")) or None,
        username=_as_text(profile.get("publicIdentifier")) or None,
        sales_nav_url=(
            "https://www.linkedin.com/sales/people/%s,NAME_SEARCH" % entity_urn.split(":")[-1]
            if entity_urn
            else None
        ),
        country_code=_as_text((profile.get("location") or {}).get("countryCode")) or None,
        country=_as_text((((profile.get("geoLocation") or {}).get("geo") or {}).get("country") or {}).get("defaultLocalizedName")) or None,
        location_name=_as_text((((profile.get("geoLocation") or {}).get("geo")) or {}).get("defaultLocalizedName")) or None,
        industry=_as_text((profile.get("industry") or {}).get("name")) or None,
        avatar_url=(
            ((profile.get("backgroundPicture") or {}).get("displayImageReference") or {}).get("vectorImage") or {}
        ).get("rootUrl", "")
        + (
            ((((profile.get("backgroundPicture") or {}).get("displayImageReference") or {}).get("vectorImage") or {}).get("artifacts") or [{}])[0]
        ).get("fileIdentifyingUrlPathSegment", ""),
        current_role=_as_text(first_position.get("title")) or None,
        current_company=_as_text(first_position.get("companyName")) or _as_text(first_group.get("companyName")) or None,
        current_company_linkedin_url=_as_text(company.get("url")) or None,
        current_company_industry=None,
        current_company_linkedin_id=(company.get("entityUrn", "").split(":")[-1] if company.get("entityUrn") else None),
        current_company_employee_count_range=current_company_range,
        school=_as_text((latest_education.get("school") or {}).get("name")) or None,
        degree=_as_text(latest_education.get("degreeName")) or None,
        field_of_study=_as_text(latest_education.get("fieldOfStudy")) or None,
        activities=_as_text(latest_education.get("activities")) or None,
        school_linkedin_id=(latest_education.get("schoolUrn", "").split(":")[-1] if latest_education.get("schoolUrn") else None),
        school_linkedin_url=_as_text((latest_education.get("school") or {}).get("url")) or None,
        experiences=experiences,
    )
