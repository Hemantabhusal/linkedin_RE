from client import LinkedInClient
from config import get_settings
from logging_setup import configure_logging, get_logger
from scraper import ProfileScraper
from storage import MySQLRepository
from utils import SessionExpiredError, sleep_between, with_retry


LOGGER = get_logger(__name__)


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level, verbose=settings.verbose_logging)

    LOGGER.info("Connecting to MySQL...")
    repository = MySQLRepository(settings)
    LOGGER.info("MySQL connected.")

    try:
        client = LinkedInClient(settings)
        LOGGER.info("Verifying LinkedIn session...")
        client.verify_session()
        LOGGER.info("LinkedIn session verified.")
        LOGGER.info("Using fixed user-agent: %s", settings.linkedin_user_agent)

        scraper = ProfileScraper(client)

        reset_count = repository.reset_stuck_profiles()
        if reset_count:
            LOGGER.warning("Reset %s stuck in_progress profile(s) back to pending.", reset_count)

        total_processed = 0
        while True:
            profiles = repository.get_pending_profiles(settings.batch_size)
            if not profiles:
                LOGGER.info("No more pending profiles. Total processed: %s", total_processed)
                break

            repository.mark_in_progress([row.id for row in profiles])

            for index, row in enumerate(profiles, start=1):
                LOGGER.info("[%s] Scraping: %s", total_processed + 1, row.linkedin_url)
                try:
                    result = with_retry(
                        lambda: scraper.scrape(row.linkedin_url),
                        max_attempts=settings.max_retries,
                        rate_limit_delay_seconds=settings.rate_limit_cooldown_ms / 1000.0,
                    )
                    repository.save_result(row.id, result)
                    repository.mark_done(row.id)
                    LOGGER.info("  Done: %s %s", result.first_name or "", result.last_name or "")
                except SessionExpiredError as exc:
                    repository.mark_error(row.id, str(exc))
                    LOGGER.error("Session expired: %s", exc)
                    return 1
                except Exception as exc:  # noqa: BLE001
                    repository.mark_error(row.id, str(exc))
                    LOGGER.error("  Error while scraping %s: %s", row.linkedin_url, exc)

                total_processed += 1
                if index < len(profiles):
                    sleep_between(settings.scrape_delay_min_ms, settings.scrape_delay_max_ms)

        return 0
    finally:
        repository.close()
