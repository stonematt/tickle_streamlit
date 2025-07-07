import asyncio
import json
import os

from playwright.async_api import async_playwright
from utils.site_monitor import restart_site_if_needed

from utils.log_util import app_logger

logger = app_logger(__name__, log_file="logs/uptime.log")

CONFIG_PATH = "config/sites.json"


async def check_site(playwright, site):
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
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
        logger.error(f"{site['name']} check failed: {e}")
    finally:
        await browser.close()


async def main():
    with open(CONFIG_PATH, "r") as f:
        sites = json.load(f)

    async with async_playwright() as playwright:
        tasks = [check_site(playwright, site) for site in sites]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
