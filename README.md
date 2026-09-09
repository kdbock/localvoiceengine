# Local Voice Engine

Local Voice Engine is a private newsroom studio for producing short-form news
videos with AI-assisted scripts, voiceovers, captions, brand kits and visual
screens.

The goal is not to fully automate publishing. The goal is to give the editor a
fast review-and-approve workflow from each article:

- choose a brand
- choose a news article
- choose a video template
- draft voiceover from the article
- edit visual screens separately from the audio
- upload article images and headshots
- approve the text
- create the video

## Current status

The local studio runs on macOS and uses the built-in Mac voice tool for the
current voiceover pipeline. Qwen voice support is still planned as a provider
option.

The voice provider is intentionally configurable because Qwen currently has more
than one path:

- Qwen3-TTS open-source models from QwenLM
- Alibaba Cloud Model Studio Qwen Audio TTS hosted models
- future local or hosted providers

Sources checked Sept. 9, 2026:

- https://github.com/QwenLM/Qwen3-TTS
- https://qwen.ai/blog?id=qwen3tts-0115
- https://www.alibabacloud.com/help/en/model-studio/realtime-tts-user-guide

## Quick Start

From this folder:

```bash
./setup_local.sh
```

Create a production brief from a pasted article:

```bash
python -m qwen_voice_engine brief examples/sample_article.txt
```

Output goes to `output/scripts/`.

Create the static dashboard files:

```bash
./run_dashboard.sh
```

Open `output/dashboard/index.html` in a browser.

Run the interactive studio:

```bash
./run_studio.sh
```

Then open `http://127.0.0.1:8765`.

The studio workflow is:

1. Pick a news article.
2. Select a video template.
3. Review and approve the text.
4. Create the video.

Import recent RSS stories and image URLs from all configured brands:

```bash
./run_import_all_feeds.sh --limit 10
```

Export one story into a production folder:

```bash
./run_export.sh 2026-09-09-autozone
```

The export creates:

- `script.txt`
- `captions.srt`
- `shotlist.md`
- `frames/*.svg`
- `frames/*.png`
- `voiceover.aiff` when the Mac voice tool is available
- `video.mp4` when the local video dependencies are installed

Story images come from each brand's RSS feed when available. The studio also
supports one headshot and up to three uploaded article images per story.

## Recommended workflow

1. Open the studio.
2. Pick the brand workspace.
3. Import stories if needed.
4. Pick an article.
5. Click `Draft voiceover from article`.
6. Edit the voiceover text.
7. Edit each visual screen.
8. Upload article images or a headshot if needed.
9. Approve the text.
10. Create the video.

## Story templates

The core newsroom templates are in `templates/`:

- `meeting_in_a_minute_template.md`
- `crime_story_template.md`
- `news_story_template.md`
- `featured_story_template.md`

The engine-ready version is `templates/story_templates.json`.

To list them:

```bash
PYTHONPATH=src python3 -m qwen_voice_engine.cli templates
```

## Video formats

Start with these recurring formats:

- Meeting in a minute
- Crime story
- News story
- Featured story
- Faces of the story

See `templates/video_formats.md`.

For free background footage, see `templates/pexels_backgrounds.md`.

## Editorial rules

- Follow AP style.
- Use sentence-style headlines.
- Avoid hype, speculation and loaded language.
- Crime videos must say what officials reported and what remains unconfirmed.
- Do not use AI voice cloning without documented consent.
- Do not fully automate posts involving children, deaths, arrests, politics or
  other sensitive subjects.

## Product Idea

Local Voice Engine repurposes the Listening Room concept for local news. Instead
of tracking audiobook chapters, it tracks short news video packages from story
selection to editor approval, voiceover, visual assembly and posting.
