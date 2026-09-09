from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from textwrap import fill


@dataclass(frozen=True)
class VideoBrief:
    title: str
    format_name: str
    hook: str
    narration: list[str]
    visual_beats: list[str]
    captions: list[str]
    social_caption: str
    checklist: list[str]


KEYWORDS = {
    "What happened next": ["arrest", "charges", "police", "sheriff", "traffic stop", "firearm", "drug"],
    "Meeting in a minute": ["commissioners", "council", "board", "approved", "hearing", "grant"],
    "New and coming soon": ["open", "opening", "expanding", "restaurant", "business"],
    "Public records roundup": ["land transfers", "new corporations", "inspections", "register of deeds"],
    "Faces of the story": ["spotlight", "student", "teacher", "volunteer", "serves", "mission"],
}


def sentence_case(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return "Untitled video"
    return text[:1].upper() + text[1:]


def choose_format(article: str) -> str:
    lower = article.lower()
    for format_name, words in KEYWORDS.items():
        if any(word in lower for word in words):
            return format_name
    return "Three things to know"


def extract_first_sentence(article: str) -> str:
    article = re.sub(r"\s+", " ", article.strip())
    match = re.search(r"(.+?[.!?])\s", article + " ")
    return match.group(1).strip() if match else article[:180].strip()


def make_brief(article: str, source_name: str = "article") -> VideoBrief:
    first_sentence = extract_first_sentence(article)
    format_name = choose_format(article)
    title = sentence_case(source_name.replace("_", " ").replace("-", " "))

    if format_name == "Meeting in a minute":
        hook = "A local board met this week. Here are the decisions residents should know about."
        visual_beats = [
            "Show courthouse, city hall or county map.",
            "Show a card with the main vote or decision.",
            "Show a second card with the dollar amount, location or deadline.",
            "End with where readers can find the full story.",
        ]
    elif format_name == "What happened next":
        hook = "If you saw people asking about this, here is what officials say happened."
        visual_beats = [
            "Show neutral location image or map pin.",
            "Show agency name and date.",
            "Show a simple timeline of what officials reported.",
            "End with a reminder that charges are allegations unless proven in court.",
        ]
    elif format_name == "New and coming soon":
        hook = "A local business update is drawing attention. Here is what we know."
        visual_beats = [
            "Show storefront, logo or map.",
            "Show what is opening, closing or expanding.",
            "Show location and timing.",
            "End with full story prompt.",
        ]
    else:
        hook = "Here is a local update worth knowing today."
        visual_beats = [
            "Show a clean Neuse News title card.",
            "Show the main person, place or agency.",
            "Show one or two key facts as text cards.",
            "End with the full story prompt.",
        ]

    narration = [
        hook,
        first_sentence,
        "Neuse News has the full story at neusenews.com.",
    ]

    captions = [
        sentence_case(format_name),
        sentence_case(first_sentence),
        "Read more at neusenews.com",
    ]

    checklist = [
        "Confirm names, dates, places and dollar amounts.",
        "Confirm headline follows sentence format.",
        "Remove speculation and loaded language.",
        "Confirm visuals are licensed, submitted or public-record appropriate.",
        "Editor approves before posting.",
    ]

    return VideoBrief(
        title=title,
        format_name=format_name,
        hook=hook,
        narration=narration,
        visual_beats=visual_beats,
        captions=captions,
        social_caption=f"{first_sentence} Read the full story at neusenews.com.",
        checklist=checklist,
    )


def render_markdown(brief: VideoBrief) -> str:
    lines = [
        f"# {brief.title}",
        "",
        f"Format: {brief.format_name}",
        "",
        "## Hook",
        brief.hook,
        "",
        "## Narration",
    ]
    lines.extend(f"{i}. {fill(item, 88)}" for i, item in enumerate(brief.narration, 1))
    lines.extend(["", "## Visual beats"])
    lines.extend(f"{i}. {item}" for i, item in enumerate(brief.visual_beats, 1))
    lines.extend(["", "## On-screen captions"])
    lines.extend(f"- {item}" for item in brief.captions)
    lines.extend(["", "## Social caption", brief.social_caption])
    lines.extend(["", "## Editor checklist"])
    lines.extend(f"- {item}" for item in brief.checklist)
    lines.append("")
    return "\n".join(lines)


def save_brief(article_path: Path, output_dir: Path) -> Path:
    article = article_path.read_text(encoding="utf-8")
    brief = make_brief(article, article_path.stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{article_path.stem}_video_brief.md"
    output_path.write_text(render_markdown(brief), encoding="utf-8")
    return output_path
