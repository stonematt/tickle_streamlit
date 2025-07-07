"""
Monitors the uptime of configured sites and restarts them if necessary.

This script is intended to be run on a schedule to ensure key web apps remain
responsive. For Streamlit-hosted apps, a wake-up button is automatically
clicked if the app is sleeping.
"""

import asyncio
import os
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from utils.config_loader import load_and_validate_config
from utils.log_util import app_logger, log_site
from utils.site_monitor import restart_site_if_needed

logger = app_logger(__name__, log_file="logs/uptime.log")

CONFIG_PATH = "config/sites.json"


def is_valid_url(url: str) -> bool:
    """
    Validate a URL string for presence of scheme and hostname.

    :param url: The URL to validate.
    :return: True if valid, else False.
    """
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


async def check_site(playwright, site):
    """
    Load the site URL in a browser and determine if it's up based on expected content.
    Attempt restart logic if applicable.

    :param playwright: The Playwright context manager.
    :param site: Dictionary with config metadata for the site.
    :return: None
    """
    browser = await playwright.chromium.launch()
    page = await browser.new_page()

    if not is_valid_url(site["url"]):
        log_site("error", logger, site, f"Invalid URL '{site['url']}' — skipping.")
        return

    try:
        log_site("info", logger, site, f"Checking {site['name']} at {site['url']}")
        await page.goto(site["url"], timeout=15000)

        # Use iframe for Streamlit apps if present, fallback to main frame otherwise
        frame = page.frame(name="streamlitApp") or page.main_frame()
        content = await frame.content()
        needle = site["must_contain"]

        if needle in content:
            log_site("info", logger, site, f"Found '{needle}'. Site is up.")
        else:
            log_site("warning", logger, site, f"Not found: '{needle}'")
            await restart_site_if_needed(page, site)

    except Exception as e:
        msg = str(e).splitlines()[0]
        log_site("error", logger, site, f"check failed: {msg}")

    finally:
        await browser.close()


async def main():
    """
    Loads site configuration and concurrently checks each site's availability.

    :return: None
    """
    sites = load_and_validate_config(CONFIG_PATH)

    async with async_playwright() as playwright:
        tasks = [check_site(playwright, site) for site in sites]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
