from __future__ import annotations

import argparse
from pathlib import Path

from .brief import save_brief
from .dashboard import write_dashboard
from .exporter import export_package
from .feed import merge_all_feeds, merge_feed
from .templates import render_template_list


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="neuse-voice",
        description="Create Neuse News short-video production briefs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    brief = subparsers.add_parser("brief", help="Create a production brief from article text.")
    brief.add_argument("article", type=Path, help="Path to a plain-text article file.")
    brief.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/scripts"),
        help="Folder for generated production briefs.",
    )

    dashboard = subparsers.add_parser("dashboard", help="Create the Local Voice Engine dashboard.")
    dashboard.add_argument(
        "--data",
        type=Path,
        default=Path("data/video_packages.json"),
        help="Path to video package data.",
    )
    dashboard.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/dashboard"),
        help="Folder for dashboard files.",
    )

    export = subparsers.add_parser("export", help="Export one story package for video production.")
    export.add_argument("package_id", help="Video package ID from data/video_packages.json.")
    export.add_argument(
        "--data",
        type=Path,
        default=Path("data/video_packages.json"),
        help="Path to video package data.",
    )
    export.add_argument(
        "--output-root",
        type=Path,
        default=Path("output/videos"),
        help="Folder for exported video packages.",
    )

    feed = subparsers.add_parser("import-feed", help="Import recent Neuse News RSS stories.")
    feed.add_argument(
        "--data",
        type=Path,
        default=Path("data/video_packages.json"),
        help="Path to video package data.",
    )
    feed.add_argument("--limit", type=int, default=10, help="Number of RSS items to inspect.")

    all_feeds = subparsers.add_parser("import-all-feeds", help="Import recent stories from every configured brand feed.")
    all_feeds.add_argument(
        "--data",
        type=Path,
        default=Path("data/video_packages.json"),
        help="Path to video package data.",
    )
    all_feeds.add_argument("--limit", type=int, default=5, help="Number of RSS items to inspect per brand.")

    subparsers.add_parser("templates", help="List available video story templates.")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "brief":
        output_path = save_brief(args.article, args.output_dir)
        print(f"Created {output_path}")
    elif args.command == "dashboard":
        output_path = write_dashboard(args.data, args.output_dir)
        print(f"Created {output_path}")
    elif args.command == "export":
        output_path = export_package(args.data, args.package_id, args.output_root)
        print(f"Created {output_path}")
    elif args.command == "import-feed":
        added = merge_feed(args.data, args.limit)
        print(f"Imported feed. Added {added} new packages.")
    elif args.command == "import-all-feeds":
        results = merge_all_feeds(args.data, args.limit)
        for brand_id, added in results.items():
            print(f"{brand_id}: added {added}")
    elif args.command == "templates":
        print(render_template_list(), end="")


if __name__ == "__main__":
    main()
