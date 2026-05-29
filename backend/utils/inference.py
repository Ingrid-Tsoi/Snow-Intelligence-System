import torch
import numpy as np

def run_inference(tiles, model, device, batch_size=8):
    """
    tiles: list of [C, H, W]
    return: list of [H, W]
    """

    model.to(device)
    model.eval()

    preds = []

    with torch.no_grad():
        for i in range(0, len(tiles), batch_size):
            batch_tiles = tiles[i:i+batch_size]

            # numpy → tensor
            batch = torch.from_numpy(np.stack(batch_tiles)).float().to(device)

            # inference
            pred = model(batch)              # [B, 2, H, W]
            pred = torch.argmax(pred, dim=1) # [B, H, W]

            preds.extend(pred.cpu().numpy())

    return preds