import os, io
import numpy as np
from PIL import Image
import torch
from segment_anything import SamPredictor, sam_model_registry
import cv2

SAM_VARIANT = "vit_h"  # you said vit_h only
SAM_CKPT = os.getenv("SAM_CKPT", "src/models/weights/sam_vit_h.pth")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- init once ---
assert os.path.exists(SAM_CKPT), f"Missing SAM checkpoint: {SAM_CKPT}"
sam = sam_model_registry[SAM_VARIANT](checkpoint=SAM_CKPT)
sam.to(device=DEVICE)
sam.eval()
_predictor = SamPredictor(sam)

def _to_numpy_rgb(image_like) -> np.ndarray:
    if isinstance(image_like, np.ndarray):
        arr = image_like
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        elif arr.ndim == 3 and arr.shape[-1] == 4:
            arr = np.array(Image.fromarray(arr).convert("RGB"))
        elif arr.ndim == 3 and arr.shape[-1] == 3:
            pass
        else:
            raise ValueError(f"Unsupported ndarray shape: {arr.shape}")
        return arr.astype(np.uint8)
    if isinstance(image_like, (bytes, bytearray)):
        return np.array(Image.open(io.BytesIO(image_like)).convert("RGB"))
    if isinstance(image_like, str):
        if not os.path.exists(image_like):
            raise FileNotFoundError(image_like)
        return np.array(Image.open(image_like).convert("RGB"))
    raise TypeError(f"Unsupported image_like type: {type(image_like)}")

def segment_within_bbox(image_like, bbox_xyxy) -> np.ndarray:
    """
    image_like: ndarray (H,W,3) uint8, or bytes, or filepath
    bbox_xyxy : (x1,y1,x2,y2) in **pixels**
    returns: (H,W) bool mask
    """
    img = _to_numpy_rgb(image_like)
    H, W = img.shape[:2]

    x1, y1, x2, y2 = bbox_xyxy
    x1 = max(0, min(W - 1, int(round(x1))))
    y1 = max(0, min(H - 1, int(round(y1))))
    x2 = max(0, min(W,     int(round(x2))))
    y2 = max(0, min(H,     int(round(y2))))
    if x2 <= x1 or y2 <= y1:
        return np.zeros((H, W), dtype=bool)

    box = np.array([x1, y1, x2, y2], dtype=np.float32)

    # Set image once per call; for multiple boxes on same image, see tip below
    _predictor.set_image(img)
    with torch.no_grad():
        masks, scores, _ = _predictor.predict(
            box=box,
            multimask_output=False,
        )
    return masks[0].astype(bool)

def visualize_mask(image: np.ndarray, mask: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    image: HxWx3 uint8 RGB
    mask : HxW bool or 0/1 array
    alpha: transparency of overlay
    """
    overlay = image.copy()
    overlay[mask] = (255, 0, 0)  # red for mask area
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
