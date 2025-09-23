"""
Task 3: Create a social media image that represents the flow using AI.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests

import base64
from PIL import Image
from io import BytesIO

from interactions import read_flow, extract_interactions


def _extract_product_and_colors(interactions):
    """
    Pull a product name and a few colors from interaction descriptions.
    """
    product = None
    colors = []
    for i in interactions:
        desc = (i.description or "").strip()
        lower = desc.lower()

        if "clicked product" in lower or "image '" in lower or "clicked '" in lower:
            if "'" in desc:
                try:
                    product = desc.split("'")[1]
                except Exception:
                    pass

        # a very naive color extraction
        # TODO: smarter way to pull color information
        for c in ["red", "blue", "pink", "green", "black", "white", "silver", "gray", "grey", "yellow", "purple"]:
            if c in lower and c.capitalize() not in colors:
                colors.append(c.capitalize())

    return product, colors

def _build_image_prompt(flow, interactions, summary_hint=None):
    """
    Build a prompt for a social image.
    """
    name = (flow.get("name") or "User Flow").strip()

    # few action cues from interactions to hint UI metaphors
    has_search = any("search" in (i.description or "").lower() for i in interactions)
    has_cart = any("cart" in (i.description or "").lower() for i in interactions)
    has_add = any("add to cart" in (i.description or "").lower() or "clicked 'add" in (i.description or "").lower() for i in interactions)
    has_nav = any(i.kind.name.lower() == "navigate" if hasattr(i.kind, "name") else i.kind == "navigate" for i in interactions)
    has_form = any("typed" in (i.description or "").lower() for i in interactions)

    ui_bits = []
    if has_search:
        ui_bits.append("a search bar")
    if has_add:
        ui_bits.append("a prominent action button")
    if has_cart:
        ui_bits.append("a generic cart or list icon")
    if has_nav:
        ui_bits.append("a simple navigation header")
    if has_form:
        ui_bits.append("a minimal input field")

    metaphors = ""
    if ui_bits:
        metaphors = " Include subtle UI metaphors such as {}.".format(", ".join(ui_bits))

    # Optional product/color hints
    product, colors = _extract_product_and_colors(interactions)
    product_hint = (" Emphasize a generic representation of '{}', without logos or trademarks.".format(product)) if product else ""
    color_hint = (" Consider accents or swatches for {}.".format(", ".join(colors))) if colors else ""

    narrative = summary_hint or name

    return (
        "Design a creative, high-quality, engaging social-media hero image (1200x630) that visually represents the following user flow, and also make sure it would drive engagement. "
        "Keep it abstract and product-agnostic (no real logos or brand marks). "
        "Use clean composition, balanced layout, and a modern palette suitable for social sharing."
        + metaphors + product_hint + color_hint +
        "Avoid text-heavy designs; prefer clear shapes/icons and generous whitespace. "
        "Narrative hint: {}.".format(narrative)
    )


def _generate_image(prompt, output_path):
    """
    Call OpenAI Images API to generate an image from the prompt.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": "Bearer {}".format(api_key),
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        },
        timeout=120,
    )
    if r.status_code >= 400:
        raise RuntimeError("OpenAI image error {}: {}".format(r.status_code, r.text))

    data = r.json()
    b64 = data["data"][0]["b64_json"]
    raw = base64.b64decode(b64)

    # Convert to 1200x630 canvas (letterbox preserving aspect)
    src = Image.open(BytesIO(raw)).convert("RGB")
    target_w, target_h = 1200, 630
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_w = target_w
        new_h = int(new_w / src_ratio)
    else:
        new_h = target_h
        new_w = int(new_h * src_ratio)

    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), (250, 250, 253))
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return Path(output_path)


def main():
    """
    Execute Task 3.
    """
    print("========== Generating Social Media Image ==========")
    flow = read_flow("flow.json")
    interactions = extract_interactions(flow)

    prompt = _build_image_prompt(flow, interactions)
    out_path = _generate_image(prompt, "social.png")
    print("Wrote {}".format(out_path.resolve()))


if __name__ == "__main__":
    main()