"""
Logic for reading flow JSON and extracting user interactions.
"""

from models import Interaction
import json
from pathlib import Path


def read_flow(path):
    """
    Read a flow JSON file from disk.

    Args: path: Path to the flow.json file.
    Returns: dict: Parsed JSON content of the flow.
    """
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _index_steps_by_id(flow):
    """
    Build a dictionary for O(1) lookup of steps by id.
    """
    by_id = {}
    for s in flow.get("steps", []):
        sid = s.get("id")
        if sid:
            by_id[sid] = s
    return by_id

def _describe_click_from_step(step):
    """
    Convert a step with clickContext into Interaction object.
    """
    page = step.get("pageContext") or {}
    title = page.get("title")
    url = page.get("url")
    click_ctx = step.get("clickContext") or {}

    element_type = click_ctx.get("elementType")
    text = (click_ctx.get("text") or "").strip()
    css = (click_ctx.get("cssSelector") or "").lower()

    if element_type == "other" and "search" in css:
        return Interaction("click", "Clicked search input", title, url)

    if element_type == "image" and text:
        return Interaction("click", "Clicked product/image '{}'".format(text), title, url)

    if element_type == "button" and text:
        return Interaction("click", "Clicked '{}' button".format(text), title, url)

    if element_type == "link":
        return Interaction("navigate", "Opened cart", title, url)

    # Fallbacks
    if text:
        return Interaction("click", "Clicked '{}'".format(text), title, url)
    return Interaction("click", "Clicked", title, url)


def extract_interactions(flow):
    """
    Produce a time-ordered list of interactions from capturedEvents.
    """
    interactions = []
    steps_by_id = _index_steps_by_id(flow)
    events = flow.get("capturedEvents", []) or []

    steps_by_id = _index_steps_by_id(flow)

    def _time(ev):
        # clicks: timeMs; typing/scrolling: startTimeMs; default 0
        return ev.get("timeMs") or ev.get("startTimeMs") or 0

    events = sorted(events, key=_time)

    for ev in events:
        etype = ev.get("type")

        if etype == "typing":
            interactions.append(Interaction("typing", "Typed in search bar"))
            continue

        if etype == "scrolling":
            interactions.append(Interaction("scrolling", "Scrolled the page"))
            continue

        if etype == "click":
            click_id = ev.get("clickId")
            step = steps_by_id.get(click_id)
            if step and step.get("type") == "IMAGE" and step.get("clickContext"):
                interactions.append(_describe_click_from_step(step))
            else:
                interactions.append(Interaction("click", "Clicked"))
            continue

        # Ignore "dragging" event type because this is not an interaction

    return interactions

