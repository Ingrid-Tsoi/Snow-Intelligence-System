import numpy as np

def crop_tiles(img, tile_size=256, overlap=32):
    C, H, W = img.shape
    stride = tile_size - overlap

    tiles = []
    coords = []

    for y in range(0, H, stride):
        for x in range(0, W, stride):
            y1, x1 = y, x
            y2, x2 = min(y1 + tile_size, H), min(x1 + tile_size, W)

            tile = img[:, y1:y2, x1:x2]

            pad_h = tile_size - tile.shape[1]
            pad_w = tile_size - tile.shape[2]

            tile = np.pad(tile, ((0,0),(0,pad_h),(0,pad_w)), mode='constant')
            tile = tile.astype(np.float32)  # ← 加這行

            tiles.append(tile)
            coords.append((y1, y2, x1, x2))

    return tiles, coords