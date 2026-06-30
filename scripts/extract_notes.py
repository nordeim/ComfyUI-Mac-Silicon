#!/usr/bin/env python3
"""Extract clean text from page_reader JSON outputs and produce consolidated notes."""
import json
import os
import re
from pathlib import Path

PAGES_DIR = Path("/home/z/my-project/research/pages")
OUT_DIR = Path("/home/z/my-project/research/notes")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_html(html: str) -> str:
    """Strip HTML tags, collapse whitespace."""
    # Remove scripts/styles
    html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.I)
    html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.I)
    # Replace br/p with newlines
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    html = re.sub(r'</p>', '\n\n', html, flags=re.I)
    html = re.sub(r'</h[1-6]>', '\n\n', html, flags=re.I)
    html = re.sub(r'</li>', '\n', html, flags=re.I)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()

for json_path in sorted(PAGES_DIR.glob("*.json")):
    key = json_path.stem
    try:
        with open(json_path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"PARSE FAIL {key}: {e}")
        continue
    
    # The page_reader returns either {data: {title, html, ...}} or {title, html, ...}
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            d = data["data"]
        else:
            d = data
        title = d.get("title", "(no title)")
        html = d.get("html") or d.get("content") or ""
        url = d.get("url", "")
        publish_time = d.get("publishedTime") or d.get("publish_time") or ""
        
        text = clean_html(html) if html else ""
        # Truncate to first 12k chars to keep notes manageable
        if len(text) > 15000:
            text = text[:15000] + "\n\n... [truncated] ..."
        
        out_path = OUT_DIR / f"{key}.txt"
        with open(out_path, "w") as f:
            f.write(f"# {title}\n# URL: {url}\n# Published: {publish_time}\n\n{text}\n")
        print(f"OK {key}: {len(text)} chars → {out_path.name}")
    else:
        print(f"UNEXPECTED {key}: type={type(data).__name__}")

print("\n=== All notes extracted ===")
