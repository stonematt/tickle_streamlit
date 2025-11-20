"""
Core monitoring functionality for tickle_streamlit.

Extracted from uptime_check.py to provide a clean API for the CLI.
"""

import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from utils.config_loader import load_and_validate_config
from utils.log_util import app_logger, log_site
from utils.site_monitor import restart_site_if_needed, log_raw_html

logger = app_logger(__name__, log_file="logs/uptime.log")


def is_valid_url(url: str) -> bool:
    """Validate a URL string for presence of scheme and hostname."""
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


async def evaluate_iframe_content(page, site, dry_run=False):
    """Evaluate iframe content to determine if site is up. Restart if content missing."""
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
        restart_result = await restart_site_if_needed(page, site, dry_run=dry_run)
        
        # If wake-up was attempted, re-check for iframe
        if restart_result == "restarted" and not dry_run:
            log_site("info", logger, site, "Re-checking site after wake-up attempt...")
            await page.wait_for_timeout(3000)  # Wait for site to reload
            
            # Try to find iframe again
            iframe_element = await page.query_selector('iframe[title="streamlitApp"]')
            if iframe_element:
                try:
                    frame = await iframe_element.content_frame()
                    await frame.wait_for_load_state("networkidle")
                    content = await frame.content()
                    if site.get("log_raw"):
                        log_raw_html(content, site, suffix="iframe_after_wakeup")
                    
                    needle = site["must_contain"]
                    if needle in content:
                        log_site("info", logger, site, f"Wake-up successful! Found '{needle}'.")
                        return "up"
                    else:
                        log_site("warning", logger, site, f"Wake-up attempted but content still missing: '{needle}'.")
                        return "down"
                except Exception as e:
                    msg = str(e).splitlines()[0]
                    log_site("warning", logger, site, f"Post-wake-up iframe check failed: {msg}")
                    return "down"
            else:
                log_site("warning", logger, site, "Wake-up attempted but iframe still not found.")
                return "down"
        
        return restart_result

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
    """Load the site URL in a browser and determine if it's up based on expected content."""
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
        
        # Wait for page to fully load and dynamic content
        await page.wait_for_load_state("networkidle", timeout=10000)
        await page.wait_for_timeout(3000)  # Extra wait for Streamlit to render

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
    """Append a timestamped summary of site statuses to a report log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as report:
        for result in results:
            report.write(f"{timestamp},{result['name']},{result['status']}\n")


async def check_sites(config_path: str = "config/sites.json", site_name: str = None, dry_run: bool = False):
    """
    Check site availability for all configured sites or a specific site.
    
    :param config_path: Path to sites configuration file
    :param site_name: Optional specific site name to check
    :param dry_run: If True, skips any restart logic
    :return: List of result dictionaries with 'name' and 'status' keys
    """
    sites = load_and_validate_config(config_path)

    if site_name:
        valid_names = [s["name"] for s in sites]
        sites = [s for s in sites if s["name"] == site_name]
        if not sites:
            logger.error(
                f"'{site_name}' not found. Valid site names are: {valid_names}"
            )
            return []

    async with async_playwright() as playwright:
        tasks = [check_site(playwright, site, dry_run=dry_run) for site in sites]
        results = await asyncio.gather(*tasks)
        write_uptime_report(results)
        return results


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    
    # For backward compatibility, allow running as script
    import argparse
    
    parser = argparse.ArgumentParser(description="Check site uptime.")
    parser.add_argument("--dry-run", action="store_true", help="Only check content, do not restart.")
    parser.add_argument("--site", help="Only check the specified site by name")
    parser.add_argument("--config", default="config/sites.json", help="Path to config file")
    
    args = parser.parse_args()
    
    results = asyncio.run(check_sites(args.config, args.site, args.dry_run))
    
    # Print summary
    print("\nCheck Results:")
    print("-" * 40)
    for result in results:
        status_symbol = {
            "up": "✅",
            "down": "❌", 
            "restarted": "🔄",
            "error": "⚠️",
            "invalid": "❓",
            "dry_run": "🔍"
        }.get(result["status"], "❓")
        
        print(f"{status_symbol} {result['name']:<20} {result['status']}")