import numpy as np
import pytest
import rasterio
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
from rasterio.transform import from_origin

from utils.analysis import (
    month_to_filename,
    resolve_raster_path,
    resolve_polygon_path,
    raster_to_mask,
    compute_pixel_area_km2,
    _crop_to_mask,
    _align_to_reference,
    _polygon_mask,
)



# =====================================================
# month_to_filename()
# =====================================================

def test_month_to_filename_valid():
    filename = month_to_filename("202504")
    assert filename == "porters_202504_NDSI.tif"


def test_month_to_filename_custom_site():
    filename = month_to_filename(
        "202504",
        site="alps"
    )

    assert filename == "alps_202504_NDSI.tif"


@pytest.mark.parametrize(
    "month",
    [
        "",
        "2025",
        "2025040",
        "abcdef",
        "20A504",
        "2025-04",
        "2025/04",
    ]
)
def test_month_to_filename_invalid(month):

    with pytest.raises(ValueError):
        month_to_filename(month)


def test_month_to_filename_strip_space():

    filename = month_to_filename(" 202504 ")

    assert filename == "porters_202504_NDSI.tif"


# =====================================================
# resolve_raster_path()
# =====================================================

def test_resolve_raster_path_success(tmp_path):

    raster = tmp_path / "porters_202504_NDSI.tif"

    raster.touch()

    result = resolve_raster_path(
        "202504",
        tmp_path
    )

    assert result == raster


def test_resolve_raster_path_custom_site(tmp_path):

    raster = tmp_path / "alps_202504_NDSI.tif"

    raster.touch()

    result = resolve_raster_path(
        "202504",
        tmp_path,
        site="alps"
    )

    assert result == raster


def test_resolve_raster_path_missing(tmp_path):

    with pytest.raises(FileNotFoundError):

        resolve_raster_path(
            "202504",
            tmp_path
        )


# =====================================================
# resolve_polygon_path()
# =====================================================

def test_resolve_polygon_path_local(tmp_path):

    data = tmp_path / "data"
    polygons = data / "polygons"

    polygons.mkdir(parents=True)

    geojson = polygons / "porters.geojson"

    geojson.touch()

    result = resolve_polygon_path(tmp_path)

    assert result == geojson


def test_resolve_polygon_path_missing(tmp_path):

    with pytest.raises(FileNotFoundError):

        resolve_polygon_path(tmp_path)


# =====================================================
# raster_to_mask()
# =====================================================

def test_raster_to_mask_positive():

    arr = np.array([

        [0, 1, 2],
        [5, 8, 0]

    ])

    mask = raster_to_mask(arr)

    expected = np.array([

        [0, 1, 1],
        [1, 1, 0]

    ])

    assert np.array_equal(mask, expected)


def test_raster_to_mask_zero():

    arr = np.zeros((5, 5))

    mask = raster_to_mask(arr)

    assert np.all(mask == 0)


def test_raster_to_mask_nan():

    arr = np.array([

        [np.nan, 2],
        [5, np.nan]

    ])

    mask = raster_to_mask(arr)

    expected = np.array([

        [0, 1],
        [1, 0]

    ])

    assert np.array_equal(mask, expected)


def test_raster_to_mask_negative():

    arr = np.array([

        [-5, -1],
        [0, 8]

    ])

    mask = raster_to_mask(arr)

    expected = np.array([

        [0, 0],
        [0, 1]

    ])

    assert np.array_equal(mask, expected)


def test_raster_to_mask_inf():

    arr = np.array([

        [np.inf, -np.inf],
        [1, 0]

    ])

    mask = raster_to_mask(arr)

    expected = np.array([

        [0, 0],
        [1, 0]

    ])

    assert np.array_equal(mask, expected)


def test_raster_to_mask_dtype():

    arr = np.random.rand(20, 20)

    mask = raster_to_mask(arr)

    assert mask.dtype == np.uint8


# =====================================================
# compute_pixel_area_km2()
# =====================================================

def test_compute_pixel_area():

    transform = from_origin(
        west=0,
        north=0,
        xsize=30,
        ysize=30
    )

    area = compute_pixel_area_km2(transform)

    expected = (30 * 30) / 1_000_000

    assert area == pytest.approx(expected)


def test_compute_pixel_area_negative_transform():

    transform = rasterio.Affine(

        -30,
        0,
        0,

        0,
        -30,
        0

    )

    area = compute_pixel_area_km2(transform)

    expected = (30 * 30) / 1_000_000

    assert area == pytest.approx(expected)


def test_compute_pixel_area_decimal():

    transform = rasterio.Affine(

        12.5,
        0,
        0,

        0,
        -12.5,
        0

    )

    area = compute_pixel_area_km2(transform)

    expected = (12.5 * 12.5) / 1_000_000

    assert area == pytest.approx(expected)


def test_compute_pixel_area_one_meter():

    transform = rasterio.Affine(

        1,
        0,
        0,

        0,
        -1,
        0

    )

    area = compute_pixel_area_km2(transform)

    assert area == pytest.approx(1e-6)


def test_compute_pixel_area_large_pixel():

    transform = rasterio.Affine(

        100,
        0,
        0,

        0,
        -100,
        0

    )

    area = compute_pixel_area_km2(transform)

    assert area == pytest.approx(0.01)


# =====================================================
# Fake Raster Dataset
# =====================================================

class DummyRaster:

    def __init__(
        self,
        width=100,
        height=100,
        transform=None,
        crs="EPSG:4326",
        nodata=0,
    ):

        self.width = width
        self.height = height

        self.transform = (
            transform
            if transform is not None
            else from_origin(0, 100, 1, 1)
        )

        self.crs = crs

        self.nodata = nodata


# =====================================================
# _crop_to_mask()
# =====================================================

def test_crop_to_mask_normal():

    arr = np.ones((100, 100))

    mask = np.zeros((100, 100), dtype=bool)

    mask[20:60, 30:70] = True

    cropped_arr, cropped_mask = _crop_to_mask(
        arr,
        mask,
        pad=0
    )

    assert cropped_arr.shape == (40, 40)

    assert cropped_mask.shape == (40, 40)

    assert np.all(cropped_mask)


def test_crop_to_mask_with_padding():

    arr = np.ones((100, 100))

    mask = np.zeros((100, 100), dtype=bool)

    mask[20:60, 30:70] = True

    cropped_arr, cropped_mask = _crop_to_mask(
        arr,
        mask,
        pad=10
    )

    assert cropped_arr.shape == (60, 60)

    assert cropped_mask.shape == (60, 60)


def test_crop_to_mask_touch_boundary():

    arr = np.ones((50, 50))

    mask = np.zeros((50, 50), dtype=bool)

    mask[0:20, 0:20] = True

    cropped_arr, cropped_mask = _crop_to_mask(
        arr,
        mask,
        pad=20
    )

    assert cropped_arr.shape[0] <= 50

    assert cropped_arr.shape[1] <= 50


def test_crop_to_mask_empty_mask():

    arr = np.ones((50, 50))

    mask = np.zeros((50, 50), dtype=bool)

    cropped_arr, cropped_mask = _crop_to_mask(
        arr,
        mask
    )

    assert np.array_equal(arr, cropped_arr)

    assert np.array_equal(mask, cropped_mask)


def test_crop_to_mask_single_pixel():

    arr = np.ones((100, 100))

    mask = np.zeros((100, 100), dtype=bool)

    mask[55, 80] = True

    cropped_arr, cropped_mask = _crop_to_mask(
        arr,
        mask,
        pad=0
    )

    assert cropped_arr.shape == (1, 1)

    assert cropped_mask.shape == (1, 1)

    assert cropped_mask[0, 0]


# =====================================================
# _align_to_reference()
# =====================================================

def test_align_same_size():

    src = DummyRaster()

    ref = DummyRaster()

    arr = np.ones((100, 100), dtype=np.float32)

    aligned = _align_to_reference(
        arr,
        src,
        ref
    )

    assert aligned.shape == (100, 100)


def test_align_different_size():

    src = DummyRaster(
        width=50,
        height=50
    )

    ref = DummyRaster(
        width=120,
        height=80
    )

    arr = np.ones((50, 50), dtype=np.float32)

    aligned = _align_to_reference(
        arr,
        src,
        ref
    )

    assert aligned.shape == (80, 120)


def test_align_output_dtype():

    src = DummyRaster()

    ref = DummyRaster()

    arr = np.random.rand(
        100,
        100
    ).astype(np.float32)

    aligned = _align_to_reference(
        arr,
        src,
        ref
    )

    assert aligned.dtype == np.float32


def test_align_zero_input():

    src = DummyRaster()

    ref = DummyRaster()

    arr = np.zeros(
        (100, 100),
        dtype=np.float32
    )

    aligned = _align_to_reference(
        arr,
        src,
        ref
    )

    assert np.all(aligned == 0)


# =====================================================
# _polygon_mask()
# =====================================================

def test_polygon_mask(monkeypatch):

    polygon = Polygon([
        (10, 10),
        (30, 10),
        (30, 30),
        (10, 30)
    ])

    gdf = gpd.GeoDataFrame(
        geometry=[polygon],
        crs="EPSG:4326"
    )

    monkeypatch.setattr(
        "utils.analysis._load_polygon_geometries",
        lambda path, crs: [
            polygon.__geo_interface__
        ]
    )

    raster = DummyRaster()

    mask = _polygon_mask(
        raster,
        "dummy.geojson"
    )

    assert mask.shape == (
        raster.height,
        raster.width
    )

    assert mask.dtype == bool

    assert mask.any()


def test_polygon_mask_empty(monkeypatch):

    monkeypatch.setattr(
        "utils.analysis._load_polygon_geometries",
        lambda path, crs: []
    )

    raster = DummyRaster()

    with pytest.raises(Exception):

        _polygon_mask(
            raster,
            "dummy.geojson"
        )


def test_polygon_mask_full(monkeypatch):

    polygon = Polygon([
        (-100, -100),
        (200, -100),
        (200, 200),
        (-100, 200)
    ])

    monkeypatch.setattr(
        "utils.analysis._load_polygon_geometries",
        lambda path, crs: [
            polygon.__geo_interface__
        ]
    )

    raster = DummyRaster()

    mask = _polygon_mask(
        raster,
        "dummy.geojson"
    )

    assert np.all(mask)


def test_polygon_mask_small_polygon(monkeypatch):

    polygon = Polygon([
        (49, 49),
        (50, 49),
        (50, 50),
        (49, 50)
    ])

    monkeypatch.setattr(
        "utils.analysis._load_polygon_geometries",
        lambda path, crs: [
            polygon.__geo_interface__
        ]
    )

    raster = DummyRaster()

    mask = _polygon_mask(
        raster,
        "dummy.geojson"
    )

    assert mask.any()

    assert mask.sum() >= 1