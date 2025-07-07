"""
Site monitoring helpers for tickle_streamlit.

This module defines platform-specific restart logic for monitored sites.
Currently supports Streamlit-hosted apps with a wake-up button trigger.
"""

from playwright.async_api import Page
from utils.log_util import app_logger, log_site

logger = app_logger(__name__, log_file="logs/uptime.log")


def log_raw_html(html: str, site: dict, suffix: str = "raw") -> None:
    """
    Dump raw HTML content to a file for inspection and log the action.

    :param html: Raw HTML content as a string.
    :param site: Dictionary with site metadata.
    :param suffix: Suffix for filename to distinguish contexts (e.g. 'raw', 'iframe').
    :return: None
    """
    filename = f"logs/{site['name'].replace(' ', '_')}_{suffix}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    log_site("debug", logger, site, f"Dumped HTML for inspection ({suffix}).")


async def restart_site_if_needed(page: Page, site: dict, dry_run: bool = False) -> None:
    """
    Attempt to restart a site if it is hosted on a known platform.

    :param page: The Playwright page instance currently loaded.
    :param site: A dictionary containing site metadata from config.
    :param dry_run: If True, skip any restart actions.
    :return: None
    """
    if site.get("is_streamlit"):
        try:
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector("#root", timeout=10000)

            if dry_run:
                log_site("info", logger, site, "Dry run enabled — skipping wake-up.")
                return

            await page.wait_for_selector(
                'button[data-testid="wakeup-button-owner"], button[data-testid="wakeup-button-viewer"]',
                timeout=5000,
            )
            log_site("warning", logger, site, "Wake-up button found. Clicking.")
            await page.click(
                'button[data-testid="wakeup-button-owner"], button[data-testid="wakeup-button-viewer"]'
            )

        except Exception as e:
            msg = str(e).splitlines()[0]
            log_site("error", logger, site, f"Wake-up attempt failed: {msg}")
    else:
        log_site("info", logger, site, "No restart logic defined for platform.")
