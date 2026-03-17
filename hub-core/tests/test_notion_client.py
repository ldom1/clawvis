#!/usr/bin/env python3
"""Tests for Notion client helpers."""

from hub_core.notion_client import get_page_title, get_page_property, format_pages_for_display


def test_get_page_title_with_title_property():
    page = {
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "Hello"}],
            }
        }
    }
    assert get_page_title(page) == "Hello"


def test_get_page_property_variants():
    page = {
        "properties": {
            "Rich": {"type": "rich_text", "rich_text": [{"plain_text": "A"}, {"plain_text": "B"}]},
            "Select": {"type": "select", "select": {"name": "X"}},
            "Checkbox": {"type": "checkbox", "checkbox": True},
            "Date": {"type": "date", "date": {"start": "2024-01-01"}},
            "Number": {"type": "number", "number": 42},
        }
    }
    assert get_page_property(page, "Rich") == "A B"
    assert get_page_property(page, "Select") == "X"
    assert get_page_property(page, "Checkbox") == "✓"
    assert get_page_property(page, "Date") == "2024-01-01"
    assert get_page_property(page, "Number") == "42"


def test_format_pages_for_display_skips_archived_and_maps_fields():
    pages = [
        {
            "id": "1",
            "created_time": "c",
            "last_edited_time": "e",
            "archived": False,
            "url": "u",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Title"}],
                }
            },
        },
        {"id": "2", "archived": True},
    ]
    out = format_pages_for_display(pages)
    assert len(out) == 1
    item = out[0]
    assert item["id"] == "1"
    assert item["title"] == "Title"
    assert item["url"] == "u"
    assert item["created"] == "c"
    assert item["edited"] == "e"

