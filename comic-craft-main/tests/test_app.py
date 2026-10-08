from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app import exporters, routes
from app.layout_builder import build_comic_layout

OUTLINE = [
    {"panel": i, "title": f"Title {i}", "scene": f"Scene {i}", "image_prompt": f"prompt {i}"}
    for i in range(1, 6)
]
STORY = "\n".join(f"Panel {i}:\nCaption: Cap {i}\nNarration: Text {i}" for i in range(1, 6))
IMAGES = [f"/docs/screenshots/generated_panel.png" for _ in OUTLINE]


def make_client():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=exporters.ROOT / "static"), name="static")
    app.include_router(routes.router)
    return TestClient(app)


def patch_ai(monkeypatch):
    monkeypatch.setattr(routes, "generate_outline", lambda *a: OUTLINE)
    monkeypatch.setattr(routes, "generate_story", lambda *a: STORY)
    monkeypatch.setattr(routes, "generate_image", lambda p: IMAGES[0])
    monkeypatch.setattr(routes, "save_pdf", lambda layout: "/static/exports/test.pdf")


def test_layout_matches_panels_to_story():
    layout = build_comic_layout(OUTLINE, IMAGES, STORY)
    assert len(layout) == 5
    assert layout[2]["caption"] == "Cap 3" and layout[2]["text"] == "Text 3"
    assert layout[0]["image"] == IMAGES[0]


def test_layout_handles_missing_story():
    layout = build_comic_layout(OUTLINE, IMAGES, "")
    assert all(p["caption"] == "" and p["text"] == "" for p in layout)


def test_save_pdf_one_page_per_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(exporters, "EXPORTS_DIR", tmp_path)
    url = exporters.save_pdf(build_comic_layout(OUTLINE, IMAGES, STORY))
    pdf = tmp_path / url.rsplit("/", 1)[1]
    assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF")
    assert pdf.read_bytes().count(b"/Type /Page\n") + pdf.read_bytes().count(b"/Type /Page ") >= 5


def test_home_page():
    r = make_client().get("/")
    assert r.status_code == 200 and "ComicCraft" in r.text


def test_generate_form_shows_preview(monkeypatch):
    patch_ai(monkeypatch)
    r = make_client().post("/generate", data=dict(prompt="p", character="Rio", setting="forest", tone="funny", style="anime"))
    assert r.status_code == 200 and "Title 1" in r.text and "Title 5" in r.text


def test_generate_json(monkeypatch):
    patch_ai(monkeypatch)
    body = dict(prompt="p", character="Rio", setting="forest", tone="funny", style="anime")
    r = make_client().post("/generate-comic/json", json=body)
    assert r.status_code == 200
    assert len(r.json()["layout"]) == 5 and r.json()["pdf_path"].endswith(".pdf")


def test_generate_requires_fields():
    assert make_client().post("/generate", data={"prompt": "only"}).status_code == 422


def test_generation_error_returns_500(monkeypatch):
    def boom(*a):
        raise RuntimeError("429 quota")
    monkeypatch.setattr(routes, "generate_outline", boom)
    r = make_client().post("/generate-comic/json", json=dict(prompt="p", character="c", setting="s", tone="t", style="y"))
    assert r.status_code == 500 and "quota" in r.json()["detail"]


def test_export_success_page():
    r = make_client().get("/export-success", params={"pdf": "/static/exports/x.pdf"})
    assert r.status_code == 200 and "x.pdf" in r.text


def test_test_image_endpoint(monkeypatch):
    monkeypatch.setattr(routes, "generate_image", lambda p: "/static/panels/a.png")
    assert make_client().get("/test-image").json() == {"image": "/static/panels/a.png"}
