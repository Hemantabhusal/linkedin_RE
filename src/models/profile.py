from typing import List, Optional

from pydantic import BaseModel, Field


class ExperienceRecord(BaseModel):
    company_name: str = ""
    company_linkedin_url: str = ""
    company_linkedin_id: str = ""
    company_size: str = ""
    company_tenure_start: str = ""
    company_tenure_end: str = ""
    title: str = ""
    employment_type: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    location_type: str = ""
    description: str = ""
    skills: str = ""


class ProfileResult(BaseModel):
    linkedin_url: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    username: Optional[str] = None
    sales_nav_url: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None
    location_name: Optional[str] = None
    industry: Optional[str] = None
    avatar_url: Optional[str] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    current_company_linkedin_url: Optional[str] = None
    current_company_industry: Optional[str] = None
    current_company_linkedin_id: Optional[str] = None
    current_company_employee_count_range: Optional[str] = None
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    activities: Optional[str] = None
    school_linkedin_id: Optional[str] = None
    school_linkedin_url: Optional[str] = None
    experiences: List[ExperienceRecord] = Field(default_factory=list)
