# src/models/inpaint.py
from typing import Optional, Union
import numpy as np
from PIL import Image
import torch
from diffusers import StableDiffusionInpaintPipeline

# --- load once ---
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_PIPE = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16 if _DEVICE == "cuda" else torch.float32,
    safety_checker=None,  # simple & fast
).to(_DEVICE)

from PIL import Image, ImageOps

def fit_to_canvas_keep_ar(img_pil: Image.Image, mask_pil: Image.Image,
                           max_side: int = 1024,  # choose highest your GPU handles (512/768/1024/1280/1536…)
                           mult: int = 64):       # keep multiples of 64 for SD
    W, H = img_pil.size
    # scale so the longest side = min(max_side, original longest side)
    target_long = min(max_side, max(W, H))
    scale = target_long / max(W, H)
    newW, newH = max(1, int(round(W * scale))), max(1, int(round(H * scale)))

    # snap up to multiple of `mult` (avoid internal rounding)
    newW = (newW + mult - 1) // mult * mult
    newH = (newH + mult - 1) // mult * mult

    # resize image/mask with correct filters
    img_rs  = img_pil.resize((newW, newH), Image.LANCZOS)
    mask_rs = mask_pil.resize((newW, newH), Image.NEAREST)

    # pad to a square canvas = max(newW, newH), also multiple of `mult`
    side = max(newW, newH)
    side = (side + mult - 1) // mult * mult
    padW, padH = side - newW, side - newH
    pl, pr = padW // 2, padW - padW // 2
    pt, pb = padH // 2, padH - padH // 2

    fill_rgb = tuple(img_pil.getpixel((0, 0))) if img_pil.mode == "RGB" else (0, 0, 0)
    img_sq  = ImageOps.expand(img_rs,  border=(pl, pt, pr, pb), fill=fill_rgb)
    mask_sq = ImageOps.expand(mask_rs, border=(pl, pt, pr, pb), fill=0)

    meta = dict(orig_size=(W, H), resized=(newW, newH), pads=(pl, pt, pr, pb))
    return img_sq, mask_sq, meta

def unpad_and_restore(inpainted_sq: Image.Image, meta) -> Image.Image:
    (W, H) = meta["orig_size"]
    (pl, pt, pr, pb) = meta["pads"]
    # remove square padding
    cropped = inpainted_sq.crop((pl, pt, inpainted_sq.width - pr, inpainted_sq.height - pb))
    # now cropped is (newW,newH); resize back to original size to preserve final resolution
    return cropped.resize((W, H), Image.LANCZOS)

def _to_pil_rgb(x: Union[np.ndarray, Image.Image]) -> Image.Image:
    if isinstance(x, Image.Image):
        return x.convert("RGB")
    # assume HxW or HxWxC numpy
    arr = x
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    if arr.shape[-1] == 4:
        return Image.fromarray(arr).convert("RGB")
    return Image.fromarray(arr).convert("RGB")

def _to_pil_mask(mask: Union[np.ndarray, Image.Image], size_wh: tuple[int,int]) -> Image.Image:
    """
    White(255) = inpaint here, Black(0) = keep.
    Resized to match `size_wh` (W,H).
    """
    if isinstance(mask, Image.Image):
        m = mask.convert("L")
    else:
        m = mask
        if m.dtype == bool:
            m = (m.astype(np.uint8) * 255)
        elif m.dtype != np.uint8:
            # accept 0..1 floats or 0..255 ints
            m = (np.clip(m, 0, 1) * 255).astype(np.uint8) if m.max() <= 1.0 else m.astype(np.uint8)
        m = Image.fromarray(m).convert("L")
    if m.size != size_wh:
        m = m.resize(size_wh, Image.NEAREST)
    return m

def inpaint_image(
    image: Union[np.ndarray, Image.Image],
    mask: Union[np.ndarray, Image.Image],
    prompt: str = "seamless background continuation, realistic, no text",
    negative_prompt: str = "text, letters, numbers, logo, signage, watermark, faces",
    steps: int = 35,
    guidance: float = 6.5,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Minimal SD inpaint:
      - image: RGB (np.ndarray HxWx3 uint8 or PIL)
      - mask : bool/0..1/0..255 (True/white = replace)
    Returns PIL RGB.
    """
    pil_img = _to_pil_rgb(image)
    pil_mask = _to_pil_mask(mask, pil_img.size)  # size = (W,H)

    gen = None
    if seed is not None:
        gen = torch.Generator(device=_DEVICE).manual_seed(seed)

    with torch.no_grad():
        out = _PIPE(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=pil_img,
            mask_image=pil_mask,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=gen,
        )
    return out.images[0].convert("RGB")
