import numpy as np
import pytest


@pytest.fixture
def sample_image():
    """
    Standard 6-channel image (512x512)
    """
    return np.random.rand(6, 512, 512).astype(np.float32)


@pytest.fixture
def small_image():
    """
    Image smaller than tile size.
    """
    return np.random.rand(6, 100, 120).astype(np.float32)


@pytest.fixture
def rectangular_image():
    """
    Non-square image.
    """
    return np.random.rand(6, 300, 500).astype(np.float32)


@pytest.fixture
def empty_prediction():
    return []


@pytest.fixture
def single_prediction():
    return [
        np.ones((256, 256), dtype=np.float32)
    ]


@pytest.fixture
def single_coord():
    return [
        (0, 256, 0, 256)
    ]


@pytest.fixture
def overlap_predictions():
    return [
        np.ones((256, 256), dtype=np.float32),
        np.zeros((256, 256), dtype=np.float32)
    ]


@pytest.fixture
def overlap_coords():
    return [
        (0, 256, 0, 256),
        (0, 256, 224, 480)
    ]