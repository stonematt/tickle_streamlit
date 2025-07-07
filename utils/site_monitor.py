"""
Site monitoring helpers for tickle_streamlit.

This module defines platform-specific restart logic for monitored sites.
Currently supports Streamlit-hosted apps with a wake-up button trigger.
"""

from playwright.async_api import Page

from utils.log_util import app_logger

logger = app_logger(__name__, log_file="logs/uptime.log")


async def restart_site_if_needed(page: Page, site: dict) -> None:
    """
    Attempt to restart a site if it is hosted on a known platform.

    :param page: The Playwright page instance currently loaded.
    :param site: A dictionary containing site metadata from config.
    :return: None
    """
    if site.get("is_streamlit"):
        try:
            await page.wait_for_selector(
                'button[data-testid="wakeup-button-owner"]', timeout=5000
            )
            logger.warning(f"{site['name']}: Wake-up button found. Clicking.")
            await page.click('button[data-testid="wakeup-button-owner"]')
        except Exception:
            logger.error(f"{site['name']}: Wake-up button not found after timeout.")
    else:
        logger.info(f"{site['name']}: No restart logic defined for platform.")
