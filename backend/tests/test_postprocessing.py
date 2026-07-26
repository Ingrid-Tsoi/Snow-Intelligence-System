import numpy as np

from utils.postprocessing import stitch_tiles


def test_single_tile(single_prediction, single_coord):
    """
    Single tile reconstruction.
    """

    mask = stitch_tiles(
        single_prediction,
        single_coord,
        256,
        256
    )

    assert mask.shape == (256, 256)
    assert mask.dtype == np.uint8

    assert np.all(mask == 1)


def test_overlap_tiles(overlap_predictions, overlap_coords):
    """
    Overlap stitching should succeed.
    """

    mask = stitch_tiles(
        overlap_predictions,
        overlap_coords,
        256,
        480
    )

    assert mask.shape == (256, 480)

    assert mask.dtype == np.uint8


def test_output_binary(single_prediction, single_coord):
    """
    Final output should only contain 0 or 1.
    """

    mask = stitch_tiles(
        single_prediction,
        single_coord,
        256,
        256
    )

    unique = np.unique(mask)

    assert set(unique).issubset({0, 1})


def test_threshold():
    """
    Threshold >0.5 should become 1.
    """

    pred = [
        np.full((256, 256), 0.8, dtype=np.float32)
    ]

    coord = [
        (0, 256, 0, 256)
    ]

    mask = stitch_tiles(
        pred,
        coord,
        256,
        256
    )

    assert np.all(mask == 1)


def test_threshold_zero():
    """
    Values below threshold become 0.
    """

    pred = [
        np.full((256, 256), 0.2, dtype=np.float32)
    ]

    coord = [
        (0, 256, 0, 256)
    ]

    mask = stitch_tiles(
        pred,
        coord,
        256,
        256
    )

    assert np.all(mask == 0)


def test_multiple_tiles():
    """
    Four tiles should reconstruct correctly.
    """

    preds = [
        np.ones((256, 256), dtype=np.float32),
        np.ones((256, 256), dtype=np.float32),
        np.ones((256, 256), dtype=np.float32),
        np.ones((256, 256), dtype=np.float32),
    ]

    coords = [
        (0, 256, 0, 256),
        (0, 256, 256, 512),
        (256, 512, 0, 256),
        (256, 512, 256, 512),
    ]

    mask = stitch_tiles(
        preds,
        coords,
        512,
        512
    )

    assert mask.shape == (512, 512)

    assert np.all(mask == 1)


def test_edge_tile():
    """
    Partial edge tile should be handled correctly.
    """

    pred = [
        np.ones((256, 256), dtype=np.float32)
    ]

    coord = [
        (200, 300, 200, 300)
    ]

    mask = stitch_tiles(
        pred,
        coord,
        300,
        300
    )

    assert mask.shape == (300, 300)

    assert np.all(mask[200:300, 200:300] == 1)