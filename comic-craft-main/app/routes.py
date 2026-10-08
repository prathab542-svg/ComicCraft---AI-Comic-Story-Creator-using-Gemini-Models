from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


class PromptRequest(BaseModel):
    prompt: str
    character: str
    setting: str
    tone: str
    style: str


def create_comic(prompt: str, character: str, setting: str, tone: str, style: str) -> tuple[list[dict], str]:
    try:
        outline = generate_outline(prompt, character, setting, tone, style)
        with ThreadPoolExecutor() as pool:  # story text overlaps with image generation
            story_job = pool.submit(generate_story, outline, character, tone)
            images = [generate_image(p["image_prompt"]) for p in outline]
            story = story_job.result()
        layout = build_comic_layout(outline, images, story)
        return layout, save_pdf(layout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Comic generation failed: {exc}") from exc


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    prompt: str = Form(...),
    character: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...),
):
    layout, pdf_path = create_comic(prompt, character, setting, tone, style)
    return templates.TemplateResponse(request, "comic_preview.html", {"layout": layout, "pdf_path": pdf_path})


@router.post("/generate-comic/json")
def generate_json(body: PromptRequest):
    layout, pdf_path = create_comic(body.prompt, body.character, body.setting, body.tone, body.style)
    return {"layout": layout, "pdf_path": pdf_path}


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request, pdf: str = ""):
    return templates.TemplateResponse(request, "export_success.html", {"pdf_path": pdf})


@router.get("/test-image")
def test_image(prompt: str = "a brave fox in an enchanted forest"):
    try:
        return {"image": generate_image(prompt)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}") from exc
