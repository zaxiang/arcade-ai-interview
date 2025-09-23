"""
Task 2: Generate Human-Friendly Summary: 
Create a clear, readable summary of what the user was trying to accomplish

- Generates summary via OpenAI or falls back to a concise template
- Writes to summary.md
"""
import os
from pathlib import Path
import requests
from interactions import read_flow, extract_interactions
from dotenv import load_dotenv


def _ai_summary(flow, interactions):
    """
    Call OpenAI to produce a friendly summary.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    name = (flow.get("name") or "Arcade Flow").strip()

    subtitle = ""
    for s in flow.get("steps", []) or []:
        if s.get("type") == "CHAPTER" and s.get("subtitle"):
            subtitle = s.get("subtitle").strip()
            break

    interactions_text = "- " + "\n- ".join(i.description for i in interactions)

    prompt = (
        "Create a clear, concise, human-readable, friendly summary of the user's objective: what the user was trying to accomplish. "
        "Be clear and approachable; avoid technical details. \n\n"
        "Flow name: {}\n"
        "Subtitle: {}\n"
        "Interactions:\n{}\n".format(name, subtitle, interactions_text)
    )

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer {}".format(api_key),
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    if not text:
        raise RuntimeError("Empty AI summary response")
    return text



def _template_summary(flow, interactions):
    """
     Create a clear, readable summary of what the user was trying to accomplish without AI.
    """
    name = (flow.get("name") or "Arcade Flow").strip()

    subtitle = ""
    for s in flow.get("steps", []) or []:
        if s.get("type") == "CHAPTER" and s.get("subtitle"):
            subtitle = s.get("subtitle").strip()
            break

    key = []
    for i in interactions:
        d = (i.description or "").lower()
        if any(k in d for k in ["search", "product", "add to cart", "cart", "coverage", "color", "image", "link"]):
            key.append(i.description)
        if len(key) >= 5:
            break

    parts = []
    parts.append("This flow shows how to {}.".format(name.lower()))
    if subtitle:
        parts.append("The user was trying to ", subtitle)
    if key:
        parts.append("The user {}.".format(", then ".join(k.lower() for k in key)))
    return " ".join(parts)


def generate_summary(flow, interactions):
    """
    Try AI to summarize; on any error, fall back to template.
    """
    try:
        return _ai_summary(flow, interactions)
    except Exception:
        return _template_summary(flow, interactions)

def _write_markdown(summary_text, out_path):
    """
    Write the summary to a markdown file with a simple header.
    """
    p = Path(out_path)
    lines = ["# Summary of what the user was trying to accomplish:", "", summary_text.strip(), ""]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def main():
    """
    Execute Task 2.
    """
    flow = read_flow("flow.json")
    interactions = extract_interactions(flow)

    summary = generate_summary(flow, interactions)

    out_path = _write_markdown(summary, "summary.md")
    print("Wrote {}".format(out_path.resolve()))


if __name__ == "__main__":
    main()


