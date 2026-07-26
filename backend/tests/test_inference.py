import numpy as np
import pytest
import torch
import torch.nn as nn

from utils.inference import run_inference


# -----------------------------------------------------
# Dummy model for unit testing
# -----------------------------------------------------

class DummyModel(nn.Module):
    """
    Produce deterministic predictions.

    Channel 0 = all zeros
    Channel 1 = all ones

    Therefore argmax() should always return class 1.
    """

    def forward(self, x):

        b, c, h, w = x.shape

        output = torch.zeros(
            (b, 2, h, w),
            dtype=torch.float32,
            device=x.device
        )

        output[:, 1, :, :] = 1.0

        return output


# -----------------------------------------------------
# Fixtures
# -----------------------------------------------------

@pytest.fixture
def cpu_device():
    return torch.device("cpu")


@pytest.fixture
def dummy_model():
    return DummyModel()


@pytest.fixture
def one_tile():

    return [
        np.random.rand(6, 256, 256).astype(np.float32)
    ]


@pytest.fixture
def four_tiles():

    return [
        np.random.rand(6, 256, 256).astype(np.float32)
        for _ in range(4)
    ]


@pytest.fixture
def ten_tiles():

    return [
        np.random.rand(6, 256, 256).astype(np.float32)
        for _ in range(10)
    ]


# -----------------------------------------------------
# Tests
# -----------------------------------------------------

def test_single_tile(
        one_tile,
        dummy_model,
        cpu_device
):
    """
    One input tile should return one prediction.
    """

    result = run_inference(
        one_tile,
        dummy_model,
        cpu_device
    )

    assert len(result) == 1

    assert result[0].shape == (256, 256)

    assert result[0].dtype == np.int64

    assert np.all(result[0] == 1)


def test_multiple_tiles(
        four_tiles,
        dummy_model,
        cpu_device
):
    """
    Multiple tiles should produce equal number of outputs.
    """

    result = run_inference(
        four_tiles,
        dummy_model,
        cpu_device
    )

    assert len(result) == 4

    for pred in result:

        assert pred.shape == (256, 256)

        assert np.all(pred == 1)


def test_large_batch(
        ten_tiles,
        dummy_model,
        cpu_device
):
    """
    Batch processing should work when
    total tiles > batch size.
    """

    result = run_inference(
        ten_tiles,
        dummy_model,
        cpu_device,
        batch_size=4
    )

    assert len(result) == 10


def test_batch_size_larger_than_dataset(
        four_tiles,
        dummy_model,
        cpu_device
):
    """
    Batch size larger than tile count.
    """

    result = run_inference(
        four_tiles,
        dummy_model,
        cpu_device,
        batch_size=64
    )

    assert len(result) == 4


def test_batch_size_one(
        four_tiles,
        dummy_model,
        cpu_device
):
    """
    Every tile processed individually.
    """

    result = run_inference(
        four_tiles,
        dummy_model,
        cpu_device,
        batch_size=1
    )

    assert len(result) == 4


def test_empty_tile_list(
        dummy_model,
        cpu_device
):
    """
    Empty input should return empty output.
    """

    result = run_inference(
        [],
        dummy_model,
        cpu_device
    )

    assert result == []


def test_prediction_binary(
        one_tile,
        dummy_model,
        cpu_device
):
    """
    Prediction should contain only class labels.
    """

    result = run_inference(
        one_tile,
        dummy_model,
        cpu_device
    )

    unique = np.unique(result[0])

    assert set(unique).issubset({0, 1})


def test_prediction_shape(
        four_tiles,
        dummy_model,
        cpu_device
):
    """
    Output size should equal tile size.
    """

    result = run_inference(
        four_tiles,
        dummy_model,
        cpu_device
    )

    for pred in result:

        assert pred.shape == (256, 256)


def test_model_called_on_cpu(
        one_tile,
        cpu_device
):
    """
    Verify model can be moved onto CPU.
    """

    model = DummyModel()

    result = run_inference(
        one_tile,
        model,
        cpu_device
    )

    assert len(result) == 1


def test_random_tile_values(
        dummy_model,
        cpu_device
):
    """
    Random input values should not
    affect prediction shape.
    """

    tiles = [

        np.random.uniform(
            -100,
            100,
            (6, 256, 256)
        ).astype(np.float32)

        for _ in range(3)

    ]

    result = run_inference(
        tiles,
        dummy_model,
        cpu_device
    )

    assert len(result) == 3

    for pred in result:

        assert pred.shape == (256, 256)


def test_numpy_float64_input(
        dummy_model,
        cpu_device
):
    """
    float64 numpy arrays should be accepted
    because run_inference converts to float().
    """

    tiles = [

        np.random.rand(
            6,
            256,
            256
        )

        for _ in range(2)

    ]

    result = run_inference(
        tiles,
        dummy_model,
        cpu_device
    )

    assert len(result) == 2


def test_prediction_dtype(
        one_tile,
        dummy_model,
        cpu_device
):
    """
    Output dtype should be integer labels.
    """

    result = run_inference(
        one_tile,
        dummy_model,
        cpu_device
    )

    assert np.issubdtype(
        result[0].dtype,
        np.integer
    )


def test_every_prediction_is_class_one(
        ten_tiles,
        dummy_model,
        cpu_device
):
    """
    DummyModel always predicts class 1.
    """

    result = run_inference(
        ten_tiles,
        dummy_model,
        cpu_device
    )

    for pred in result:

        assert np.all(pred == 1)


def test_batch_loop_execution(
        ten_tiles,
        dummy_model,
        cpu_device
):
    """
    Force multiple iterations of the
    batching loop.
    """

    result = run_inference(
        ten_tiles,
        dummy_model,
        cpu_device,
        batch_size=3
    )

    assert len(result) == 10