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

import io
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
from supervision import Detections
from PIL import Image, ImageFile
from typing import List, Tuple

# download model
model_path = "src/models/weights/yolov8n_100e.pt"
ImageFile.LOAD_TRUNCATED_IMAGES = True

# load model
model = YOLO(model_path)

image_path = "tests/assets/face.png"

output = model(Image.open(image_path))
print(output[0].boxes)
results = Detections.from_ultralytics(output[0])
def _pil_from_bytes(img_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")

def faces(img_bytes: bytes, conf_th: float = 0.5) -> List[Tuple[float, float, float, float, float]]:
    """
    Returns a list of detections: [(x, y, w, h, conf)], with (x,y,w,h) normalized to [0..1].
    """
    pil_img = _pil_from_bytes(img_bytes)
    W, H = pil_img.size

    # Run inference (ultralytics handles resizing/letterbox internally)
    # We pass conf= to filter low scores in the model output already.
    results = model.predict(source=pil_img, conf=conf_th, verbose=False)

    out: List[Tuple[float, float, float, float, float]] = []
    if not results or results[0] is None or results[0].boxes is None:
        return out

    boxes_xyxy = results[0].boxes.xyxy  # tensor [N,4] in original image coords
    scores     = results[0].boxes.conf  # tensor [N]

    # Convert tensors to CPU numpy
    if hasattr(boxes_xyxy, "cpu"):
        boxes_xyxy = boxes_xyxy.cpu().numpy()
    if hasattr(scores, "cpu"):
        scores = scores.cpu().numpy()

    for (x1, y1, x2, y2), s in zip(boxes_xyxy, scores):
        # clip to image
        x1 = float(max(0.0, min(x1, W)))
        y1 = float(max(0.0, min(y1, H)))
        x2 = float(max(0.0, min(x2, W)))
        y2 = float(max(0.0, min(y2, H)))

        # normalize
        x = x1 / W
        y = y1 / H
        w = max(0.0, (x2 - x1) / W)
        h = max(0.0, (y2 - y1) / H)
        conf = float(s)

        # filter any degenerate boxes that survived
        if w <= 0 or h <= 0:
            continue

        out.append((x, y, w, h, conf))

    return out