import json
from typing import Iterable, List

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
        sql = """
            INSERT INTO profile_results
              (profile_id, linkedin_url, first_name, last_name, headline, summary, username,
               sales_nav_url, country_code, country, location_name, industry, avatar_url,
               `current_role`, current_company, current_company_linkedin_url,
               current_company_industry, current_company_linkedin_id,
               current_company_employee_range, school, degree, field_of_study,
               activities, school_linkedin_id, school_linkedin_url, experiences)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              linkedin_url = VALUES(linkedin_url),
              first_name = VALUES(first_name),
              last_name = VALUES(last_name),
              headline = VALUES(headline),
              summary = VALUES(summary),
              username = VALUES(username),
              sales_nav_url = VALUES(sales_nav_url),
              country_code = VALUES(country_code),
              country = VALUES(country),
              location_name = VALUES(location_name),
              industry = VALUES(industry),
              avatar_url = VALUES(avatar_url),
              `current_role` = VALUES(`current_role`),
              current_company = VALUES(current_company),
              current_company_linkedin_url = VALUES(current_company_linkedin_url),
              current_company_industry = VALUES(current_company_industry),
              current_company_linkedin_id = VALUES(current_company_linkedin_id),
              current_company_employee_range = VALUES(current_company_employee_range),
              school = VALUES(school),
              degree = VALUES(degree),
              field_of_study = VALUES(field_of_study),
              activities = VALUES(activities),
              school_linkedin_id = VALUES(school_linkedin_id),
              school_linkedin_url = VALUES(school_linkedin_url),
              experiences = VALUES(experiences),
              scraped_at = CURRENT_TIMESTAMP
        """
        values = (
            profile_id,
            result.linkedin_url,
            result.first_name,
            result.last_name,
            result.headline,
            result.summary,
            result.username,
            result.sales_nav_url,
            result.country_code,
            result.country,
            result.location_name,
            result.industry,
            result.avatar_url,
            result.current_role,
            result.current_company,
            result.current_company_linkedin_url,
            result.current_company_industry,
            result.current_company_linkedin_id,
            result.current_company_employee_count_range,
            result.school,
            result.degree,
            result.field_of_study,
            result.activities,
            result.school_linkedin_id,
            result.school_linkedin_url,
            experiences_json,
        )
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(sql, values)
        self.connection.commit()
