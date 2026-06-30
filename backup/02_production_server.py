#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux", "fastapi", "uvicorn", "pydantic"]
# ///
"""
FastAPI OpenAI-compatible image generation server

Section reference: Report §5.2 — Production server
Expected runtime on M4 Pro 24 GB: ~50 ms cold-start per request after model load
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

from __future__ import annotations

import base64
import io
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mflux.models.z_image import ZImageTurbo


# Model registry — load once at startup, reuse across requests.
# Add more models here as you scale.
MODELS: dict[str, ZImageTurbo] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Pre-load models at startup (~30-60 seconds for Z-Image Turbo int8)
    print("Loading z-image-turbo (int8)... ~30-60s")
    MODELS["z-image-turbo"] = ZImageTurbo(quantize=8)
    print(f"Loaded models: {list(MODELS.keys())}")
    yield
    MODELS.clear()


app = FastAPI(title="mflux image server", lifespan=lifespan)


class GenerateRequest(BaseModel):
    model: str = Field(..., examples=["z-image-turbo"])
    prompt: str
    seed: int = 42
    steps: int = 9
    width: int = 1024
    height: int = 1024


class GenerateResponse(BaseModel):
    data: list[dict[str, str]]


@app.post("/v1/images/generations", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    """OpenAI-compatible image generation endpoint."""
    if req.model not in MODELS:
        available = list(MODELS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Model '{req.model}' not loaded. Available: {available}",
        )
    model = MODELS[req.model]
    image = model.generate_image(
        prompt=req.prompt,
        seed=req.seed,
        num_inference_steps=req.steps,
        width=req.width,
        height=req.height,
    )
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return GenerateResponse(data=[{"b64_json": b64}])


@app.get("/v1/models")
async def list_models() -> dict[str, list[str]]:
    return {"models": list(MODELS.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
