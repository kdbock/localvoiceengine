from __future__ import annotations

import json
from pathlib import Path


DEFAULT_BRAND_ID = "neuse-news"


def brand_kits_path() -> Path:
    return Path.cwd() / "config" / "brand_kits.json"


def load_brand_kits(path: Path | None = None) -> dict:
    path = path or brand_kits_path()
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_brand(package: dict, path: Path | None = None) -> dict:
    kits = load_brand_kits(path)
    brand_id = package.get("brand_id") or DEFAULT_BRAND_ID
    brand = kits.get(brand_id) or kits[DEFAULT_BRAND_ID]
    return {"id": brand_id, **brand}


def brand_asset_path(brand: dict, key: str) -> Path | None:
    asset = brand.get(key)
    if not asset:
        return None
    path = Path(asset)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path if path.exists() else None
