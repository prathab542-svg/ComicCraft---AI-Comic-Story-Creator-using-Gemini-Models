import re
from pathlib import Path

PANELS_DIR = Path(__file__).resolve().parent.parent / "static" / "panels"
MODEL_ID = "runwayml/stable-diffusion-v1-5"

_pipe = None


def _get_pipe():
    global _pipe
    if _pipe is None:
        import torch
        from diffusers import StableDiffusionPipeline

        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        dtype = torch.float32 if device == "cpu" else torch.float16
        _pipe = StableDiffusionPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype).to(device)
        _pipe.enable_attention_slicing()
    return _pipe


def generate_image(prompt: str) -> str:
    """Generate a comic-style image, save to static/panels, return its URL path."""
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", prompt).strip("_")[:60] or "panel"
    path = PANELS_DIR / f"{safe}.png"
    image = _get_pipe()(prompt + ", comic book illustration, detailed", num_inference_steps=25).images[0]
    image.save(path)
    return f"/static/panels/{path.name}"
