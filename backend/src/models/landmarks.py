# src/models/landmarks.py

from ultralytics import YOLO
import numpy as np
from io import BytesIO
from PIL import Image

CLASSES = [
    "person", "rider", "car", "truck", "bus", "train",
    "motorcycle", "bicycle", "traffic light", "traffic sign", "building"
]

# load once at import time
_model = YOLO("src/models/weights/yolov8n_landmarks.pt")

def landmarks(img_bytes: bytes, conf_th: float = 0.25):
    """
    Run YOLO landmarks detection.
    Returns list of (class_name, x, y, w, h, conf) with normalized coords.
    """
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    results = _model.predict(img, conf=conf_th, verbose=False)

    findings = []
    for r in results:
        h, w = r.orig_shape
        for box in r.boxes:
            cls_id = int(box.cls.item())
            class_name = CLASSES[cls_id] if cls_id < len(CLASSES) else str(cls_id)
            conf = float(box.conf.item())

            # convert to normalized xywh
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = (x1 + x2) / 2 / w
            cy = (y1 + y2) / 2 / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h

            findings.append((class_name, cx, cy, bw, bh, conf))
    return findings
