from http.cookies import SimpleCookie
from typing import Dict, Optional

from curl_cffi import requests as curl_requests

from config import Settings
from logging_setup import get_logger
from models import ProfileResult
from parser.linkedin import parse_profile_payload
from utils import RetryableRateLimitError, SessionExpiredError


LOGGER = get_logger(__name__)
LINKEDIN_BASE = "https://www.linkedin.com"


class LinkedInClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session = curl_requests.Session(
            impersonate=settings.linkedin_impersonate,
            timeout=settings.request_timeout_seconds,
        )
        self._headers = {}  # type: Dict[str, str]

    def _sanitize_cookie_string(self, cookie_string: str) -> str:
        parts = []
        for pair in cookie_string.split(";"):
            item = pair.strip()
            if not item:
                continue
            if any(ord(char) > 127 for char in item):
                continue
            if item.startswith("JSESSIONID="):
                continue
            parts.append(item)
        return "; ".join(parts)

    def _extract_retry_after_seconds(self, response: curl_requests.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return 0.0
        try:
            return float(retry_after)
        except ValueError:
            return 0.0

    def _ensure_ok(self, response: curl_requests.Response, context: str) -> None:
        if response.status_code in (401, 403):
            raise SessionExpiredError("%s returned %s" % (context, response.status_code))
        if response.status_code == 429:
            raise RetryableRateLimitError(
                "%s returned 429" % context,
                retry_after_seconds=self._extract_retry_after_seconds(response),
            )
        if response.status_code >= 400:
            sample = response.text[:400].replace("\n", " ")
            raise RuntimeError("%s returned %s: %s" % (context, response.status_code, sample))

    def _fetch_fresh_jsession_id(self, base_cookie_string: str) -> str:
        response = self._session.get(
            "%s/uas/authenticate" % LINKEDIN_BASE,
            headers={
                "User-Agent": self.settings.linkedin_user_agent,
                "Accept": "*/*",
                "Cookie": base_cookie_string,
            },
        )
        self._ensure_ok(response, "/uas/authenticate")

        jsession_id = response.cookies.get("JSESSIONID")
        if not jsession_id:
            set_cookie_headers = response.headers.get("set-cookie", "")
            if set_cookie_headers:
                cookie = SimpleCookie()
                cookie.load(set_cookie_headers)
                morsel = cookie.get("JSESSIONID")
                if morsel:
                    jsession_id = morsel.value

        if not jsession_id:
            raise RuntimeError("Could not obtain JSESSIONID from /uas/authenticate")

        return jsession_id.replace('"', "")

    def verify_session(self) -> None:
        base_cookie_string = self._sanitize_cookie_string(self.settings.linkedin_cookies)
        jsession_id = self._fetch_fresh_jsession_id(base_cookie_string)
        final_cookie_string = "%s; JSESSIONID=\"%s\"" % (base_cookie_string, jsession_id)

        self._headers = {
            "User-Agent": self.settings.linkedin_user_agent,
            "csrf-token": jsession_id,
            "Cookie": final_cookie_string,
        }

        response = self._session.get(
            "%s/voyager/api/me" % LINKEDIN_BASE,
            headers=self._headers,
        )
        self._ensure_ok(response, "/voyager/api/me")
        LOGGER.debug("Session verification payload keys=%s", list(response.json().keys())[:8])

    def scrape_profile(self, linkedin_url: str) -> ProfileResult:
        slug = self._extract_slug(linkedin_url)
        api_url = (
            "%s/voyager/api/identity/dash/profiles"
            "?q=memberIdentity&memberIdentity=%s"
            "&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-101"
            "&count=100"
        ) % (LINKEDIN_BASE, slug)

        LOGGER.debug("Profile request url=%s", api_url)
        response = self._session.get(api_url, headers=self._headers)
        self._ensure_ok(response, "profile request")
        payload = response.json()
        LOGGER.debug("Profile response status=%s keys=%s", response.status_code, list(payload.keys())[:8])
        return parse_profile_payload(linkedin_url, payload, self.settings.verbose_logging)

    @staticmethod
    def _extract_slug(linkedin_url: str) -> str:
        marker = "/in/"
        if marker not in linkedin_url:
            raise ValueError("Invalid LinkedIn profile URL: %s" % linkedin_url)
        slug = linkedin_url.split(marker, 1)[1].split("?", 1)[0].split("#", 1)[0].strip("/")
        if not slug:
            raise ValueError("Invalid LinkedIn profile URL: %s" % linkedin_url)
        return slug
