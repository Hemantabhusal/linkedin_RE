from client import LinkedInClient
from models import ProfileResult


class ProfileScraper:
    def __init__(self, client: LinkedInClient) -> None:
        self.client = client

    def scrape(self, linkedin_url: str) -> ProfileResult:
        return self.client.scrape_profile(linkedin_url)
