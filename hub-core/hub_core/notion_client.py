"""
Notion API Client — Fetch data from Notion databases

Usage:
    from hub_core.notion_client import get_notion_pages
    pages = get_notion_pages()
"""

import os
from typing import List, Dict, Any
import logging

import requests

logger = logging.getLogger(__name__)

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


def get_notion_pages(
    *, api_key: str | None = None, database_id: str | None = None
) -> List[Dict[str, Any]]:
    """
    Fetch all pages from Notion database.

    Returns: List of page objects with title, properties, created_time
    """
    api_key = api_key or os.getenv("NOTION_API_KEY")
    database_id = database_id or os.getenv("NOTION_DATABASE_ID")
    if not api_key or not database_id:
        logger.error("Notion credentials missing: NOTION_API_KEY or NOTION_DATABASE_ID")
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }

    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"

    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()
        data = response.json()

        pages = []
        for result in data.get("results", []):
            page_data = {
                "id": result.get("id"),
                "created_time": result.get("created_time"),
                "last_edited_time": result.get("last_edited_time"),
                "properties": result.get("properties", {}),
                "archived": result.get("archived", False),
                "url": result.get("url"),
            }
            pages.append(page_data)

        logger.info(f"Fetched {len(pages)} pages from Notion")
        return pages

    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API error: {e}")
        return []


def get_page_title(page: Dict[str, Any]) -> str:
    """Extract title from page properties (handles Title property)"""
    props = page.get("properties", {})

    # Look for Title property
    for prop_name, prop_value in props.items():
        if prop_value.get("type") == "title":
            titles = prop_value.get("title", [])
            if titles:
                return titles[0].get("plain_text", "Untitled")

    return "Untitled"


def get_page_property(page: Dict[str, Any], prop_name: str) -> str:
    """Extract property value from page"""
    props = page.get("properties", {})
    prop = props.get(prop_name, {})

    prop_type = prop.get("type")

    if prop_type == "rich_text":
        texts = prop.get("rich_text", [])
        return " ".join([t.get("plain_text", "") for t in texts])

    elif prop_type == "select":
        option = prop.get("select")
        return option.get("name", "") if option else ""

    elif prop_type == "checkbox":
        return "✓" if prop.get("checkbox") else "○"

    elif prop_type == "date":
        date_obj = prop.get("date")
        return date_obj.get("start", "") if date_obj else ""

    elif prop_type == "number":
        return str(prop.get("number", ""))

    else:
        return ""


def format_pages_for_display(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format pages for UI display"""
    formatted = []

    for page in pages:
        if page.get("archived"):
            continue

        title = get_page_title(page)

        formatted.append(
            {
                "id": page["id"],
                "title": title,
                "url": page["url"],
                "created": page.get("created_time", ""),
                "edited": page.get("last_edited_time", ""),
                "properties": page.get("properties", {}),
            }
        )

    return formatted
