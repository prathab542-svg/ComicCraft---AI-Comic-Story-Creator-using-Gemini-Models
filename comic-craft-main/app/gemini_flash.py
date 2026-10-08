import json
import os

import google.generativeai as genai

MODEL = os.getenv("GEMINI_FLASH_MODEL", "models/gemini-1.5-flash")
PANELS = 5


def generate_outline(prompt: str, character: str, setting: str, tone: str, style: str) -> list[dict]:
    """Return a structured 5-panel outline: panel, title, scene, image_prompt."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        MODEL, generation_config={"response_mime_type": "application/json"}
    )
    request = (
        f"Create a {PANELS}-panel comic outline.\n"
        f"Story idea: {prompt}\nMain character: {character}\nSetting: {setting}\n"
        f"Tone: {tone}\nArt style: {style}\n\n"
        f"Return a JSON array of exactly {PANELS} objects with keys: "
        '"panel" (integer starting at 1), "title", "scene" (one-paragraph scene description), '
        f'"image_prompt" (a vivid image-generation prompt in {style} style featuring {character}).'
    )
    outline = json.loads(model.generate_content(request).text)
    if not isinstance(outline, list) or not outline:
        raise ValueError("Gemini Flash returned an invalid outline")
    return [
        {
            "panel": i,
            "title": str(p.get("title", f"Panel {i}")),
            "scene": str(p.get("scene", "")),
            "image_prompt": str(p.get("image_prompt", p.get("scene", ""))),
        }
        for i, p in enumerate(outline[:PANELS], 1)
    ]
