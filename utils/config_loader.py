"""
Configuration loader and schema validator for tickle_streamlit.

This module ensures all site config entries conform to required structure.
"""

import json
from urllib.parse import urlparse

from utils.log_util import app_logger

logger = app_logger(__name__, log_file="logs/uptime.log")

REQUIRED_KEYS = ["name", "url", "selector", "is_streamlit"]
OPTIONAL_KEYS = ["must_contain"]


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme in ("http", "https"), parsed.netloc])


def load_and_validate_config(path: str = "config/sites.json") -> list[dict]:
    """
    Load site config and validate schema for each entry.

    :param path: Path to sites.json config
    :return: List of valid site dictionaries
    """
    with open(path, "r") as f:
        data = json.load(f)

    valid_sites = []
    for site in data:
        if not all(k in site for k in REQUIRED_KEYS):
            logger.error(f"Skipping site: missing required keys — {site}")
            continue
        if not isinstance(site["is_streamlit"], bool):
            logger.error(f"{site['name']}: 'is_streamlit' must be true/false.")
            continue
        if not is_valid_url(site["url"]):
            logger.error(f"{site['name']}: Invalid URL — {site['url']}")
            continue
        valid_sites.append(site)

    logger.info(f"Loaded {len(valid_sites)} valid site(s) from config.")
    return valid_sites
