from linkedin_profile_scraper_python.client import LinkedInClient
from linkedin_profile_scraper_python.models import ProfileResult


class ProfileScraper:
    def __init__(self, client: LinkedInClient) -> None:
        self.client = client

    def scrape(self, linkedin_url: str) -> ProfileResult:
        return self.client.scrape_profile(linkedin_url)

