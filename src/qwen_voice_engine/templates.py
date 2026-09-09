from __future__ import annotations

import json
from pathlib import Path


def templates_path() -> Path:
    return Path(__file__).resolve().parents[2] / "templates" / "story_templates.json"


def load_story_templates(path: Path | None = None) -> dict:
    path = path or templates_path()
    return json.loads(path.read_text(encoding="utf-8"))


def render_template_list(path: Path | None = None) -> str:
    templates = load_story_templates(path)
    rows = ["Local Voice Engine templates", ""]
    for template_id, template in templates.items():
        rows.extend(
            [
                template["name"],
                f"ID: {template_id}",
                f"Target: {template['target_seconds']} seconds",
                f"Best for: {template['best_for']}",
                "",
            ]
        )
    return "\n".join(rows).strip() + "\n"
