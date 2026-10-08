import re


def build_comic_layout(outline: list[dict], images: list[str], story: str) -> list[dict]:
    """Match each outline panel with its image and its slice of the story text."""
    sections = {
        int(m.group(1)): m.group(2).strip()
        for m in re.finditer(r"Panel\s+(\d+)\s*:?\s*(.*?)(?=Panel\s+\d+\s*:|\Z)", story, re.S)
    }
    layout = []
    for panel, image in zip(outline, images):
        text = sections.get(panel["panel"], "")
        caption = re.search(r"Caption:\s*(.*?)(?=Narration:|\Z)", text, re.S)
        narration = re.search(r"Narration:\s*(.*)", text, re.S)
        layout.append(
            {
                "panel": panel["panel"],
                "title": panel["title"],
                "scene": panel["scene"],
                "image_prompt": panel["image_prompt"],
                "image": image,
                "caption": caption.group(1).strip() if caption else "",
                "text": narration.group(1).strip() if narration else text,
            }
        )
    return layout
