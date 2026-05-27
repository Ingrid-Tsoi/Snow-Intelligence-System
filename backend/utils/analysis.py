from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import base64
import io
import json

import geopandas as gpd
import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject


ABS_POLYGON_GEOJSON = Path(
    r"C:\Users\Ingrid\OneDrive\Hong Kong Metropolitan University\8960\Project\06 Website Product\Snow-Intelligence-System\backend\data\polygons\porters.geojson"
)


def month_to_filename(month: str, site: str = "porters") -> str:
    month = month.strip()
    if len(month) != 6 or not month.isdigit():
        raise ValueError(f"Invalid month format: {month}. Expected YYYYMM.")
    return f"{site}_{month}_NDSI.tif"


def resolve_raster_path(month: str, raster_dir: Path, site: str = "porters") -> Path:
    path = raster_dir / month_to_filename(month, site=site)
    if not path.exists():
        raise FileNotFoundError(f"Raster not found: {path}")
    return path


def resolve_polygon_path(base_dir: Path) -> Path:
    """
    Try project-local polygon first, then your absolute Windows path.
    """
    candidates = [
        base_dir / "data" / "polygons" / "porters.geojson",
        ABS_POLYGON_GEOJSON,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Polygon file not found. Place porters.geojson at backend/data/polygons/porters.geojson "
        "or use the absolute Windows path provided in the code."
    )


def _read_raster(path: Path) -> Tuple[np.ndarray, rasterio.io.DatasetReader]:
    src = rasterio.open(path)
    arr = src.read(1, masked=False)
    return arr, src


def _align_to_reference(
    source_arr: np.ndarray,
    source_src: rasterio.io.DatasetReader,
    reference_src: rasterio.io.DatasetReader,
) -> np.ndarray:
    destination = np.zeros((reference_src.height, reference_src.width), dtype=np.float32)

    reproject(
        source=source_arr,
        destination=destination,
        src_transform=source_src.transform,
        src_crs=source_src.crs,
        dst_transform=reference_src.transform,
        dst_crs=reference_src.crs,
        resampling=Resampling.nearest,
        src_nodata=source_src.nodata,
        dst_nodata=0,
    )
    return destination


def raster_to_mask(arr: np.ndarray) -> np.ndarray:
    """
    In this project:
      1 = snow
      0 / nodata / NaN = non-snow
    """
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return (arr > 0).astype(np.uint8)


def compute_pixel_area_km2(transform: rasterio.Affine) -> float:
    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)
    return (pixel_width * pixel_height) / 1_000_000.0


def _load_polygon_geometries(polygon_path: Path, target_crs) -> list:
    gdf = gpd.read_file(polygon_path)

    if gdf.empty:
        raise ValueError(f"Polygon file is empty: {polygon_path}")

    # Clean invalid geometries where possible
    try:
        gdf["geometry"] = gdf.geometry.buffer(0)
    except Exception:
        pass

    if gdf.crs is None:
        # If CRS is missing, assume it matches the raster CRS.
        # This is the least surprising fallback for local project data.
        if target_crs is not None:
            gdf = gdf.set_crs(target_crs)
    elif target_crs is not None and gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)

    geometries = [geom.__geo_interface__ for geom in gdf.geometry if geom is not None and not geom.is_empty]
    if not geometries:
        raise ValueError(f"No valid polygon geometries found in: {polygon_path}")

    return geometries


def _polygon_mask(reference_src, polygon_path: Path) -> np.ndarray:
    geometries = _load_polygon_geometries(polygon_path, reference_src.crs)
    mask = geometry_mask(
        geometries,
        out_shape=(reference_src.height, reference_src.width),
        transform=reference_src.transform,
        invert=True,   # True = inside polygon
        all_touched=False,
    )
    return mask


def _crop_to_mask(arr: np.ndarray, mask: np.ndarray, pad: int = 8):
    rows, cols = np.where(mask)
    if rows.size == 0 or cols.size == 0:
        return arr, mask

    r0 = max(int(rows.min()) - pad, 0)
    r1 = min(int(rows.max()) + pad + 1, arr.shape[0])
    c0 = max(int(cols.min()) - pad, 0)
    c1 = min(int(cols.max()) + pad + 1, arr.shape[1])

    return arr[r0:r1, c0:c1], mask[r0:r1, c0:c1]


def compare_rasters(
    left_path: Path,
    right_path: Path,
    polygon_path: Path,
    output_dir: Optional[Path] = None,
    site: str = "porters",
) -> Dict[str, Any]:
    """
    Compare two monthly snow rasters inside the provided polygon only.
    """
    left_arr, left_src = _read_raster(left_path)
    right_arr, right_src = _read_raster(right_path)

    try:
        # Align right raster to left raster grid if needed.
        if (
            left_src.width != right_src.width
            or left_src.height != right_src.height
            or left_src.crs != right_src.crs
            or left_src.transform != right_src.transform
        ):
            right_arr = _align_to_reference(right_arr, right_src, left_src)

        roi_mask = _polygon_mask(left_src, polygon_path)

        left_mask_full = raster_to_mask(left_arr)
        right_mask_full = raster_to_mask(right_arr)

        # Restrict all calculations to polygon area only
        left_mask = np.where(roi_mask, left_mask_full, 0).astype(np.uint8)
        right_mask = np.where(roi_mask, right_mask_full, 0).astype(np.uint8)

        diff = right_mask.astype(np.int16) - left_mask.astype(np.int16)

        gain_pixels = int(np.sum(diff == 1))
        loss_pixels = int(np.sum(diff == -1))

        roi_pixels = int(np.sum(roi_mask))
        left_snow_pixels = int(np.sum(left_mask == 1))
        right_snow_pixels = int(np.sum(right_mask == 1))

        pixel_area_km2 = compute_pixel_area_km2(left_src.transform)

        roi_area_km2 = roi_pixels * pixel_area_km2
        left_area_km2 = left_snow_pixels * pixel_area_km2
        right_area_km2 = right_snow_pixels * pixel_area_km2
        gain_area_km2 = gain_pixels * pixel_area_km2
        loss_area_km2 = loss_pixels * pixel_area_km2
        net_area_km2 = gain_area_km2 - loss_area_km2

        left_ratio = (left_snow_pixels / roi_pixels * 100.0) if roi_pixels else 0.0
        right_ratio = (right_snow_pixels / roi_pixels * 100.0) if roi_pixels else 0.0
        coverage_delta_pct = right_ratio - left_ratio

        rgba = np.zeros((diff.shape[0], diff.shape[1], 4), dtype=np.uint8)
        rgba[diff == 1] = [0, 120, 255, 190]   # blue gain
        rgba[diff == -1] = [255, 0, 0, 190]    # red loss

        # Keep polygon mask only; outside polygon is transparent
        rgba[~roi_mask] = [255, 255, 255, 0]

        # Crop to polygon bounding box so the preview only shows polygon part
        rgba_cropped, roi_mask_cropped = _crop_to_mask(rgba, roi_mask, pad=8)
        if rgba_cropped.size == 0:
            rgba_cropped = rgba
            roi_mask_cropped = roi_mask

        diff_img = Image.fromarray(rgba_cropped, mode="RGBA")
        buf = io.BytesIO()
        diff_img.save(buf, format="PNG")
        diff_image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        result: Dict[str, Any] = {
            "left": {
                "month": left_path.stem.replace(f"{site}_", "").replace("_NDSI", ""),
                "snow_area_km2": round(float(left_area_km2), 4),
                "ratio": round(float(left_ratio), 2),
                "pixels": left_snow_pixels,
            },
            "right": {
                "month": right_path.stem.replace(f"{site}_", "").replace("_NDSI", ""),
                "snow_area_km2": round(float(right_area_km2), 4),
                "ratio": round(float(right_ratio), 2),
                "pixels": right_snow_pixels,
            },
            "gain": {
                "snow_area_km2": round(float(gain_area_km2), 4),
                "pixels": gain_pixels,
            },
            "loss": {
                "snow_area_km2": round(float(loss_area_km2), 4),
                "pixels": loss_pixels,
            },
            "net": {
                "snow_area_km2": round(float(net_area_km2), 4),
                "pixels": gain_pixels - loss_pixels,
            },
            "roi": {
                "area_km2": round(float(roi_area_km2), 4),
                "pixels": roi_pixels,
            },
            "coverage_delta_pct": round(float(coverage_delta_pct), 2),
            "pixel_area_km2": round(float(pixel_area_km2), 8),
            "diff_image_base64": diff_image_base64,
        }

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            left_month = result["left"]["month"]
            right_month = result["right"]["month"]
            png_path = output_dir / f"compare_{left_month}_{right_month}_{stamp}.png"
            json_path = output_dir / f"compare_{left_month}_{right_month}_{stamp}.json"
            diff_img.save(png_path)
            json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            result["diff_image_path"] = str(png_path)
            result["json_path"] = str(json_path)

        return result
    finally:
        left_src.close()
        right_src.close()
