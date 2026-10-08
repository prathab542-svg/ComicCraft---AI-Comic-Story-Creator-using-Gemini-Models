import json
from types import SimpleNamespace

import pytest

from app import gemini_flash, gemini_pro, image_generator
from app.layout_builder import build_comic_layout

OUTLINE = [
    {"panel": i, "title": f"Title {i}", "scene": f"Scene {i}", "image_prompt": f"prompt {i}"}
    for i in range(1, 4)
]


class FakeModel:
    """Stands in for genai.GenerativeModel and records the request."""

    last = None

    def __init__(self, name, generation_config=None):
        self.name = name
        self.generation_config = generation_config

    def generate_content(self, request):
        FakeModel.last = request
        return SimpleNamespace(text=FakeModel.reply)


@pytest.fixture
def fake_genai(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    for module in (gemini_flash, gemini_pro):
        monkeypatch.setattr(module.genai, "configure", lambda **kw: None)
        monkeypatch.setattr(module.genai, "GenerativeModel", FakeModel)
    return FakeModel


def test_outline_normalises_panel_numbers_and_defaults(fake_genai):
    fake_genai.reply = json.dumps([{"panel": 9, "title": "A", "scene": "S"}, {"scene": "Only scene"}])
    outline = gemini_flash.generate_outline("idea", "Rio", "forest", "funny", "anime")
    assert [p["panel"] for p in outline] == [1, 2]
    assert outline[0]["image_prompt"] == "S"  # falls back to the scene
    assert outline[1]["title"] == "Panel 2"


def test_outline_is_capped_at_five_panels(fake_genai):
    fake_genai.reply = json.dumps([{"title": str(i), "scene": "s", "image_prompt": "p"} for i in range(8)])
    assert len(gemini_flash.generate_outline("i", "c", "s", "t", "st")) == gemini_flash.PANELS


@pytest.mark.parametrize("reply", ["[]", "{}", '"text"'])
def test_outline_rejects_invalid_json_shape(fake_genai, reply):
    fake_genai.reply = reply
    with pytest.raises(ValueError):
        gemini_flash.generate_outline("i", "c", "s", "t", "st")


def test_outline_prompt_contains_user_choices(fake_genai):
    fake_genai.reply = json.dumps([{"title": "t", "scene": "s", "image_prompt": "p"}])
    gemini_flash.generate_outline("a lost robot", "Rio", "desert", "dark", "noir")
    for word in ("a lost robot", "Rio", "desert", "dark", "noir"):
        assert word in fake_genai.last


def test_outline_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(KeyError):
        gemini_flash.generate_outline("i", "c", "s", "t", "st")


def test_story_returns_model_text_and_includes_outline(fake_genai):
    fake_genai.reply = "Panel 1:\nCaption: c\nNarration: n"
    story = gemini_pro.generate_story(OUTLINE, "Rio", "funny")
    assert story == fake_genai.reply
    assert "Title 2" in fake_genai.last and "Rio" in fake_genai.last and "funny" in fake_genai.last


def test_layout_truncates_to_shortest_input():
    layout = build_comic_layout(OUTLINE, ["/a.png", "/b.png"], "")
    assert [p["panel"] for p in layout] == [1, 2]


def test_layout_without_caption_keeps_whole_section_as_text():
    layout = build_comic_layout(OUTLINE, ["/a.png"] * 3, "Panel 1: just some prose\nPanel 2: more prose")
    assert layout[0]["caption"] == "" and layout[0]["text"] == "just some prose"
    assert layout[1]["text"] == "more prose"


def test_layout_tolerates_markdown_free_spacing_variants():
    story = "Panel 1\nCaption: X\nNarration: Y\nPanel 2:\nCaption: Z\nNarration: W"
    layout = build_comic_layout(OUTLINE[:2], ["/a.png"] * 2, story)
    assert layout[1]["caption"] == "Z"


def test_layout_copies_outline_fields():
    layout = build_comic_layout(OUTLINE, ["/a.png"] * 3, "")
    assert layout[1]["title"] == "Title 2" and layout[1]["image_prompt"] == "prompt 2"


class FakePipe:
    def __init__(self):
        self.prompt = None

    def __call__(self, prompt, num_inference_steps):
        self.prompt, self.steps = prompt, num_inference_steps
        from PIL import Image

        return SimpleNamespace(images=[Image.new("RGB", (8, 8), "red")])


def test_generate_image_saves_png_with_safe_name(tmp_path, monkeypatch):
    pipe = FakePipe()
    monkeypatch.setattr(image_generator, "PANELS_DIR", tmp_path)
    monkeypatch.setattr(image_generator, "_get_pipe", lambda: pipe)
    url = image_generator.generate_image("A fox! in <the> forest/..")
    name = url.rsplit("/", 1)[1]
    assert name == "A_fox_in_the_forest.png" and (tmp_path / name).exists()
    assert pipe.steps == 25 and pipe.prompt.startswith("A fox!")


def test_generate_image_name_is_truncated_and_has_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(image_generator, "PANELS_DIR", tmp_path)
    monkeypatch.setattr(image_generator, "_get_pipe", lambda: FakePipe())
    long_name = image_generator.generate_image("x" * 200).rsplit("/", 1)[1]
    assert len(long_name) <= 64
    assert image_generator.generate_image("!!!").endswith("/panel.png")
