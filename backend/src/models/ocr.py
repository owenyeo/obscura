    # Copyright 2025 Obscura
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Tuple, Optional
import numpy as np, cv2
from paddleocr import PaddleOCR

# Initialize once at import
# lang="en" covers English; switch to "ch" or "en_ppocr_mobile_v2.0" variants if needed
_OCR = PaddleOCR(use_textline_orientation=True, lang="en")

def _norm_bbox_from_poly(poly: np.ndarray, w: int, h: int) -> Tuple[float, float, float, float]:
    xs = poly[:, 0]; ys = poly[:, 1]
    x1, y1, x2, y2 = float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())
    x = max(0.0, x1 / w); y = max(0.0, y1 / h)
    bw = min(1.0, (x2 - x1) / w); bh = min(1.0, (y2 - y1) / h)
    return x, y, bw, bh

def _norm_bbox_from_box(box: np.ndarray, w: int, h: int) -> Tuple[float, float, float, float]:
    # Expecting [x1,y1,x2,y2]
    x1, y1, x2, y2 = [float(v) for v in box]
    x = max(0.0, x1 / w); y = max(0.0, y1 / h)
    bw = min(1.0, (x2 - x1) / w); bh = min(1.0, (y2 - y1) / h)
    return x, y, bw, bh

def ocr(img_bytes: bytes) -> List[Tuple[str, Tuple[float, float, float, float], float]]:
    """
    Returns: list of (text, (x,y,w,h) normalized 0..1, conf 0..1)
    Compatible with both:
      - NEW pipeline: [{'rec_texts': [...], 'rec_scores': [...], 'rec_polys': [...], 'rec_boxes': ...}, ...]
      - CLASSIC: [ [pts, (text, score)], ... ] in result[0]
    """
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return []
    h, w = img.shape[:2]

    result = _OCR.predict(img)
    out: List[Tuple[str, Tuple[float, float, float, float], float]] = []

    # Case A: NEW pipeline — list[dict]
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
        page = result[0]
        texts  = page.get("rec_texts", []) or []
        scores = page.get("rec_scores", []) or []
        polys  = page.get("rec_polys", None)  # list of (4,2) arrays
        boxes  = page.get("rec_boxes", None)  # (N,4) x1,y1,x2,y2

        n = len(texts)
        for i in range(n):
            text = str(texts[i]) if i < len(texts) else ""
            conf = float(scores[i]) if i < len(scores) else 0.0

            bbox: Optional[Tuple[float, float, float, float]] = None
            if polys is not None and i < len(polys):
                poly = np.array(polys[i], dtype=np.float32)  # (4,2)
                bbox = _norm_bbox_from_poly(poly, w, h)
            elif boxes is not None and i < len(boxes):
                box = np.array(boxes[i], dtype=np.float32)   # (4,)
                bbox = _norm_bbox_from_box(box, w, h)

            if bbox is None:
                continue

            out.append((text.strip(), bbox, conf))
        return out

    # Case B: CLASSIC — list[list] with points and (text, score)
    # result -> [lines] and lines is typically result[0]
    lines = (result[0] if isinstance(result, list) and len(result) > 0 else []) or []
    for line in lines:
        if isinstance(line, (list, tuple)) and len(line) >= 2:
            box_pts, text_part = line[0], line[1]
            if isinstance(text_part, (list, tuple)) and len(text_part) >= 2:
                text, conf = text_part[0], float(text_part[1])
            elif isinstance(text_part, dict):
                text = text_part.get("text", "")
                conf = float(text_part.get("score", 0.0))
            else:
                continue

            poly = np.array(box_pts, dtype=np.float32)  # (4,2)
            bbox = _norm_bbox_from_poly(poly, w, h)
            out.append((str(text).strip(), bbox, conf))

    return out