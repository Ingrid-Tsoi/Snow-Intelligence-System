import numpy as np

from utils.preprocessing import crop_tiles


def test_crop_tiles_normal_image(sample_image):
    """
    512x512 image should generate multiple tiles.
    """

    tiles, coords = crop_tiles(sample_image)

    assert len(tiles) > 1
    assert len(tiles) == len(coords)

    for tile in tiles:
        assert tile.shape == (6, 256, 256)
        assert tile.dtype == np.float32


def test_crop_tiles_small_image(small_image):
    """
    Small image should still produce one padded tile.
    """

    tiles, coords = crop_tiles(small_image)

    assert len(tiles) == 1

    tile = tiles[0]

    assert tile.shape == (6, 256, 256)

    assert coords[0] == (0, 100, 0, 120)


def test_crop_tiles_rectangular_image(rectangular_image):
    """
    Non-square image should generate valid coordinates.
    """

    tiles, coords = crop_tiles(rectangular_image)

    assert len(tiles) == len(coords)

    H = 300
    W = 500

    for y1, y2, x1, x2 in coords:

        assert 0 <= y1 < H
        assert y2 <= H

        assert 0 <= x1 < W
        assert x2 <= W


def test_crop_tiles_output_dtype(sample_image):
    """
    Every tile should be float32.
    """

    tiles, _ = crop_tiles(sample_image)

    for tile in tiles:
        assert tile.dtype == np.float32


def test_crop_tiles_padding(small_image):
    """
    Padding area should contain zeros.
    """

    tiles, _ = crop_tiles(small_image)

    tile = tiles[0]

    assert np.all(tile[:, 100:, :] == 0)
    assert np.all(tile[:, :, 120:] == 0)


def test_crop_tiles_coordinate_number(sample_image):
    """
    Tile number should equal coordinate number.
    """

    tiles, coords = crop_tiles(sample_image)

    assert len(tiles) == len(coords)


def test_crop_tiles_overlap():
    """
    Overlap parameter should increase tile count.
    """

    img = np.random.rand(6, 512, 512).astype(np.float32)

    tiles_no_overlap, _ = crop_tiles(
        img,
        tile_size=256,
        overlap=0
    )

    tiles_overlap, _ = crop_tiles(
        img,
        tile_size=256,
        overlap=32
    )

    assert len(tiles_overlap) > len(tiles_no_overlap)