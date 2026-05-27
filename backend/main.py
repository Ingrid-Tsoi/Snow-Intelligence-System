from __future__ import annotations

from pathlib import Path
import base64
import io
import time

import numpy as np
import rasterio
import torch
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from model.model import UNet
from utils.analysis import compare_rasters, resolve_polygon_path, resolve_raster_path
from utils.inference import run_inference
from utils.postprocessing import stitch_tiles
from utils.preprocessing import crop_tiles

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "snow.pth"
RASTER_DIR = BASE_DIR / "data" / "rasters" / "porters"
OUTPUT_DIR = BASE_DIR / "output" / "analysis"
POLYGON_PATH = resolve_polygon_path(BASE_DIR)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = UNet(n_channels=6, n_classes=2)
ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=False)
model.load_state_dict(ckpt["state_dict"])
model.to(device)
model.eval()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    start_total = time.time()

    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Only .tif / .tiff allowed")

    contents = await file.read()

    try:
        with rasterio.open(io.BytesIO(contents)) as src:
            img = src.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid TIFF: {exc}")

    if img.shape[0] != 6:
        raise HTTPException(status_code=400, detail="Require 6-channel image")

    t1 = time.time()
    img = np.nan_to_num(img)
    img = np.clip(img, 0, 65535)
    img = img / 65535
    img = img.astype(np.float32)
    t2 = time.time()
    print("Preprocessing:", t2 - t1)

    _, H, W = img.shape

    t3 = time.time()
    tiles, coords = crop_tiles(img)
    t4 = time.time()
    print("Crop:", t4 - t3)

    t5 = time.time()
    pred_tiles = run_inference(tiles, model, device)
    t6 = time.time()
    print("Inference:", t6 - t5)

    t7 = time.time()
    mask = stitch_tiles(pred_tiles, coords, H, W)
    t8 = time.time()
    print("Stitch:", t8 - t7)

    png = (mask * 255).astype(np.uint8)
    img_pil = Image.fromarray(png)

    total_pixels = H * W
    snow_pixels = int(mask.sum())
    percentage = (snow_pixels / total_pixels * 100.0) if total_pixels else 0.0

    buf = io.BytesIO()
    img_pil.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode()

    end_total = time.time()
    print("Total:", end_total - start_total)

    return JSONResponse(
        {
            "image": image_base64,
            "total_area": total_pixels,
            "snow_area": snow_pixels,
            "percentage": round(percentage, 2),
        }
    )


@app.get("/compare")
def compare(
    left: str = Query(..., description="Left month in YYYYMM format"),
    right: str = Query(..., description="Right month in YYYYMM format"),
):
    try:
        left_path = resolve_raster_path(left, RASTER_DIR)
        right_path = resolve_raster_path(right, RASTER_DIR)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        result = compare_rasters(
            left_path=left_path,
            right_path=right_path,
            polygon_path=POLYGON_PATH,
            output_dir=OUTPUT_DIR,
            site="porters",
        )
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {exc}")
