import json
from typing import Iterable, List, Optional, Set

import mysql.connector

from config import Settings
from models import PendingProfileRow, ProfileResult


class MySQLRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            autocommit=False,
        )
        self._profile_result_columns = None  # type: Optional[Set[str]]

    def close(self) -> None:
        self.connection.close()

    def reset_stuck_profiles(self) -> int:
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("UPDATE profiles SET status = 'pending' WHERE status = 'in_progress'")
            affected = cursor.rowcount
        self.connection.commit()
        return affected

    def get_pending_profiles(self, limit: int) -> List[PendingProfileRow]:
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, linkedin_url FROM profiles WHERE status = 'pending' ORDER BY id ASC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()
        return [PendingProfileRow(**row) for row in rows]

    def _get_profile_result_columns(self) -> Set[str]:
        if self._profile_result_columns is not None:
            return self._profile_result_columns

        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("SHOW COLUMNS FROM profile_results")
            rows = cursor.fetchall()

        self._profile_result_columns = {row["Field"] for row in rows}
        return self._profile_result_columns

    def mark_in_progress(self, profile_ids: Iterable[int]) -> None:
        ids = list(profile_ids)
        if not ids:
            return
        placeholders = ", ".join(["%s"] * len(ids))
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "UPDATE profiles SET status = 'in_progress' WHERE id IN (%s)" % placeholders,
                tuple(ids),
            )
        self.connection.commit()

    def mark_done(self, profile_id: int) -> None:
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("UPDATE profiles SET status = 'done', error_msg = NULL WHERE id = %s", (profile_id,))
        self.connection.commit()

    def mark_error(self, profile_id: int, message: str) -> None:
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "UPDATE profiles SET status = 'error', error_msg = %s WHERE id = %s",
                (message[:500], profile_id),
            )
        self.connection.commit()

    def save_result(self, profile_id: int, result: ProfileResult) -> None:
        experiences_json = json.dumps(
            [experience.model_dump() for experience in result.experiences],
            ensure_ascii=False,
        )
        educations_json = json.dumps([education.model_dump() for education in result.educations], ensure_ascii=False)
        certifications_json = json.dumps(
            [certification.model_dump() for certification in result.certifications],
            ensure_ascii=False,
        )
        top_skills_json = json.dumps([skill.model_dump() for skill in result.top_skills], ensure_ascii=False)

        values_by_column = {
            "profile_id": profile_id,
            "linkedin_url": result.linkedin_url,
            "first_name": result.first_name,
            "last_name": result.last_name,
            "headline": result.headline,
            "summary": result.summary,
            "username": result.username,
            "sales_nav_url": result.sales_nav_url,
            "country_code": result.country_code,
            "country": result.country,
            "location_name": result.location_name,
            "industry": result.industry,
            "avatar_url": result.avatar_url,
            "current_role": result.current_role,
            "current_company": result.current_company,
            "current_company_linkedin_url": result.current_company_linkedin_url,
            "current_company_industry": result.current_company_industry,
            "current_company_linkedin_id": result.current_company_linkedin_id,
            "current_company_employee_range": result.current_company_employee_count_range,
            "school": result.school,
            "degree": result.degree,
            "field_of_study": result.field_of_study,
            "activities": result.activities,
            "school_linkedin_id": result.school_linkedin_id,
            "school_linkedin_url": result.school_linkedin_url,
            "experiences": experiences_json,
            "educations": educations_json,
            "certifications": certifications_json,
            "top_skills": top_skills_json,
        }
        available_columns = self._get_profile_result_columns()
        columns = [column for column in values_by_column if column in available_columns]
        quoted_columns = ["`%s`" % column if column == "current_role" else column for column in columns]
        placeholders = ", ".join(["%s"] * len(columns))
        update_columns = [column for column in columns if column not in ("profile_id",)]
        update_assignments = ",\n              ".join(
            "%s = VALUES(%s)"
            % (
                "`%s`" % column if column == "current_role" else column,
                "`%s`" % column if column == "current_role" else column,
            )
            for column in update_columns
        )
        sql = """
            INSERT INTO profile_results
              (%s)
            VALUES
              (%s)
            ON DUPLICATE KEY UPDATE
              %s,
              scraped_at = CURRENT_TIMESTAMP
        """ % (", ".join(quoted_columns), placeholders, update_assignments)
        values = tuple(values_by_column[column] for column in columns)
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(sql, values)
        self.connection.commit()
