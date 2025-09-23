## Project overview

This tool analyzes an Arcade `flow.json` and produces:
- Interactions: a human-readable list of user actions
- Summary: a concise description of what the user was trying to accomplish
- Social image: a creative shareable image representing the flow

Outputs are written to the project root as `interactions.md`, `summary.md`, and `social.png`.

## Prerequisites
- Python 3.10+
- An OpenAI API key in local `.env` file with:
  - `OPENAI_API_KEY=sk-...`

## Install
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run each task

### Task 1 — Identify User Interactions
Generates `interactions.md` and prints the lines to the console.
```bash
python interactions_report.py
```

### Task 2 — Generate Human-Friendly Summary (AI with fallback)
Writes `summary.md`. Defaults to AI; falls back to a template if the API fails.
```bash
python ai_summary.py
```

### Task 3 — Create a Social Media Image (AI)
Creates `social.png`. Uses OpenAI Images (1024x1024), then letterboxes to 1200x630 for social.
```bash
python ai_image.py
```

## End-to-end quickstart
```bash
python interactions_report.py && python ai_summary.py && python ai_image.py
```

## How each task is approached
- Interactions: I parse `capturedEvents` in chronological order and enrich click events using the corresponding IMAGE-step `clickContext` .
- Summary: I use OpenAI (chat completions) to produce a clear description; if the AI call fails, it will fall back to a concise template-based summary.
- Social image: I build a prompt from the product and color cues found in interactions in step1 and include subtle UI metaphors (search bar, product card, primary action button, cart badge). I then generate an image via OpenAI Images at 1024×1024 and letterbox it to 1200×630 for sharing.

## Potential improvements
- Generalize parsing across more Arcade step types (beyond IMAGE/VIDEO/CHAPTER) and improve fuzzy mapping between `capturedEvents` and steps.
- Smarter color/product extraction.
- Caching of AI responses and images using content hashes (to reduce cost and re-runs).


