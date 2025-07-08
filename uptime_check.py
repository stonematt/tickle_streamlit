"""
Monitors the uptime of configured sites and restarts them if necessary.

This script is intended to be run on a schedule to ensure key web apps remain
responsive. For Streamlit-hosted apps, a wake-up button is automatically
clicked if the app is sleeping.
"""

import argparse
import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from utils.config_loader import load_and_validate_config
from utils.log_util import app_logger, log_site
from utils.site_monitor import restart_site_if_needed, log_raw_html

logger = app_logger(__name__, log_file="logs/uptime.log")

CONFIG_PATH = "config/sites.json"

parser = argparse.ArgumentParser(description="Check site uptime.")
parser.add_argument(
    "--dry-run", action="store_true", help="Only check content, do not restart."
)
parser.add_argument(
    "--site", help="Only check the specified site by name (matches 'name' in config)"
)
args = parser.parse_args()


def is_valid_url(url: str) -> bool:
    """
    Validate a URL string for presence of scheme and hostname.

    :param url: The URL to validate.
    :return: True if valid, else False.
    """
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


async def evaluate_iframe_content(page, site, dry_run=False):
    """
    Evaluate iframe content to determine if site is up. Restart if content missing.

    :param page: The Playwright page object.
    :param site: Dictionary with site metadata.
    :param dry_run: Passed to downstream restart logic only.
    :return: One of 'up', 'down', or 'restarted'
    """
    iframe_element = await page.query_selector('iframe[title="streamlitApp"]')

    if not iframe_element:
        log_site("info", logger, site, "No iframe found — attempting restart")
        if site.get("log_raw"):
            try:
                html = await page.content()
                log_raw_html(html, site, suffix="raw_iframe")
            except Exception as dump_err:
                log_site(
                    "warning", logger, site, f"failed to dump page HTML: {dump_err}"
                )
        return await restart_site_if_needed(page, site, dry_run=dry_run)

    try:
        frame = await iframe_element.content_frame()
        await frame.wait_for_load_state("networkidle")

        content = await frame.content()
        if site.get("log_raw"):
            log_raw_html(content, site, suffix="iframe")

        needle = site["must_contain"]
        if needle in content:
            log_site("info", logger, site, f"Found '{needle}'. Site is up.")
            return "up"

        log_site("warning", logger, site, f"Not found: '{needle}'. Site is down.")
        return "down"

    except Exception as e:
        msg = str(e).splitlines()[0]
        log_site("warning", logger, site, f"Iframe load or content check failed: {msg}")
        if site.get("log_raw"):
            try:
                html = await page.content()
                log_raw_html(html, site, suffix="raw_iframe")
            except Exception as dump_err:
                log_site(
                    "warning", logger, site, f"failed to dump page HTML: {dump_err}"
                )
        return "down"


async def check_site(playwright, site, dry_run=False):
    """
    Load the site URL in a browser and determine if it's up based on expected content.
    Attempt restart logic if applicable.

    :param playwright: The Playwright context manager.
    :param site: Dictionary with config metadata for the site.
    :param dry_run: If True, skips any restart logic.
    :return: Dict containing the final status.
    """
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    assert callable(page.frame), "page.frame has been overwritten or misused"

    result = {"name": site["name"], "status": "unknown"}

    if not is_valid_url(site["url"]):
        log_site("error", logger, site, f"Invalid URL '{site['url']}' — skipping.")
        result["status"] = "invalid"
        return result

    try:
        log_site("info", logger, site, f"Checking {site['name']} at {site['url']}")
        await page.goto(site["url"], timeout=15000)

        # Delegate to iframe logic
        result["status"] = await evaluate_iframe_content(page, site, dry_run=dry_run)

    except Exception as e:
        msg = str(e).splitlines()[0]
        log_site("error", logger, site, f"check failed: {msg}")
        if site.get("log_raw"):
            try:
                html = await page.content()
                log_raw_html(html, site, suffix="raw_timeout")
            except Exception as dump_err:
                log_site(
                    "warning", logger, site, f"failed to dump raw HTML: {dump_err}"
                )
        result["status"] = "error"

    finally:
        await browser.close()
        return result


def write_uptime_report(results, log_path="logs/uptime_report.log"):
    """
    Append a timestamped summary of site statuses to a report log.

    :param results: List of dicts with 'name' and 'status' keys.
    :param log_path: File path to write the report entry.
    :return: None
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as report:
        for result in results:
            report.write(f"{timestamp},{result['name']},{result['status']}\n")


async def main():
    """
    Loads site configuration and concurrently checks each site's availability.

    :return: None
    """
    sites = load_and_validate_config(CONFIG_PATH)

    if args.site:
        valid_names = [s["name"] for s in sites]
        sites = [s for s in sites if s["name"] == args.site]
        if not sites:
            logger.error(
                f"'{args.site}' not found. Valid site names are: {valid_names}"
            )
            return

    async with async_playwright() as playwright:
        tasks = [check_site(playwright, site, dry_run=args.dry_run) for site in sites]
        results = await asyncio.gather(*tasks)
        write_uptime_report(results)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
