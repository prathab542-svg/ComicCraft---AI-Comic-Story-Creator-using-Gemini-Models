import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.image_generator import _get_pipe  # noqa: E402
from app.routes import router  # noqa: E402  (needs env loaded first)

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="ComicCraft")
threading.Thread(target=_get_pipe, daemon=True).start()  # warm up Stable Diffusion in the background
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.include_router(router)
