from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


FEED_URL = "https://www.neusenews.com/index?format=rss"
BRAND_FEEDS = {
    "neuse-news": "https://www.neusenews.com/index?format=rss",
    "nc-political-news": "https://www.ncpoliticalnews.com/news?format=rss",
    "nc-business-desk": "https://www.ncbusinessdesk.com/news?format=rss",
    "local-art-beat": "https://www.localartbeat.com/feed/",
}
MEDIA_NS = "{http://www.rssboard.org/media-rss}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def clean_html_text(html: str) -> str:
    parser = TextExtractor()
    parser.feed(unescape(html or ""))
    text = " ".join(parser.parts)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"The post .+ appeared first on .+\\.", "", text)
    return text.strip()


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Local Voice Engine/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or "story"


def text_of(parent: ET.Element, tag: str) -> str:
    child = parent.find(tag)
    return (child.text or "").strip() if child is not None else ""


def first_image_from_html(html: str) -> str:
    match = re.search(r'<img[^>]+(?:data-image|src)=["\']([^"\']+)["\']', html)
    return unescape(match.group(1)) if match else ""


def parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall("./channel/item"):
        title = text_of(item, "title")
        link = text_of(item, "link")
        description = text_of(item, "description")
        creator = text_of(item, f"{DC_NS}creator")
        encoded = text_of(item, f"{CONTENT_NS}encoded")
        image_url = ""
        media = item.find(f"{MEDIA_NS}content")
        if media is not None:
            image_url = media.attrib.get("url", "")
        enclosure = item.find("enclosure")
        if not image_url and enclosure is not None:
            image_url = enclosure.attrib.get("url", "")
        if not image_url:
            image_url = first_image_from_html(encoded)
        categories = [category.text or "" for category in item.findall("category")]
        items.append(
            {
                "title": title,
                "link": link,
                "description": re.sub(r"\s+", " ", description).strip(),
                "creator": creator,
                "categories": categories,
                "image_url": image_url,
                "pub_date": text_of(item, "pubDate"),
                "body": clean_html_text(encoded),
            }
        )
    return items


def choose_format(item: dict, brand_id: str = "neuse-news") -> str:
    if brand_id == "local-art-beat":
        return "Featured story"
    if brand_id in {"nc-political-news", "nc-business-desk"}:
        return "News story"
    title = item.get("title", "").lower()
    categories = " ".join(item.get("categories", [])).lower()
    text = f"{title} {categories}"
    if any(word in text for word in ["police", "sheriff", "arrest", "charges", "traffic stop", "crime"]):
        return "Crime story"
    if any(word in text for word in ["commissioners", "council", "board", "hearing", "grant"]):
        return "Meeting in a minute"
    if any(word in text for word in ["corporations", "land transfers", "inspections"]):
        return "Public records roundup"
    if any(word in text for word in ["spotlight", "named", "principal"]):
        return "Featured story"
    if any(word in text for word in ["open", "restaurant", "business"]):
        return "New and coming soon"
    return "News story"


def infer_county(item: dict, brand_id: str = "neuse-news") -> str:
    combined = " ".join(
        [
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("categories", [])),
        ]
    ).lower()
    if "greene" in combined:
        return "Greene County"
    if "jones" in combined:
        return "Jones County"
    if brand_id in {"nc-political-news", "nc-business-desk"}:
        return "North Carolina"
    return "Lenoir County"


def package_from_item(item: dict, brand_id: str = "neuse-news") -> dict:
    title = item.get("title", "Local update")
    description = item.get("description", "")
    format_name = choose_format(item, brand_id)
    county = infer_county(item, brand_id)
    package_id = f"{brand_id}-{item.get('pub_date', '')[:16].replace(',', '').replace(' ', '-').lower()}-{slugify(title)}"
    package_id = re.sub(r"-+", "-", package_id).strip("-") or slugify(title)
    return {
        "id": package_id,
        "headline": title,
        "county": county,
        "format": format_name,
        "status": "idea",
        "priority": "medium",
        "brand_id": brand_id,
        "source_url": item.get("link", ""),
        "pub_date": item.get("pub_date", ""),
        "rss_image_url": item.get("image_url", ""),
        "background_asset": "",
        "body": item.get("body", ""),
        "hook": description or title,
        "next_step": "Review script and confirm story image before publishing.",
        "visuals": ["story image", "context card", "caption card", "branded end card"],
        "platforms": ["Facebook Reels", "Instagram Reels", "TikTok"],
    }


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def merge_feed(data_path: Path, limit: int = 10, feed_url: str = FEED_URL, brand_id: str = "neuse-news") -> int:
    items = parse_feed(fetch_text(feed_url))[:limit]
    existing = load_json(data_path)
    by_link = {
        package.get("source_url"): package
        for package in existing
        if package.get("source_url") and (package.get("brand_id") or "neuse-news") == brand_id
    }
    by_title = {
        package.get("headline", "").lower(): package
        for package in existing
        if (package.get("brand_id") or "neuse-news") == brand_id
    }
    added = 0
    for item in items:
        package = by_link.get(item["link"]) or by_title.get(item["title"].lower())
        if package:
            package["brand_id"] = brand_id
            package["source_url"] = item["link"]
            package["pub_date"] = item.get("pub_date", package.get("pub_date", ""))
            package["rss_image_url"] = item.get("image_url", "")
            package["body"] = item.get("body", package.get("body", ""))
            if not package.get("hook"):
                package["hook"] = item.get("description", "")
        else:
            existing.append(package_from_item(item, brand_id))
            added += 1
    existing.sort(key=lambda package: str(package.get("pub_date") or package.get("id") or ""), reverse=True)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return added


def merge_all_feeds(data_path: Path, limit: int = 5) -> dict[str, int]:
    results = {}
    for brand_id, feed_url in BRAND_FEEDS.items():
        results[brand_id] = merge_feed(data_path, limit, feed_url, brand_id)
    return results


def download_image(url: str, output_dir: Path, stem: str) -> Path | None:
    if not url:
        return None
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slugify(stem)}{suffix}"
    request = Request(url, headers={"User-Agent": "Local Voice Engine/0.1"})
    with urlopen(request, timeout=30) as response:
        output_path.write_bytes(response.read())
    return output_path
