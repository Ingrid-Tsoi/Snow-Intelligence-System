import numpy as np


def stitch_tiles(pred_tiles, coords, H, W, tile_size=256):
    output = np.zeros((H, W), dtype=np.float32)
    count = np.zeros((H, W), dtype=np.float32)

    weight = np.ones((tile_size, tile_size), dtype=np.float32)

    for pred, (y1, y2, x1, x2) in zip(pred_tiles, coords):
        h, w = y2 - y1, x2 - x1

        pred = pred[:h, :w]
        w_mask = weight[:h, :w]

        output[y1:y2, x1:x2] += pred * w_mask
        count[y1:y2, x1:x2] += w_mask

    output = output / count
    return (output > 0.5).astype(np.uint8)