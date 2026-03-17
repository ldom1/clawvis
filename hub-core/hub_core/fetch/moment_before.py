"""
Fetch historical event from Wikipedia 'On This Day'.
Generates dated .md file for TRMNL display + historical archive.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from loguru import logger

from hub_core.config import LAB_DIR


def fetch_wikipedia_event() -> dict:
    """
    Fetch most impactful historical event from Wikipedia 'On This Day'.
    Returns dict with year, event, and file path.
    """
    today = datetime.now()
    lab_dir = LAB_DIR
    
    # Create output directory
    moment_dir = lab_dir / "hub" / "public" / "moment-before"
    moment_dir.mkdir(parents=True, exist_ok=True)
    
    # Filename with date for historical archive
    date_str = today.strftime("%Y-%m-%d")
    moment_file = moment_dir / f"{date_str}.md"
    
    year = today.strftime("%Y")
    event_text = "Today's history awaits your curiosity"
    source = "Automatic generation (fallback)"
    
    try:
        # Fetch Wikipedia "On This Day"
        url = "https://en.wikipedia.org/wiki/Wikipedia:On_this_day/Today"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Lab/1.0)"}
        
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        html = response.text
        
        # Extract events from <dl> sections using regex
        # Pattern: <dt>year</dt><dd>event text</dd>
        pattern = r"<dt>(\d{4})</dt>\s*<dd[^>]*>([^<]+(?:<[^>]+>[^<]*)*)</dd>"
        matches = re.findall(pattern, html)
        
        if matches:
            # Get first impactful event (usually most recent/significant)
            for match_year, event_html in matches[:3]:
                # Clean HTML tags
                clean_event = re.sub(r"<[^>]+>", "", event_html).strip()
                # Remove excessive whitespace
                clean_event = re.sub(r"\s+", " ", clean_event)[:180]
                
                if len(clean_event) > 20:
                    year = match_year
                    event_text = clean_event
                    source = "Wikipedia On This Day"
                    logger.info(f"✅ Moment Before fetched: {year} — {event_text[:50]}...")
                    break
        else:
            logger.warning("⚠️ Could not parse Wikipedia events, using fallback")
    
    except requests.exceptions.Timeout:
        logger.warning("⚠️ Wikipedia timeout, using fallback")
    except requests.exceptions.RequestException as e:
        logger.error(f"⚠️ Error fetching Wikipedia: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in moment_before: {e}")
    
    # Always write the file (with actual data or fallback)
    file_content = f"""# Moment Before — {date_str}

## {year}: Historical Event

**{event_text}**

---
*Source: {source}*
"""
    
    moment_file.write_text(file_content)
    logger.info(f"✅ Moment Before file created: {moment_file}")
    
    return {
        "year": year,
        "event": event_text,
        "file": f"/moment-before/{date_str}.md",
        "source": source
    }


if __name__ == "__main__":
    # Test standalone
    result = fetch_wikipedia_event()
    print(f"\n✅ Moment Before:")
    print(f"   Year: {result['year']}")
    print(f"   Event: {result['event']}")
    print(f"   File: {result['file']}")
