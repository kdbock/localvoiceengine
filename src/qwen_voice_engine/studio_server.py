from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import cgi
import json
import mimetypes
from pathlib import Path
import threading
import urllib.parse

from .dashboard import write_dashboard
from .exporter import draft_narration_lines, export_package, narration_lines, visual_lines
from .brands import load_brand_kits
from .feed import merge_all_feeds
from .templates import load_story_templates


ROOT = Path.cwd()
DATA_PATH = ROOT / "data" / "video_packages.json"
DASHBOARD_DIR = ROOT / "output" / "dashboard"
UPLOAD_DIR = ROOT / "input" / "uploads"
RENDER_LOCK = threading.Lock()


def load_packages() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def save_packages(packages: list[dict]) -> None:
    DATA_PATH.write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")


def find_package(packages: list[dict], package_id: str) -> dict:
    for package in packages:
        if package.get("id") == package_id:
            return package
    raise KeyError(package_id)


def script_for_package(package: dict) -> list[str]:
    return narration_lines(package)


class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/videos/"):
            video_path = ROOT / "output" / parsed.path.lstrip("/")
            if not video_path.exists() or not video_path.is_file():
                self.send_json({"ok": False, "error": "Video not found"}, 404)
                return
            content_type = mimetypes.guess_type(video_path.name)[0] or "application/octet-stream"
            body = video_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/packages":
            packages = load_packages()
            for package in packages:
                package["suggested_script_lines"] = script_for_package(package)
            self.send_json(packages)
            return
        if parsed.path == "/api/templates":
            self.send_json(load_story_templates())
            return
        if parsed.path == "/api/brands":
            self.send_json(load_brand_kits())
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/approve":
            body = self.read_json_body()
            packages = load_packages()
            package = find_package(packages, body["id"])
            package["format"] = body.get("format", package.get("format", "News story"))
            package["brand_id"] = body.get("brand_id", package.get("brand_id", "neuse-news"))
            package["approved_script_lines"] = [
                line.strip() for line in body.get("script_lines", []) if line.strip()
            ]
            package["approved_visual_lines"] = [
                str(line).strip() for line in body.get("visual_lines", [])
            ]
            package["visual_text_mode"] = body.get("visual_text_mode", "auto")
            package["status"] = "approved"
            save_packages(packages)
            write_dashboard(DATA_PATH, DASHBOARD_DIR)
            self.send_json({"ok": True, "package": package})
            return
        if parsed.path == "/api/upload-images":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                },
            )
            package_id = str(form.getfirst("id", ""))
            packages = load_packages()
            package = find_package(packages, package_id)
            upload_dir = UPLOAD_DIR / package_id
            upload_dir.mkdir(parents=True, exist_ok=True)

            headshot = form["headshot"] if "headshot" in form else None
            if headshot is not None and getattr(headshot, "filename", ""):
                suffix = Path(headshot.filename).suffix.lower() or ".jpg"
                path = upload_dir / f"headshot{suffix}"
                path.write_bytes(headshot.file.read())
                package["headshot_image_path"] = str(path)

            article_fields = form["article_images"] if "article_images" in form else []
            if not isinstance(article_fields, list):
                article_fields = [article_fields]
            article_paths = []
            for index, field in enumerate(article_fields[:3], 1):
                if not getattr(field, "filename", ""):
                    continue
                suffix = Path(field.filename).suffix.lower() or ".jpg"
                path = upload_dir / f"article-{index}{suffix}"
                path.write_bytes(field.file.read())
                article_paths.append(str(path))
            if article_paths:
                package["article_image_paths"] = article_paths

            save_packages(packages)
            write_dashboard(DATA_PATH, DASHBOARD_DIR)
            self.send_json({"ok": True, "package": package})
            return
        if parsed.path == "/api/draft":
            body = self.read_json_body()
            packages = load_packages()
            package = dict(find_package(packages, body["id"]))
            package["format"] = body.get("format", package.get("format", "News story"))
            package["brand_id"] = body.get("brand_id", package.get("brand_id", "neuse-news"))
            package.pop("approved_script_lines", None)
            package.pop("approved_visual_lines", None)
            package.pop("visual_text_mode", None)
            script_lines = draft_narration_lines(package)
            self.send_json(
                {
                    "ok": True,
                    "script_lines": script_lines,
                    "visual_lines": visual_lines(package, script_lines),
                }
            )
            return
        if parsed.path == "/api/render":
            body = self.read_json_body()
            package_id = body["id"]
            if not RENDER_LOCK.acquire(blocking=False):
                self.send_json(
                    {
                        "ok": False,
                        "error": "Another video is still being created. Wait for it to finish, then try again.",
                    },
                    409,
                )
                return
            try:
                package_dir = export_package(DATA_PATH, package_id, ROOT / "output" / "videos")
            except Exception as exc:
                self.send_json({"ok": False, "error": f"Video render failed: {exc}"}, 500)
                return
            finally:
                RENDER_LOCK.release()
            video_path = package_dir / "video.mp4"
            if not video_path.exists():
                self.send_json({"ok": False, "error": "Video render did not create an MP4."}, 500)
                return
            version = int(video_path.stat().st_mtime)
            self.send_json(
                {
                    "ok": True,
                    "video_path": str(video_path),
                    "video_url": f"/videos/{package_id}/video.mp4?v={version}",
                }
            )
            return
        if parsed.path == "/api/import-all":
            body = self.read_json_body()
            results = merge_all_feeds(DATA_PATH, int(body.get("limit", 5)))
            write_dashboard(DATA_PATH, DASHBOARD_DIR)
            self.send_json({"ok": True, "results": results})
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    write_dashboard(DATA_PATH, DASHBOARD_DIR)
    server = ThreadingHTTPServer((host, port), StudioHandler)
    print(f"Local Voice Engine running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
