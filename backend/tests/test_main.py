import io
import base64

import numpy as np
import pytest
import rasterio
import torch
import torch.nn as nn

from fastapi.testclient import TestClient
from rasterio.io import MemoryFile


# =====================================================
# Dummy Model
# =====================================================

class DummyModel(nn.Module):
    """
    Simple model for testing.
    Always predicts class 1.
    """

    def forward(self, x):

        b, c, h, w = x.shape

        output = torch.zeros(
            (b, 2, h, w),
            dtype=torch.float32,
            device=x.device
        )

        output[:, 1] = 1

        return output


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def dummy_image():

    """
    6-channel image
    """

    return np.random.rand(
        6,
        256,
        256
    ).astype(np.float32)


@pytest.fixture
def dummy_prediction():

    """
    Binary prediction
    """

    return np.ones(
        (256, 256),
        dtype=np.uint8
    )


@pytest.fixture
def dummy_mask():

    return np.ones(
        (256, 256),
        dtype=np.uint8
    )


@pytest.fixture
def dummy_png():

    return (
        np.ones((256, 256), dtype=np.uint8)
        * 255
    )


# =====================================================
# TIFF Generator
# =====================================================

@pytest.fixture
def valid_tiff():

    """
    Generate a valid 6-band TIFF
    in memory.
    """

    data = np.random.randint(

        0,
        65535,

        size=(6, 256, 256),

        dtype=np.uint16

    )

    memfile = MemoryFile()

    with memfile.open(

        driver="GTiff",

        height=256,
        width=256,

        count=6,

        dtype=data.dtype

    ) as dst:

        dst.write(data)

    return memfile.read()


@pytest.fixture
def invalid_tiff():

    return b"This is not a TIFF file."


@pytest.fixture
def wrong_channel_tiff():

    data = np.random.randint(

        0,
        65535,

        size=(3, 256, 256),

        dtype=np.uint16

    )

    memfile = MemoryFile()

    with memfile.open(

        driver="GTiff",

        height=256,
        width=256,

        count=3,

        dtype=data.dtype

    ) as dst:

        dst.write(data)

    return memfile.read()


# =====================================================
# Common Monkeypatch
# =====================================================

@pytest.fixture
def app_client(monkeypatch):

    """
    Import main.py after patching
    expensive dependencies.
    """

    import main

    monkeypatch.setattr(
        main,
        "model",
        DummyModel()
    )

    monkeypatch.setattr(
        main,
        "device",
        torch.device("cpu")
    )

    monkeypatch.setattr(
        main,
        "crop_tiles",
        lambda img: (
            [img],
            [(0, img.shape[1], 0, img.shape[2])]
        )
    )

    monkeypatch.setattr(
        main,
        "run_inference",
        lambda tiles, model, device: [
            np.ones(
                (
                    tiles[0].shape[1],
                    tiles[0].shape[2]
                ),
                dtype=np.uint8
            )
        ]
    )

    monkeypatch.setattr(
        main,
        "stitch_tiles",
        lambda preds, coords, h, w:
        np.ones(
            (h, w),
            dtype=np.uint8
        )
    )

    client = TestClient(main.app)

    return client

# =====================================================
# /health
# =====================================================

def test_health(app_client):
    """
    Health endpoint should return status OK.
    """

    response = app_client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "status": "ok"
    }


def test_health_content_type(app_client):
    """
    Response should be JSON.
    """

    response = app_client.get("/health")

    assert response.headers["content-type"].startswith(
        "application/json"
    )


def test_health_multiple_requests(app_client):
    """
    Endpoint should remain stable.
    """

    for _ in range(5):

        response = app_client.get("/health")

        assert response.status_code == 200

        assert response.json()["status"] == "ok"


# =====================================================
# /predict
# Success Cases
# =====================================================

def test_predict_success(
        app_client,
        valid_tiff
):
    """
    Complete prediction pipeline.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "image.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 200

    result = response.json()

    assert "image" in result
    assert "total_area" in result
    assert "snow_area" in result
    assert "percentage" in result


def test_predict_area_values(
        app_client,
        valid_tiff
):
    """
    Area statistics should be valid.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    result = response.json()

    assert result["total_area"] == 256 * 256

    assert result["snow_area"] == 256 * 256

    assert result["percentage"] == 100.0


def test_predict_base64_image(
        app_client,
        valid_tiff
):
    """
    Returned image should be valid Base64.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    result = response.json()

    decoded = base64.b64decode(
        result["image"]
    )

    assert len(decoded) > 100


def test_predict_png_signature(
        app_client,
        valid_tiff
):
    """
    PNG header validation.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    img = base64.b64decode(
        response.json()["image"]
    )

    assert img.startswith(
        b"\x89PNG"
    )


def test_predict_percentage_range(
        app_client,
        valid_tiff
):
    """
    Percentage should stay
    within 0-100.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    pct = response.json()["percentage"]

    assert 0 <= pct <= 100


def test_predict_json_keys(
        app_client,
        valid_tiff
):
    """
    Verify returned JSON schema.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    result = response.json()

    expected = {

        "image",

        "total_area",

        "snow_area",

        "percentage"

    }

    assert set(result.keys()) == expected


def test_predict_multiple_calls(
        app_client,
        valid_tiff
):
    """
    Multiple requests should
    remain stable.
    """

    for _ in range(3):

        response = app_client.post(

            "/predict/",

            files={
                "file": (
                    "snow.tif",
                    valid_tiff,
                    "image/tiff"
                )
            }

        )

        assert response.status_code == 200


def test_predict_image_not_empty(
        app_client,
        valid_tiff
):
    """
    Image string should not
    be empty.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    image = response.json()["image"]

    assert isinstance(
        image,
        str
    )

    assert len(image) > 0


def test_predict_image_decodable(
        app_client,
        valid_tiff
):
    """
    Base64 image should decode
    without exception.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    base64.b64decode(
        response.json()["image"]
    )


def test_predict_content_type(
        app_client,
        valid_tiff
):
    """
    Response MIME type.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.headers[
        "content-type"
    ].startswith(
        "application/json"
    )



# =====================================================
# /predict
# Exception Tests
# =====================================================

import numpy as np
import pytest


def test_predict_wrong_extension(
        app_client
):
    """
    Upload non-TIFF file.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "image.jpg",
                b"dummy",
                "image/jpeg"
            )
        }

    )

    assert response.status_code == 400

    assert response.json()["detail"] == \
        "Only .tif / .tiff allowed"


def test_predict_invalid_tiff(
        app_client,
        invalid_tiff
):
    """
    Invalid TIFF content.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "image.tif",
                invalid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 400

    assert "Invalid TIFF" in response.json()["detail"]


def test_predict_wrong_channel(
        app_client,
        wrong_channel_tiff
):
    """
    Image must contain six bands.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "image.tif",
                wrong_channel_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 400

    assert response.json()["detail"] == \
        "Require 6-channel image"


def test_crop_tiles_exception(
        app_client,
        valid_tiff,
        monkeypatch
):
    """
    Force crop_tiles() failure.
    """

    import main

    def raise_error(img):
        raise RuntimeError("crop failed")

    monkeypatch.setattr(
        main,
        "crop_tiles",
        raise_error
    )

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 500


def test_run_inference_exception(
        app_client,
        valid_tiff,
        monkeypatch
):
    """
    Force inference failure.
    """

    import main

    def raise_error(
        tiles,
        model,
        device
    ):
        raise RuntimeError(
            "Inference failed"
        )

    monkeypatch.setattr(
        main,
        "run_inference",
        raise_error
    )

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 500


def test_stitch_tiles_exception(
        app_client,
        valid_tiff,
        monkeypatch
):
    """
    Force stitching failure.
    """

    import main

    def raise_error(
        preds,
        coords,
        h,
        w
    ):
        raise RuntimeError(
            "stitch failed"
        )

    monkeypatch.setattr(
        main,
        "stitch_tiles",
        raise_error
    )

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "snow.tif",
                valid_tiff,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 500


def test_empty_filename(
        app_client
):
    """
    Empty filename should fail validation.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "",
                b"",
                "image/tiff"
            )
        }

    )

    assert response.status_code >= 400


def test_corrupted_binary(
        app_client
):
    """
    Random binary pretending
    to be TIFF.
    """

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "fake.tif",
                b"\x01\x02\x03\x04",
                "image/tiff"
            )
        }

    )

    assert response.status_code == 400

    assert "Invalid TIFF" in response.json()["detail"]


def test_large_invalid_upload(
        app_client
):
    """
    Large invalid upload.
    """

    fake = np.random.bytes(
        1024 * 1024
    )

    response = app_client.post(

        "/predict/",

        files={
            "file": (
                "large.tif",
                fake,
                "image/tiff"
            )
        }

    )

    assert response.status_code == 400


def test_missing_upload(
        app_client
):
    """
    Missing upload field.
    """

    response = app_client.post(
        "/predict/"
    )

    assert response.status_code == 422


# =====================================================
# /compare
# Success Tests
# =====================================================

def test_compare_success(
        app_client,
        monkeypatch
):
    """
    Successful raster comparison.
    """

    import main

    monkeypatch.setattr(
        main,
        "resolve_raster_path",
        lambda month, raster_dir:
            f"/fake/{month}.tif"
    )

    monkeypatch.setattr(
        main,
        "compare_rasters",
        lambda **kwargs: {

            "left": {
                "month": "202504",
                "snow_area_km2": 10.5,
                "ratio": 35.2,
                "pixels": 100
            },

            "right": {
                "month": "202505",
                "snow_area_km2": 12.1,
                "ratio": 40.3,
                "pixels": 120
            },

            "gain": {
                "snow_area_km2": 2.0,
                "pixels": 20
            },

            "loss": {
                "snow_area_km2": 0.4,
                "pixels": 4
            },

            "net": {
                "snow_area_km2": 1.6,
                "pixels": 16
            },

            "roi": {
                "area_km2": 25.0,
                "pixels": 300
            },

            "coverage_delta_pct": 5.1,

            "pixel_area_km2": 0.0001,

            "diff_image_base64": "ZmFrZQ=="

        }
    )

    response = app_client.get(

        "/compare",

        params={
            "left": "202504",
            "right": "202505"
        }

    )

    assert response.status_code == 200

    data = response.json()

    assert data["left"]["month"] == "202504"

    assert data["right"]["month"] == "202505"


    def test_compare_response_keys(
        app_client,
        monkeypatch
):

    import main

    monkeypatch.setattr(
        main,
        "resolve_raster_path",
        lambda month, raster_dir:
            f"/fake/{month}.tif"
    )

    monkeypatch.setattr(
        main,
        "compare_rasters",
        lambda **kwargs: {

            "left": {},
            "right": {},
            "gain": {},
            "loss": {},
            "net": {},
            "roi": {},

            "coverage_delta_pct": 0,

            "pixel_area_km2": 0.001,

            "diff_image_base64": ""

        }
    )

    response = app_client.get(

        "/compare",

        params={
            "left": "202504",
            "right": "202505"
        }

    )

    result = response.json()

    expected = {

        "left",

        "right",

        "gain",

        "loss",

        "net",

        "roi",

        "coverage_delta_pct",

        "pixel_area_km2",

        "diff_image_base64"

    }

    assert expected.issubset(result.keys())


    def test_compare_base64_image(
        app_client,
        monkeypatch
):

    import main

    image = base64.b64encode(
        b"dummy image"
    ).decode()

    monkeypatch.setattr(
        main,
        "resolve_raster_path",
        lambda month, raster_dir:
            f"/fake/{month}.tif"
    )

    monkeypatch.setattr(
        main,
        "compare_rasters",
        lambda **kwargs: {

            "left": {},
            "right": {},
            "gain": {},
            "loss": {},
            "net": {},
            "roi": {},

            "coverage_delta_pct": 0,

            "pixel_area_km2": 0,

            "diff_image_base64": image

        }
    )

    response = app_client.get(

        "/compare",

        params={
            "left": "202504",
            "right": "202505"
        }

    )

    decoded = base64.b64decode(

        response.json()["diff_image_base64"]

    )

    assert decoded == b"dummy image"


    def test_compare_area_values(
        app_client,
        monkeypatch
):

    import main

    monkeypatch.setattr(
        main,
        "resolve_raster_path",
        lambda month, raster_dir:
            f"/fake/{month}.tif"
    )

    monkeypatch.setattr(
        main,
        "compare_rasters",
        lambda **kwargs: {

            "left": {
                "snow_area_km2": 10
            },

            "right": {
                "snow_area_km2": 15
            },

            "gain": {
                "snow_area_km2": 6
            },

            "loss": {
                "snow_area_km2": 1
            },

            "net": {
                "snow_area_km2": 5
            },

            "roi": {},

            "coverage_delta_pct": 20,

            "pixel_area_km2": 0.0001,

            "diff_image_base64": ""

        }
    )

    response = app_client.get(

        "/compare",

        params={
            "left": "202504",
            "right": "202505"
        }

    )

    result = response.json()

    assert result["left"]["snow_area_km2"] == 10

    assert result["right"]["snow_area_km2"] == 15

    assert result["net"]["snow_area_km2"] == 5


# =====================================================
# Cleanup / Shared Validation
# =====================================================

import gc
import torch
import pytest


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Automatically clean up resources after each test.
    """

    yield

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def test_application_exists(app_client):
    """
    Verify FastAPI application is available.
    """

    assert app_client is not None


def test_openapi_schema(app_client):
    """
    Verify OpenAPI schema is generated.
    """

    response = app_client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert "paths" in schema

    assert "/health" in schema["paths"]

    assert "/predict/" in schema["paths"]

    assert "/compare" in schema["paths"]


def test_docs_page(app_client):
    """
    Swagger UI should be available.
    """

    response = app_client.get("/docs")

    assert response.status_code == 200


def test_redoc_page(app_client):
    """
    ReDoc page should be available.
    """

    response = app_client.get("/redoc")

    assert response.status_code == 200


def test_json_response_type(app_client):
    """
    Verify JSON content type.
    """

    response = app_client.get("/health")

    assert response.headers[
        "content-type"
    ].startswith("application/json")


def test_unknown_endpoint(app_client):
    """
    Unknown endpoint should return 404.
    """

    response = app_client.get("/unknown")

    assert response.status_code == 404