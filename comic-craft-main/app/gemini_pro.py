import json
import os

import google.generativeai as genai

MODEL = os.getenv("GEMINI_PRO_MODEL", "models/gemini-1.5-pro")


def generate_story(outline: list[dict], character: str, tone: str) -> str:
    """Expand the outline into narration and dialogue; one text block, panels delimited by 'Panel N:'."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(MODEL)
    request = (
        f"Write a {tone} comic story featuring {character} from this panel outline:\n"
        f"{json.dumps(outline, indent=2)}\n\n"
        "For every panel use exactly this plain-text format (no markdown):\n"
        "Panel <number>:\n"
        "Caption: <one short ambient line>\n"
        "Narration: <2-4 sentences of action, emotion and character dialogue>\n"
    )
    return model.generate_content(request).text
