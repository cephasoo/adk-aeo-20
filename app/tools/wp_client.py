import os
from urllib.parse import urlparse

def get_wp_credentials():
    """
    Returns (wp_url, wp_user, wp_pass, is_mock).
    Removes spaces from application password and flags mock mode if credentials are missing or testing.
    """
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")

    if wp_pass:
        wp_pass = wp_pass.replace(" ", "")

    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    is_mock = not wp_url or not wp_user or not wp_pass or is_testing

    return wp_url, wp_user, wp_pass, is_mock

def base_site_url(wp_url: str = None) -> str:
    """Extracts base WordPress site URL from WP_API_URL."""
    if not wp_url:
        wp_url, _, _, _ = get_wp_credentials()
    if not wp_url:
        return "http://aeo-copilot.local"
    return wp_url.split("/wp-json")[0]
