import json
from typing import Any, Dict, List, Optional

from logging_setup import get_logger
from models import CertificationRecord, EducationRecord, ExperienceRecord, ProfileResult, SkillRecord


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


def _date_range_start(value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    if "start" in value or "end" in value:
        return value.get("start")
    return (value.get("timePeriod") or {}).get("startDate")


def _date_range_end(value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    if "start" in value or "end" in value:
        return value.get("end")
    return (value.get("timePeriod") or {}).get("endDate")


def _format_range_start(record: Dict[str, Any]) -> str:
    return _format_date(_date_range_start(record.get("dateRange") or record.get("timePeriod")))


def _format_range_end(record: Dict[str, Any], default: str = "") -> str:
    return _format_date(_date_range_end(record.get("dateRange") or record.get("timePeriod"))) or default


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


def _extract_skill_names(container: Optional[Dict[str, Any]]) -> List[str]:
    skills = []
    elements = (container or {}).get("elements") or []
    for item in elements:
        if not isinstance(item, dict):
            continue
        name = _as_text((item.get("skill") or {}).get("name")) or _as_text(item.get("name"))
        if name:
            skills.append(name)
    return skills


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
            skills = _extract_skill_names(position.get("profileTaxonomySkills"))

            experiences.append(
                ExperienceRecord(
                    company_name=_as_text(group.get("companyName")),
                    company_linkedin_url=_as_text(company.get("url")),
                    company_linkedin_id=(company.get("entityUrn", "").split(":")[-1] if company.get("entityUrn") else ""),
                    company_size=company_size,
                    company_tenure_start=_format_range_start(group),
                    company_tenure_end=_format_range_end(group, "Present"),
                    title=_as_text(position.get("title")),
                    employment_type=_as_text(position.get("employmentType")),
                    start_date=_format_range_start(position),
                    end_date=_format_range_end(position, "Present"),
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


def _extract_educations(profile_educations: Optional[Dict[str, Any]]) -> List[EducationRecord]:
    educations = []
    for education in (profile_educations or {}).get("elements") or []:
        school = education.get("school") or {}
        educations.append(
            EducationRecord(
                school=_as_text(school.get("name")) or _as_text(education.get("schoolName")),
                degree=_as_text(education.get("degreeName")),
                field_of_study=_as_text(education.get("fieldOfStudy")),
                start_date=_format_range_start(education),
                end_date=_format_range_end(education),
                grade=_as_text(education.get("grade")),
                activities=_as_text(education.get("activities")),
                description=_as_text(education.get("description")),
                school_linkedin_id=(education.get("schoolUrn", "").split(":")[-1] if education.get("schoolUrn") else ""),
                school_linkedin_url=_as_text(school.get("url")),
                skills=", ".join(_extract_skill_names(education.get("profileTaxonomySkills"))),
            )
        )
    return educations


def _extract_certifications(profile: Dict[str, Any]) -> List[CertificationRecord]:
    certifications = []
    possible_sections = [
        profile.get("profileCertifications"),
        profile.get("profileLicensesAndCertifications"),
        profile.get("profileLicenseAndCertifications"),
    ]
    elements = []
    for section in possible_sections:
        if isinstance(section, dict):
            elements.extend(section.get("elements") or [])

    for certification in elements:
        if not isinstance(certification, dict):
            continue
        certifications.append(
            CertificationRecord(
                name=_as_text(certification.get("name")),
                authority=_as_text(certification.get("authority")) or _as_text((certification.get("company") or {}).get("name")),
                issued_date=_format_range_start(certification) or _format_date(certification.get("issueDate")),
                expiration_date=_format_range_end(certification) or _format_date(certification.get("expirationDate")),
                credential_id=_as_text(certification.get("licenseNumber")) or _as_text(certification.get("credentialId")),
                credential_url=_as_text(certification.get("url")) or _as_text(certification.get("credentialUrl")),
                license_number=_as_text(certification.get("licenseNumber")),
                skills=", ".join(_extract_skill_names(certification.get("profileTaxonomySkills"))),
            )
        )
    return certifications


def _extract_top_skills(profile: Dict[str, Any]) -> List[SkillRecord]:
    skills = []
    possible_sections = [
        profile.get("profileTopSkills"),
        profile.get("topSkills"),
        profile.get("profileSkills"),
    ]
    elements = []
    for section in possible_sections:
        if isinstance(section, dict):
            elements.extend(section.get("elements") or [])
        elif isinstance(section, list):
            elements.extend(section)

    for item in elements:
        if not isinstance(item, dict):
            continue
        name = _as_text((item.get("skill") or {}).get("name")) or _as_text(item.get("name"))
        if not name:
            continue
        endorsement_count = item.get("endorsementCount")
        skills.append(
            SkillRecord(
                name=name,
                endorsement_count=endorsement_count if isinstance(endorsement_count, int) else None,
                source=_as_text(item.get("source")),
            )
        )
    return skills


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


def parse_profile_payload(linkedin_url: str, payload: Dict[str, Any], verbose_logging: bool) -> ProfileResult:
    profile = _extract_profile(payload)
    if not profile:
        if verbose_logging:
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
    educations_all = _extract_educations(profile.get("profileEducations"))
    certifications = _extract_certifications(profile)
    top_skills = _extract_top_skills(profile)
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
        school=_as_text((latest_education.get("school") or {}).get("name")) or _as_text(latest_education.get("schoolName")) or None,
        degree=_as_text(latest_education.get("degreeName")) or None,
        field_of_study=_as_text(latest_education.get("fieldOfStudy")) or None,
        activities=_as_text(latest_education.get("activities")) or None,
        school_linkedin_id=(latest_education.get("schoolUrn", "").split(":")[-1] if latest_education.get("schoolUrn") else None),
        school_linkedin_url=_as_text((latest_education.get("school") or {}).get("url")) or None,
        experiences=experiences,
        educations=educations_all,
        certifications=certifications,
        top_skills=top_skills,
    )
