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

    # CSS selector heuristics when text is empty
    if not text and css:
        if any(k in css for k in ["addtocart", "add-to-cart", "add_to_cart", "addtocartbutton", "addtobag", "add-to-bag"]):
            return Interaction("click", "Clicked 'Add to cart' button", title, url)
        if any(k in css for k in ["checkout", "proceed-to-checkout", "proceed_to_checkout", "begin-checkout", "begin_checkout"]):
            return Interaction("click", "Clicked 'Checkout'", title, url)
        if "search" in css:
            return Interaction("click", "Clicked search input", title, url)
        if "filter" in css:
            return Interaction("click", "Opened filters", title, url)
        if any(k in css for k in ["next", "continue", "continue-button", "continue_btn"]):
            return Interaction("click", "Clicked 'Next'", title, url)
        if "submit" in css:
            return Interaction("click", "Clicked 'Submit'", title, url)

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

    last_kind = None
    for ev in events:
        etype = ev.get("type")

        if etype == "typing":
            interactions.append(Interaction("typing", "Typed in search bar"))
            last_kind = "typing"
            continue

        if etype == "scrolling":
            # collapse consecutive scrolling to reduce noise
            if last_kind != "scrolling":
                interactions.append(Interaction("scrolling", "Scrolled the page"))
                last_kind = "scrolling"
            continue

        if etype == "click":
            click_id = ev.get("clickId")
            step = steps_by_id.get(click_id)
            if step and step.get("type") == "IMAGE":
                if step.get("clickContext"):
                    interactions.append(_describe_click_from_step(step))
                else:
                    # Fallback to hotspot hint if available
                    page = step.get("pageContext") or {}
                    title = page.get("title")
                    url = page.get("url")
                    hotspots = step.get("hotspots") or []
                    label = hotspots[0].get("label") if hotspots else None
                    if label:
                        interactions.append(Interaction("hint", label, title, url))
                    else:
                        interactions.append(Interaction("click", "Clicked", title, url))
            else:
                interactions.append(Interaction("click", "Clicked"))
            last_kind = "click"
            continue

        # Ignore "dragging" event type because this is not an interaction

    return interactions

