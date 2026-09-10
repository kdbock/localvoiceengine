from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import wave

from .brands import brand_asset_path, resolve_brand
from .dashboard import load_packages
from .feed import download_image


MAX_VIDEO_SECONDS = 58
SECONDS_PER_SCENE = 3.5


def find_package(packages: list[dict], package_id: str) -> dict:
    for package in packages:
        if package.get("id") == package_id:
            return package
    available = ", ".join(str(package.get("id")) for package in packages)
    raise ValueError(f"Package not found: {package_id}. Available packages: {available}")


def narration_lines(package: dict) -> list[str]:
    approved_lines = package.get("approved_script_lines")
    if isinstance(approved_lines, list) and approved_lines:
        return [sanitize_script_line(str(line)) for line in approved_lines if str(line).strip()]
    return draft_narration_lines(package)


def draft_narration_lines(package: dict) -> list[str]:
    format_name = package.get("format", "Three things to know")
    headline = package.get("headline", "Local update")
    source = article_source_text(package)
    lines = story_script_lines(package, source)
    if not lines:
        lines = [headline, call_to_action(package)]
    return [sanitize_script_line(line) for line in lines if line]


def article_source_text(package: dict) -> str:
    body = str(package.get("body", "") or "").strip()
    parts = [body] if len(body) > 200 else [
        package.get("hook", ""),
        package.get("headline", ""),
    ]
    text = " ".join(str(part) for part in parts if part)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    text = (
        text.replace("U.S.", "U.S")
        .replace("N.C.", "N.C")
        .replace(" W. ", " W ")
        .replace(" E. ", " E ")
        .replace(" N. ", " N ")
        .replace(" S. ", " S ")
    )
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    seen = set()
    for part in parts:
        sentence = sanitize_script_line(part.strip())
        key = re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()
        if len(sentence) <= 18 or key in seen:
            continue
        seen.add(key)
        sentences.append(sentence)
    return sentences


def score_sentence(sentence: str, package: dict, index: int) -> int:
    lowered = sentence.lower()
    score = max(0, 12 - index)
    for pattern in [r"\$[\d,]+", r"\d+%", r"\b\d{2,}\b", r"\bapproved\b", r"\bcharged\b", r"\bplans\b", r"\bsaid\b", r"\bwill\b", r"\bmust\b", r"\bdeadline\b", r"\bapply\b"]:
        if re.search(pattern, lowered):
            score += 4
    for word in str(package.get("headline", "")).lower().split():
        if len(word) > 4 and word in lowered:
            score += 1
    if lowered.startswith(("read more", "click", "subscribe", "the post ")):
        score -= 20
    return score


def choose_story_sentences(package: dict, limit: int = 5) -> list[str]:
    sentences = split_sentences(article_source_text(package))
    if not sentences:
        return []
    headline_key = re.sub(r"[^a-z0-9]+", " ", str(package.get("headline", "")).lower()).strip()
    filtered = [
        sentence for sentence in sentences
        if re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip() != headline_key
    ]
    if not filtered:
        filtered = sentences
    ranked = sorted(
        enumerate(filtered),
        key=lambda item: score_sentence(item[1], package, item[0]),
        reverse=True,
    )
    chosen_indexes = sorted(index for index, _sentence in ranked[:limit])
    return [filtered[index] for index in chosen_indexes]


def call_to_action(package: dict) -> str:
    brand = resolve_brand(package)
    format_name = package.get("format", "News story")
    if format_name == "Meeting in a minute":
        return f"Read the full meeting recap at {brand.get('site', 'neusenews.com')}."
    if format_name in {"Featured story", "Faces of the story"}:
        return f"Read the full feature at {brand.get('site', 'neusenews.com')}."
    return f"Read the full story at {brand.get('site', 'neusenews.com')}."


def story_script_lines(package: dict, source: str) -> list[str]:
    format_name = package.get("format", "News story")
    if format_name == "Meeting in a minute":
        return meeting_script_lines(package)
    if format_name in {"Crime story", "What happened next"}:
        return crime_script_lines(package)
    if format_name in {"Featured story", "Faces of the story"}:
        return feature_script_lines(package)
    return news_script_lines(package, 5)


def news_script_lines(package: dict, max_lines: int) -> list[str]:
    sentences = choose_story_sentences(package, max_lines + 2)
    hook = sanitize_script_line(str(package.get("hook", "")))
    lines = []
    if hook and 45 <= len(hook) <= 190:
        lines.append(hook)
    for sentence in sentences:
        if not is_duplicate(sentence, lines):
            lines.append(sentence)
        if len(lines) >= max_lines:
            break
    lines.append(call_to_action(package))
    return lines


def meeting_script_lines(package: dict) -> list[str]:
    sentences = split_sentences(article_source_text(package))
    lines = []
    add_best(lines, sentences, [r"\bapproved\b", r"\bvoted\b", r"\bpassed\b"])
    add_best(lines, sentences, [r"\bvote\b", r"\b\d+-\d+\b", r"\bvoting against\b"])
    add_best(lines, sentences, [r"\bcrash\b", r"\bsafety\b", r"\brecommend\b"])
    add_best(lines, sentences, [r"\$[\d,]+", r"\bcost\b", r"\bagreement\b", r"\bcontract\b"])
    add_best(lines, sentences, [r"\bgrant\b", r"\bappointment\b", r"\brecognized\b", r"\bproclaimed\b"])
    for sentence in choose_story_sentences(package, 7):
        if len(lines) >= 6:
            break
        if not is_duplicate(sentence, lines):
            lines.append(sentence)
    lines.append(call_to_action(package))
    return lines


def crime_script_lines(package: dict) -> list[str]:
    sentences = split_sentences(article_source_text(package))
    source = article_source_text(package)
    lines = []
    hook = sanitize_script_line(str(package.get("hook", "")))
    if hook:
        lines.append(hook)
    add_best(lines, sentences, [r"\bbegan\b", r"\btraffic stop\b", r"\bofficers responded\b"])
    charge_summary = crime_charge_summary(source)
    if charge_summary:
        lines.append(charge_summary)
    else:
        add_best(lines, sentences, [r"\bcharged\b", r"\bcharges\b", r"\bpossession\b", r"\bfirearm\b"])
    bond_summary = crime_bond_summary(source)
    if bond_summary:
        lines.append(bond_summary)
    else:
        add_best(lines, sentences, [r"\bbond\b", r"\bjail\b", r"\breleased\b"])
    add_best(lines, sentences, [r"\binvestigated\b", r"\binvestigating\b", r"\bState Highway Patrol\b"])
    if not any("allegation" in line.lower() for line in lines):
        lines.append("Charges are allegations unless proven in court.")
    lines.append(call_to_action(package))
    return lines


def crime_charge_summary(source: str) -> str:
    match = re.search(
        r"charged\s+(.+?)\s+with:\s*(.+?)(?:\s+Williams was placed|\s+The passenger|\s+Because this incident|$)",
        source,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    person = sanitize_script_line(match.group(1))
    charge_text = match.group(2).replace("\u2022", "|")
    charges = [
        sanitize_script_line(charge).strip(" .;:")
        for charge in charge_text.split("|")
        if sanitize_script_line(charge).strip(" .;:")
    ]
    if len(charges) > 3:
        charge_summary = f"{charges[0]}, {charges[1]} and other drug-related offenses"
    elif len(charges) == 3:
        charge_summary = f"{charges[0]}, {charges[1]} and {charges[2]}"
    elif len(charges) == 2:
        charge_summary = f"{charges[0]} and {charges[1]}"
    elif charges:
        charge_summary = charges[0]
    else:
        return ""
    return f"Officers charged {person} with {charge_summary}."


def crime_bond_summary(source: str) -> str:
    match = re.search(r"\b([A-Z][a-z]+ was placed in .+? under .+? bond)\.", source)
    if match:
        return f"{sanitize_script_line(match.group(1))}."
    return ""


def feature_script_lines(package: dict) -> list[str]:
    sentences = split_sentences(article_source_text(package))
    lines = []
    add_best(lines, sentences, [r"\bwho\b", r"\buses\b", r"\bstarted\b", r"\bfounded\b", r"\bserves\b"])
    add_best(lines, sentences, [r"\bsaid\b", r"\bcalled\b", r"\bdescribed\b"])
    add_best(lines, sentences, [r"\bcommunity\b", r"\blocal\b", r"\bstudents\b", r"\bfamilies\b", r"\bseniors\b"])
    for sentence in choose_story_sentences(package, 6):
        if len(lines) >= 5:
            break
        if not is_duplicate(sentence, lines):
            lines.append(sentence)
    lines.append(call_to_action(package))
    return lines


def add_best(lines: list[str], sentences: list[str], patterns: list[str]) -> None:
    for sentence in sentences:
        if is_bad_source_sentence(sentence):
            continue
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns):
            if not is_duplicate(sentence, lines):
                lines.append(sentence)
            return


def is_bad_source_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    if "\u2022" in sentence or " with: " in lowered:
        return True
    if lowered.startswith(("read more", "click", "subscribe", "the post ")):
        return True
    return False


def is_duplicate(sentence: str, lines: list[str]) -> bool:
    key = sentence_key(sentence)
    if not key:
        return True
    for line in lines:
        existing = sentence_key(line)
        if key == existing or key in existing or existing in key:
            return True
    return False


def sentence_key(sentence: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()


def make_visual_line(line: str) -> str:
    line = sanitize_script_line(line)
    line = re.sub(r"Read the full .+", "", line).strip()
    line = re.sub(r"^[A-Z][A-Z\s.]+[-\u2014]\s+", "", line).strip()
    if not line:
        return ""
    card = visual_card_phrase(line)
    if card:
        return card
    protected = line.replace("Sept.", "Sept").replace("U.S.", "U.S").replace("N.C.", "N.C")
    sentence = re.split(r"(?<=[.!?])\s+", protected)[0].strip()
    sentence = visual_sentence(sentence)
    return sentence if len(sentence) <= 180 else short_bullet(sentence, 110)


def visual_card_phrase(line: str) -> str:
    lowered = line.lower()
    money = re.search(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?", line, re.IGNORECASE)
    percent = re.search(r"\b\d+%", line)
    vote = re.search(r"\b\d+-\d+\b", line)
    if "read the full" in lowered:
        return ""
    if "police presence" in lowered and "autozone" in lowered:
        return "Police presence at AutoZone."
    if "traffic stop" in lowered:
        return "The incident began with a traffic stop."
    if "charged" in lowered and ("firearm" in lowered or "drug" in lowered):
        return "Firearm and drug-related charges."
    if "jail" in lowered and "bond" in lowered:
        return "Secured bond at Lenoir County Jail."
    if "allegation" in lowered:
        return "Charges are allegations unless proven in court."
    if "split discussion" in lowered and ("all-way stop" in lowered or "four-way stop" in lowered):
        return "Debate focused on safety and traffic flow."
    if "all-way stop" in lowered or "four-way stop" in lowered:
        return "All-way stop approved."
    if vote:
        return f"Vote: {vote.group(0)}."
    if "crash" in lowered and any(word in lowered for word in ["safety", "intersection", "improvements"]):
        return "Safety concerns drove the discussion."
    if "lower-cost safety improvements" in lowered:
        return "Earlier safety fixes were not enough."
    if "welcomed a new finance officer" in lowered:
        return "Finance, retirement and recognitions."
    if money:
        return f"Amount: {money.group(0)}."
    if percent:
        return f"Key number: {percent.group(0)}."
    return ""


def visual_sentence(sentence: str) -> str:
    sentence = sentence.strip(" ,;:")
    sentence = re.sub(r", according to .+$", "", sentence)
    sentence = re.sub(r", along with .+$", "", sentence)
    sentence = re.sub(r", but .+$", "", sentence)
    sentence = re.sub(r" while .+$", "", sentence)
    replacements = [
        (r"^(.+?\bapproved\b .*?)(?: on [A-Z][a-z]+| during .+| after .+|, .+)$", r"\1"),
        (r"^(.+?\bgenerated\b .*?)(?:, .+)$", r"\1"),
        (r"^(.+?\bincreased\b .*?)(?:, .+)$", r"\1"),
        (r"^(.+?\bsigned\b .*?)(?: covering .+| from .+|, .+)$", r"\1"),
        (r"^(.+?\bwill support\b .*?)(?: while .+|, .+)$", r"\1"),
    ]
    for pattern, replacement in replacements:
        shortened = re.sub(pattern, replacement, sentence)
        if shortened != sentence and len(shortened) >= 24:
            sentence = shortened
            break
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence


def visual_lines(package: dict, audio_lines: list[str]) -> list[str]:
    approved_lines = package.get("approved_visual_lines")
    if package.get("visual_text_mode") == "manual" and isinstance(approved_lines, list) and approved_lines:
        lines = [sanitize_script_line(str(line)) for line in approved_lines]
        return normalize_visual_lines(lines, audio_lines)
    return normalize_visual_lines([], audio_lines)


def normalize_visual_lines(manual_lines: list[str], audio_lines: list[str]) -> list[str]:
    normalized = []
    for index, audio_line in enumerate(audio_lines):
        manual_line = manual_lines[index].strip() if index < len(manual_lines) else ""
        normalized.append(manual_line or make_visual_line(audio_line) or sanitize_script_line(audio_line))
    return normalized


def sanitize_script_line(line: str) -> str:
    line = line.replace("Last night,", "On Sept. 8,")
    line = re.sub(r"\s*\(September 8, 2026\)", "", line)
    line = line.replace("\u2014", "-")
    line = line.replace("&nbsp;", " ")
    line = line.replace("\u2019", "'")
    return " ".join(line.split())


def spoken_script_text(script: str) -> str:
    script = re.sub(
        r"Read the full (story|meeting recap|feature) at [a-z0-9.-]+\.",
        r"Read the full \1 online.",
        script,
    )
    script = script.replace("LenoirCountyNC.gov", "La'Nore County N C dot gov")
    script = script.replace("Lenoir County", "La'Nore County")
    return script


def hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    value = (value or "").strip().lstrip("#")
    if len(value) != 6:
        return fallback
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback


def luminance(color: tuple[int, int, int]) -> float:
    channels = []
    for value in color:
        value = value / 255
        channels.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def readable_text_color(background: tuple[int, int, int]) -> tuple[int, int, int]:
    return (28, 34, 40) if luminance(background) > 0.62 else (255, 255, 255)


def shadowed_text(draw, position: tuple[int, int], text: str, fill, font, shadow=(0, 0, 0, 120)) -> None:
    x, y = position
    draw.text((x + 2, y + 2), text, fill=shadow, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def wrap_caption(text: str) -> str:
    return "\n".join(textwrap.wrap(text, width=42))


def short_bullet(text: str, max_chars: int = 34) -> str:
    text = re.sub(r"Read the full .+", "", text)
    text = " ".join(text.replace("$", "$").split()).strip(" .")
    if len(text) <= max_chars:
        return text
    wrapped = textwrap.wrap(text, width=max_chars, break_on_hyphens=False)
    bullet = wrapped[0].strip(" .,;:") if wrapped else text[:max_chars].strip()
    weak_endings = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "additional"}
    words = bullet.split()
    while words and words[-1].lower().strip(".,;:") in weak_endings:
        words.pop()
    result = " ".join(words) or bullet
    return result if result.endswith((".", "!", "?")) else f"{result}."


def story_bullets(package: dict, current_line: str) -> list[str]:
    lines = package.get("approved_script_lines") or package.get("suggested_script_lines") or []
    candidates = [current_line, package.get("headline", ""), package.get("hook", ""), *lines]
    bullets = []
    for candidate in candidates:
        bullet = short_bullet(str(candidate))
        if not bullet or bullet.lower().startswith("read the full"):
            continue
        if bullet.lower() in {item.lower() for item in bullets}:
            continue
        bullets.append(bullet)
        if len(bullets) == 2:
            break
    bullets.append(package.get("county", "Local"))
    return bullets[:3]


def srt_timestamp(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02},000"


def scene_durations(lines: list[str], total_duration: float | None = None) -> list[float]:
    raw = [max(4, len(line.split())) for line in lines]
    if not total_duration:
        return [max(3.0, min(9.0, weight / 16.0)) for weight in raw]
    target = min(MAX_VIDEO_SECONDS + 2, total_duration + 2.5)
    scale = target / sum(raw)
    durations = [max(2.4, weight * scale) for weight in raw]
    overflow = sum(durations) - target
    if overflow > 0:
        adjustable = [max(0, duration - 2.4) for duration in durations]
        adjustable_total = sum(adjustable)
        if adjustable_total:
            durations = [
                duration - overflow * (amount / adjustable_total)
                for duration, amount in zip(durations, adjustable)
            ]
    return durations


def measured_scene_durations(lines: list[str], package_dir: Path) -> list[float] | None:
    if not Path("/usr/bin/say").exists():
        return None
    timing_dir = package_dir / "timing"
    if timing_dir.exists():
        shutil.rmtree(timing_dir)
    timing_dir.mkdir(parents=True, exist_ok=True)
    durations = []
    for index, line in enumerate(lines, 1):
        text_path = timing_dir / f"line-{index:02}.txt"
        audio_path = timing_dir / f"line-{index:02}.aiff"
        text_path.write_text(spoken_script_text(line), encoding="utf-8")
        try:
            subprocess.run(
                ["/usr/bin/say", "-f", str(text_path), "-o", str(audio_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        duration = audio_duration_seconds(audio_path)
        if duration is None:
            return None
        durations.append(duration + 0.15)
    if durations:
        durations[-1] += 1.4
    return durations


def render_srt(lines: list[str], durations: list[float] | None = None) -> str:
    durations = durations or scene_durations(lines)
    blocks = []
    current = 0.0
    for index, line in enumerate(lines, 1):
        start = int(current)
        current += durations[index - 1]
        end = int(current)
        blocks.append(
            f"{index}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{wrap_caption(line)}"
        )
    return "\n\n".join(blocks) + "\n"


def render_shotlist(package: dict, lines: list[str]) -> str:
    visuals = package.get("visuals", [])
    rows = [
        f"# {package.get('headline', 'Untitled package')}",
        "",
        f"Format: {package.get('format', 'Three things to know')}",
        f"County: {package.get('county', 'Local')}",
        f"Status: {package.get('status', 'idea')}",
        "",
        "## Timeline",
    ]
    for index, line in enumerate(lines, 1):
        visual = visual_for_scene(visuals, index - 1, len(lines))
        start = round((index - 1) * SECONDS_PER_SCENE, 1)
        end = round(index * SECONDS_PER_SCENE, 1)
        rows.extend(
            [
                f"### {start}-{end} seconds",
                f"Visual: {visual}",
                f"Narration: {line}",
                "",
            ]
        )
    rows.extend(
        [
            "## Production Notes",
            f"- Next step: {package.get('next_step', '')}",
            "- Use vertical 9:16 format.",
            "- Burn captions into the video.",
            "- Use editor-approved visuals only.",
        ]
    )
    return "\n".join(rows) + "\n"


def visual_for_scene(visuals: list[str], index: int, line_count: int) -> str:
    if line_count <= 5:
        sequence = ["opening", "what we know", "key details", "what's next", "find out more"]
        return sequence[min(index, len(sequence) - 1)]
    if index == 0 and "story image" in visuals:
        return "story image"
    if index == line_count - 1:
        for visual in visuals:
            if "branded" in visual.lower() or "end" in visual.lower():
                return visual
        return "branded end card"
    middle = [
        visual
        for visual in visuals
        if visual != "story image" and "branded" not in visual.lower() and "end" not in visual.lower()
    ]
    if not middle:
        middle = ["context card", "caption card"]
    return middle[(index - 1) % len(middle)]


def screen_label(index: int, line_count: int, visual: str) -> str:
    if line_count <= 5:
        labels = ["Opening", "What we know", "Key details", "What's next", "Find out more"]
        return labels[min(index, len(labels) - 1)]
    if visual == "story image":
        return "Opening"
    if "context" in visual.lower():
        return "What we know"
    if "caption" in visual.lower():
        return "Key details"
    if "branded" in visual.lower() or "end" in visual.lower():
        return "Find out more"
    return "Key details"


def load_story_image(package: dict, package_dir: Path):
    try:
        from PIL import Image
    except ImportError:
        return None

    asset = package.get("story_image_asset") or package.get("story_image_path")
    image_path = Path(asset) if asset else None
    if image_path and not image_path.is_absolute():
        image_path = Path.cwd() / image_path
    if not image_path or not image_path.exists():
        downloaded = download_image(
            package.get("rss_image_url", ""),
            package_dir / "assets",
            package.get("id") or package.get("headline", "story"),
        )
        image_path = downloaded
        if downloaded:
            package["story_image_path"] = str(downloaded)
    if image_path and image_path.exists():
        try:
            return Image.open(image_path).convert("RGB")
        except OSError:
            return None
    return None


def load_image_path(path_value: str):
    try:
        from PIL import Image
    except ImportError:
        return None
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGB")
    except OSError:
        return None


def load_visual_images(package: dict, package_dir: Path) -> list:
    images = []
    rss_image = load_story_image(package, package_dir)
    if rss_image is not None:
        images.append(rss_image)
    for path_value in package.get("article_image_paths", [])[:3]:
        image = load_image_path(str(path_value))
        if image is not None:
            images.append(image)
    headshot = load_image_path(str(package.get("headshot_image_path", "")))
    if headshot is not None:
        images.append(headshot)
    return images


def cover_crop(image, size: tuple[int, int], motion_step: int = 0):
    width, height = image.size
    target_width, target_height = size
    scale = max(target_width / width, target_height / height) * (1.02 + motion_step * 0.0018)
    resized = image.resize((int(width * scale), int(height * scale)))
    x = max(0, (resized.width - target_width) // 2)
    y = max(0, (resized.height - target_height) // 2)
    return resized.crop((x, y, x + target_width, y + target_height))


def contain_image(image, size: tuple[int, int]):
    from PIL import ImageEnhance, ImageFilter

    width, height = image.size
    target_width, target_height = size
    scale = min(target_width / width, target_height / height)
    resized = image.resize((int(width * scale), int(height * scale)))
    canvas = cover_crop(image, size).filter(ImageFilter.GaussianBlur(18))
    canvas = ImageEnhance.Brightness(canvas).enhance(0.72)
    x = (target_width - resized.width) // 2
    y = (target_height - resized.height) // 2
    canvas.paste(resized, (x, y))
    return canvas


def load_ambient_asset(package: dict):
    asset = package.get("ambient_asset") or package.get("background_asset")
    if not asset:
        return None
    path = Path(asset)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return None
    return path


def ambient_frame(package: dict, size: tuple[int, int], motion_step: int, story_image=None, brand=None):
    from PIL import Image, ImageDraw, ImageFilter

    width, height = size
    palette = {
        "What happened next": ((15, 25, 35), (110, 34, 38), (226, 184, 86)),
        "Crime story": ((15, 25, 35), (110, 34, 38), (226, 184, 86)),
        "Meeting in a minute": ((20, 38, 48), (37, 92, 119), (207, 224, 235)),
        "News story": ((20, 36, 41), (47, 111, 94), (225, 211, 148)),
        "Public records roundup": ((26, 37, 41), (53, 88, 78), (224, 213, 184)),
        "Faces of the story": ((38, 33, 43), (93, 65, 103), (235, 204, 165)),
        "Featured story": ((38, 33, 43), (93, 65, 103), (235, 204, 165)),
    }.get(package.get("format"), ((20, 36, 41), (47, 111, 94), (225, 211, 148)))
    bg, mid, accent = palette
    if brand:
        video = brand.get("video", {})
        bg = hex_to_rgb(video.get("top_bar"), bg)
        mid = hex_to_rgb(brand.get("colors", {}).get("primary"), mid)
        accent = hex_to_rgb(video.get("accent"), accent)
    image = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(image, "RGBA")
    if story_image is not None:
        base = cover_crop(story_image, size, motion_step + 14).filter(ImageFilter.GaussianBlur(24))
        veil = Image.new("RGBA", size, (*bg, 155))
        image = Image.alpha_composite(base.convert("RGBA"), veil).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
    for i in range(12):
        x = -260 + i * 140 + motion_step * 8
        draw.line((x, -80, x + 520, height + 80), fill=(*mid, 72), width=52)
    for i in range(6):
        y = 160 + i * 290 - motion_step * 4
        draw.ellipse((80 + i * 120, y, 460 + i * 120, y + 380), fill=(*accent, 24))
    for i in range(9):
        x = (motion_step * 27 + i * 151) % (width + 180) - 90
        y = 310 + ((motion_step * 19 + i * 211) % 1120)
        draw.rounded_rectangle((x, y, x + 190, y + 54), radius=10, fill=(255, 255, 255, 18))
    return image.filter(ImageFilter.GaussianBlur(1.4))


def read_video_background_frame(asset_path: Path, frame_index: int, size: tuple[int, int]):
    try:
        import imageio.v2 as imageio
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return None

    if asset_path.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm"}:
        return None
    try:
        reader = imageio.get_reader(str(asset_path))
        count = reader.count_frames()
        frame = reader.get_data(frame_index % max(1, count))
        reader.close()
        image = Image.fromarray(frame).convert("RGB")
        image = cover_crop(image, size, frame_index)
        image = ImageEnhance.Brightness(image).enhance(0.62)
        return image.filter(ImageFilter.GaussianBlur(2))
    except Exception:
        return None


def draw_story_foreground(canvas, story_image, motion_step: int) -> None:
    from PIL import ImageDraw

    draw = ImageDraw.Draw(canvas, "RGBA")
    box = (210, 170, 870, 1050)
    draw.rounded_rectangle((box[0] - 8, box[1] - 8, box[2] + 8, box[3] + 8), radius=24, fill=(255, 255, 255, 30))
    foreground = cover_crop(story_image, (box[2] - box[0], box[3] - box[1]), motion_step + 8)
    canvas.paste(foreground, (box[0], box[1]))
    draw.rounded_rectangle(box, radius=16, outline=(255, 255, 255, 145), width=4)


def draw_brand_logo(canvas, brand: dict, box: tuple[int, int, int, int], dark_background: bool = True) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    if dark_background:
        logo_path = brand_asset_path(brand, "logo_dark") or brand_asset_path(brand, "logo_horizontal") or brand_asset_path(brand, "logo")
    else:
        logo_path = brand_asset_path(brand, "logo") or brand_asset_path(brand, "logo_horizontal") or brand_asset_path(brand, "logo_dark")
    if not logo_path:
        return False
    try:
        logo = Image.open(logo_path).convert("RGBA")
    except OSError:
        return False
    left, top, right, bottom = box
    max_width = right - left
    max_height = bottom - top
    scale = min(max_width / logo.width, max_height / logo.height)
    resized = logo.resize((max(1, int(logo.width * scale)), max(1, int(logo.height * scale))))
    x = left + (max_width - resized.width) // 2
    y = top + (max_height - resized.height) // 2
    canvas.paste(resized, (x, y), resized)
    return True


def draw_scene(
    package: dict,
    line: str,
    visual: str,
    index: int,
    output_path: Path,
    story_image=None,
    ambient_asset: Path | None = None,
    motion_step: int = 0,
    line_count: int = 1,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required to render PNG frames.") from exc

    brand = resolve_brand(package)
    video = brand.get("video", {})
    bg = hex_to_rgb(video.get("background") or video.get("top_bar"), (23, 50, 77))
    fg = hex_to_rgb(video.get("text"), (247, 250, 252))
    accent = hex_to_rgb(video.get("accent"), (242, 191, 94))
    image = None
    if video.get("background_style") == "solid":
        image = Image.new("RGB", (1080, 1920), bg)
    elif ambient_asset is not None:
        image = read_video_background_frame(ambient_asset, index * 18 + motion_step, (1080, 1920))
    if image is None:
        image = ambient_frame(package, (1080, 1920), index * 18 + motion_step, story_image, brand)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    def font(size: int, bold: bool = False):
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    logo_on_dark = luminance(bg) < 0.55
    logo_box = (54, 34, 254, 134)
    if brand.get("id") != "neuse-news":
        draw.rounded_rectangle((34, 20, 274, 148), radius=16, fill=((0, 0, 0, 80) if logo_on_dark else (255, 255, 255, 190)))
    logo_drawn = draw_brand_logo(overlay, brand, logo_box, dark_background=logo_on_dark)
    if not logo_drawn:
        draw.text((60, 68), brand.get("site", "news").upper(), fill=readable_text_color(bg), font=font(28, True))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    label = screen_label(index, line_count, visual)
    uses_story_image = story_image is not None and visual in {"story image", "opening"}
    if uses_story_image:
        draw_story_foreground(image, story_image, motion_step)
    else:
        art_box = (54, 235, 1026, 1284)
        draw.rounded_rectangle(art_box, radius=18, fill=(248, 250, 252, 228), outline=accent, width=3)
        draw_visual(draw, art_box, visual, label, package, brand, line, index, motion_step, font)

    if uses_story_image:
        caption_box = (54, 1160, 1026, 1504)
        caption_fill = (255, 255, 255)
        caption_text = hex_to_rgb(brand.get("colors", {}).get("ink"), (28, 34, 40))
        draw.rounded_rectangle(caption_box, radius=22, fill=(*caption_fill, 236), outline=(*accent, 210), width=3)
        caption_left, caption_top, caption_right, caption_bottom = caption_box
        draw.text((caption_left + 38, caption_top + 28), label.upper(), fill=accent, font=font(26, True))
        caption_width = caption_right - caption_left - 76
        caption_height = caption_bottom - caption_top - 124
        caption_font_size = 50
        wrapped = []
        while caption_font_size >= 26:
            test_font = font(caption_font_size, True)
            chars_per_line = max(22, int(caption_width / (caption_font_size * 0.58)))
            wrapped = textwrap.wrap(line, width=chars_per_line)
            line_height = int(caption_font_size * 1.2)
            fits_height = len(wrapped) * line_height <= caption_height
            fits_width = all(draw.textbbox((0, 0), part, font=test_font)[2] <= caption_width for part in wrapped)
            if fits_height and fits_width:
                break
            caption_font_size -= 2

        y = caption_box[1] + 72
        line_height = int(caption_font_size * 1.2)
        for part in wrapped:
            draw.text((92, y), part, fill=caption_text, font=font(caption_font_size, True))
            y += line_height

    draw.line((72, 1600, 1008, 1600), fill=(*accent, 175), width=4)
    footer_text = readable_text_color(bg)
    footer_shadow = (255, 255, 255, 155) if footer_text == (28, 34, 40) else (0, 0, 0, 120)
    shadowed_text(draw, (92, 1642), f"Read the full story at {brand.get('site', 'neusenews.com')}", fill=footer_text, font=font(34, True), shadow=footer_shadow)
    headline = package.get("headline", "Local update")
    y = 1712
    for part in textwrap.wrap(headline, width=54)[:3]:
        headline_shadow = (255, 255, 255, 145) if luminance(fg) < 0.35 else (0, 0, 0, 110)
        shadowed_text(draw, (92, y), part, fill=fg, font=font(28), shadow=headline_shadow)
        y += 36

    image.save(output_path)


def draw_visual(draw, box, visual: str, label: str, package: dict, brand: dict, line: str, index: int, motion_step: int, font) -> None:
    left, top, right, bottom = box
    w = right - left
    h = bottom - top
    lower = visual.lower()
    brand_colors = brand.get("colors", {})
    primary = hex_to_rgb(brand_colors.get("primary"), (47, 64, 82))
    accent = hex_to_rgb(brand.get("video", {}).get("accent"), (210, 158, 71))
    primary_text = readable_text_color(primary)
    accent_text = readable_text_color(accent)
    if lower in {"what we know", "key details", "what's next", "find out more"}:
        draw.rectangle((left, top, right, bottom), fill=(247, 248, 250))
        draw.text((left + 70, top + 78), label, fill=primary, font=font(54, True))
        fact = " ".join(line.replace("Charges are allegations unless proven in court.", "").split()).strip()
        y = top + 190
        for part in textwrap.wrap(fact, width=32)[:4]:
            draw.text((left + 70, y), part, fill=(31, 36, 40), font=font(44, True))
            y += 58
        if lower == "find out more":
            draw.rounded_rectangle((left + 70, bottom - 150, right - 70, bottom - 72), radius=16, fill=accent)
            draw.text((left + 100, bottom - 132), f"Read at {brand.get('site', 'neusenews.com')}", fill=accent_text, font=font(36, True))
        else:
            draw.line((left + 70, bottom - 110, right - 70, bottom - 110), fill=accent, width=6)
    elif "map" in lower:
        draw.rectangle((left, top, right, bottom), fill=(228, 235, 230))
        for i in range(7):
            y = top + 40 + i * 82 + motion_step
            draw.line((left + 20, y, right - 20, y + 90), fill=(202, 214, 205), width=16)
        draw.line((left + 40, bottom - 120, right - 80, top + 120), fill=(246, 246, 238), width=46)
        draw.line((left + 40, bottom - 120, right - 80, top + 120), fill=accent, width=8)
        pin_x = left + w // 2 + (motion_step % 8)
        pin_y = top + h // 2 - 30
        draw.ellipse((pin_x - 46, pin_y - 46, pin_x + 46, pin_y + 46), fill=primary)
        draw.ellipse((pin_x - 16, pin_y - 16, pin_x + 16, pin_y + 16), fill=(255, 255, 255))
        draw.text((left + 48, bottom - 86), package.get("county", "Local"), fill=(31, 43, 47), font=font(42, True))
    elif "timeline" in lower:
        draw.rectangle((left, top, right, bottom), fill=(247, 247, 242))
        x = left + 130
        draw.line((x, top + 90, x, bottom - 90), fill=primary, width=10)
        labels = ["Report", "Response", "Update"]
        for i, label in enumerate(labels):
            y = top + 120 + i * 150 + motion_step
            draw.ellipse((x - 28, y - 28, x + 28, y + 28), fill=accent)
            draw.text((x + 70, y - 30), label, fill=(31, 36, 40), font=font(44, True))
    elif "record" in lower or "table" in lower or "document" in lower or "grant" in lower:
        draw.rectangle((left, top, right, bottom), fill=(250, 250, 247))
        for i in range(8):
            y = top + 70 + i * 55
            draw.line((left + 70, y, right - 70, y), fill=(202, 210, 217), width=3)
        draw.rectangle((left + 70, top + 80, right - 70, top + 150), fill=primary)
        draw.text((left + 98, top + 98), "PUBLIC RECORD", fill=primary_text, font=font(34, True))
        draw.rounded_rectangle((left + 94, bottom - 150, right - 94, bottom - 82), radius=12, fill=(255, 255, 255), outline=accent, width=3)
        draw.text((left + 120, bottom - 136), "Verified before publishing", fill=(31, 36, 40), font=font(34, True))
    elif "agency" in lower or "date" in lower or "decision" in lower or "dollar" in lower:
        draw.rectangle((left, top, right, bottom), fill=(240, 245, 249))
        draw.rounded_rectangle((left + 70, top + 80, right - 70, bottom - 80), radius=18, fill=(255, 255, 255), outline=(190, 205, 218), width=4)
        draw.text((left + 110, top + 128), "LOCAL UPDATE", fill=primary, font=font(46, True))
        draw.text((left + 110, top + 220), package.get("county", "Local"), fill=(31, 36, 40), font=font(58, True))
        draw.text((left + 110, top + 320), package.get("format", "News"), fill=(88, 102, 112), font=font(38))
    elif "context" in lower:
        draw.rectangle((left, top, right, bottom), fill=(244, 247, 246))
        draw.text((left + 70, top + 88), label, fill=primary, font=font(54, True))
        short_format = package.get("format", "Local update")
        if short_format in {"Crime story", "What happened next"}:
            short_format = "Police update"
        bullets = story_bullets(package, line)
        for item_index, bullet in enumerate(bullets):
            y = top + 190 + item_index * 92
            draw.ellipse((left + 78, y + 15, left + 112, y + 49), fill=accent)
            draw.text((left + 140, y), bullet, fill=(31, 36, 40), font=font(38, True))
        draw.line((left + 70, bottom - 130, right - 70, bottom - 130), fill=(190, 205, 198), width=4)
        draw.text((left + 70, bottom - 94), short_format, fill=(88, 102, 112), font=font(32, True))
    elif "caption" in lower:
        draw.rectangle((left, top, right, bottom), fill=(247, 247, 242))
        if package.get("format") == "Meeting in a minute":
            label = "Meeting notes"
            footer = "Local decisions, quickly"
        elif package.get("format") in {"Crime story", "What happened next"}:
            label = "Police said"
            footer = "Charges are allegations"
        elif package.get("format") == "Featured story":
            label = "Featured detail"
            footer = "Read the full feature"
        else:
            label = label or "Key details"
            footer = "Read the full report"
        draw.text((left + 70, top + 78), label, fill=primary, font=font(50, True))
        fact = " ".join(line.replace("Charges are allegations unless proven in court.", "").split()).strip()
        y = top + 178
        body_font_size = 40 if package.get("format") == "Meeting in a minute" else 44
        for part in textwrap.wrap(fact, width=34)[:4]:
            draw.text((left + 70, y), part, fill=(31, 36, 40), font=font(body_font_size, True))
            y += 54
        draw.rounded_rectangle((left + 70, bottom - 150, right - 70, bottom - 72), radius=16, fill=accent)
        draw.text((left + 100, bottom - 132), footer, fill=accent_text, font=font(36, True))
    else:
        draw.rectangle((left, top, right, bottom), fill=(238, 242, 246))
        draw.text((left + 70, top + 92), brand.get("name", "Neuse News"), fill=(31, 36, 40), font=font(58, True))
        draw.text((left + 70, top + 182), brand.get("tagline", "Local reporting for eastern North Carolina"), fill=(88, 102, 112), font=font(34))
        draw.rounded_rectangle((left + 70, bottom - 158, right - 70, bottom - 78), radius=16, fill=accent)
        draw.text((left + 102, bottom - 139), "Read more online", fill=accent_text, font=font(38, True))


def audio_duration_seconds(path: Path) -> float | None:
    if not path.exists() or path.suffix.lower() not in {".aiff", ".aif", ".wav"}:
        return None
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as audio:
                return audio.getnframes() / float(audio.getframerate())
        except wave.Error:
            return None
    try:
        result = subprocess.run(
            ["/usr/bin/afinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"estimated duration:\s+([0-9.]+)", result.stdout)
    return float(match.group(1)) if match else None


def render_mp4(package_dir: Path, frame_paths: list[Path], voiceover_path: Path | None, durations: list[float]) -> Path | None:
    try:
        import imageio.v2 as imageio
        import imageio_ffmpeg
    except ImportError:
        return None

    if not frame_paths:
        return None

    video_path = package_dir / "video.mp4"
    temp_video = package_dir / "video_silent.mp4"
    temp_video.unlink(missing_ok=True)
    writer = imageio.get_writer(
        str(temp_video),
        fps=24,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        ffmpeg_log_level="error",
    )
    try:
        scene_count = max(1, len(durations))
        frames_per_scene = max(1, len(frame_paths) // scene_count)
        for scene_index, duration in enumerate(durations):
            scene_frames = frame_paths[
                scene_index * frames_per_scene : (scene_index + 1) * frames_per_scene
            ]
            if not scene_frames:
                continue
            repeats = max(1, math.ceil((duration / len(scene_frames)) * 24))
            for frame_path in scene_frames:
                frame = imageio.imread(frame_path)
                for _ in range(repeats):
                    writer.append_data(frame)
    finally:
        writer.close()

    if voiceover_path and voiceover_path.exists():
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(temp_video),
                "-i",
                str(voiceover_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                str(video_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        temp_video.unlink(missing_ok=True)
    else:
        temp_video.replace(video_path)
    return video_path


def write_voiceover(script_path: Path, output_path: Path) -> bool:
    if not Path("/usr/bin/say").exists():
        return False
    voice_script_path = output_path.with_name("voiceover_input.txt")
    voice_script_path.write_text(
        spoken_script_text(script_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    subprocess.run(
        ["/usr/bin/say", "-f", str(voice_script_path), "-o", str(output_path)],
        check=True,
    )
    return True


def export_package(data_path: Path, package_id: str, output_root: Path) -> Path:
    package = find_package(load_packages(data_path), package_id)
    package_dir = output_root / package_id
    frames_dir = package_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    lines = narration_lines(package)
    screen_lines = visual_lines(package, lines)
    script = "\n\n".join(lines) + "\n"
    visual_script = "\n\n".join(screen_lines) + "\n"
    visuals = package.get("visuals", []) or ["branded card"]

    (package_dir / "script.txt").write_text(script, encoding="utf-8")
    (package_dir / "visual_text.txt").write_text(visual_script, encoding="utf-8")
    (package_dir / "package.json").write_text(
        json.dumps(package, indent=2) + "\n",
        encoding="utf-8",
    )

    png_frame_paths = []
    visual_images = load_visual_images(package, package_dir)
    ambient_asset = load_ambient_asset(package)
    for index, line in enumerate(lines):
        screen_line = screen_lines[index] if index < len(screen_lines) else line
        visual = "story image" if index < len(visual_images) else visual_for_scene(visuals, index, len(lines))
        story_image = visual_images[index % len(visual_images)] if visual_images else None
        for motion_step in range(18):
            png_path = frames_dir / f"scene_{index + 1:02}_{motion_step + 1:02}.png"
            try:
                draw_scene(package, screen_line, visual, index, png_path, story_image, ambient_asset, motion_step, len(lines))
                png_frame_paths.append(png_path)
            except RuntimeError:
                pass

    (package_dir / "package.json").write_text(
        json.dumps(package, indent=2) + "\n",
        encoding="utf-8",
    )

    voiceover_path = package_dir / "voiceover.aiff"
    try:
        write_voiceover(package_dir / "script.txt", voiceover_path)
    except (OSError, subprocess.CalledProcessError):
        voiceover_path = None

    durations = measured_scene_durations(lines, package_dir) or scene_durations(
        lines, audio_duration_seconds(voiceover_path) if voiceover_path else None
    )
    (package_dir / "captions.srt").write_text(render_srt(lines, durations), encoding="utf-8")
    (package_dir / "shotlist.md").write_text(render_shotlist(package, lines), encoding="utf-8")

    video_path = None
    try:
        video_path = render_mp4(package_dir, png_frame_paths, voiceover_path, durations)
    except (OSError, subprocess.CalledProcessError, RuntimeError):
        video_path = None

    (package_dir / "render_notes.md").write_text(
        "# Render notes\n\n"
        + (
            f"Rendered video: {video_path.name}\n\n"
            if video_path
            else "The production package was created, but MP4 rendering did not complete.\n\n"
        )
        + "Inputs:\n"
        "- script.txt\n"
        "- captions.srt\n"
        "- voiceover.aiff, if generated\n"
        "- frames/*.png\n",
        encoding="utf-8",
    )
    return package_dir
