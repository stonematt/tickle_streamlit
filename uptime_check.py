import asyncio
import json
import os
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from utils.config_loader import load_and_validate_config
from utils.log_util import app_logger
from utils.site_monitor import restart_site_if_needed

logger = app_logger(__name__, log_file="logs/uptime.log")

CONFIG_PATH = "config/sites.json"


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


async def check_site(playwright, site):
    browser = await playwright.chromium.launch()
    page = await browser.new_page()

    if not is_valid_url(site["url"]):
        logger.error(f"{site['name']}: Invalid URL '{site['url']}' — skipping.")
        return

    try:
        logger.info(f"Checking {site['name']} at {site['url']}")
        await page.goto(site["url"], timeout=15000)

        content = await page.content()
        if site["must_contain"] in content:
            logger.info(
                f"{site['name']}: Page contains '{site['must_contain']}'. Site is up."
            )
        elif site.get("is_streamlit"):
            await restart_site_if_needed(page, site)

    except Exception as e:
        msg = str(e).splitlines()[0]
        logger.error(f"{site['name']} check failed: {msg}")

    finally:
        await browser.close()


async def main():
    sites = load_and_validate_config(CONFIG_PATH)

    async with async_playwright() as playwright:
        tasks = [check_site(playwright, site) for site in sites]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
