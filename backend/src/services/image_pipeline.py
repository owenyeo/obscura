from typing import List, Dict
import io
import os
from PIL import Image  # for W,H (and optionally to pass pixel data to SAM)
import numpy as np
import cv2 
from src.schemas.common import ImageFinding
from src.schemas.analyze_image import AnalyzeImageResponse
from src.models.ocr import ocr
from src.models.faces import faces
from src.models.landmarks import landmarks
from src.models.pii_from_text import classify_ocr_text, mask_text_for_privacy
from src.services.risk_scoring import score
from src.services.utils_warnings import warning_for_kind
from src.models.masking import segment_within_bbox, visualize_mask  # SAM segmentation logic
# from src.models.inpaint import inpaint_image, fit_to_canvas_keep_ar, unpad_and_restore
from src.models.lama import inpaint

MODEL_VER = {"ocr": "paddleocr-2.7", "pii_rules": "pii-regex-1.0", "face": "YOLOv8"}

async def analyze_image(img_bytes: bytes, modes: str | None, policy: str | None, filename: str | None = None) -> AnalyzeImageResponse:
    findings: List[ImageFinding] = []
    warnings: List[str] = []
    kind_counts: Dict[str, int] = {}

    # Decode image once to get shape (and reuse if SAM needs pixels)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    W, H = pil_img.size
    np_img = np.array(pil_img)  # if segment_within_bbox needs a pixel array

    # 1) OCR to extract text blocks + coords
    ocr_lines = ocr(img_bytes)  # expecting [(raw_text, (x,y,w,h), conf), ...]

    # 2) Classify each OCR line as PII (email/phone/credit_card/address_text)
    for raw_text, (x, y, w, h), conf in ocr_lines:
        kind = classify_ocr_text(raw_text)
        if not kind:
            continue

        masked = mask_text_for_privacy(kind, raw_text)
        findings.append(
            ImageFinding(
                kind=kind,
                bbox=(x, y, w, h),                    # normalized 0..1 (xywh)
                conf=float(min(1.0, conf)),
                source="ocr+rules",
                ver=f"{MODEL_VER['ocr']}|{MODEL_VER['pii_rules']}",
                text=masked,                          # masked text for UI tooltip
            )
        )
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        warnings.append(warning_for_kind(kind))

    # 2b) Faces
    for (x, y, w, h, conf) in faces(img_bytes, conf_th=0.5):  # should also be normalized xywh
        findings.append(
            ImageFinding(
                kind="face",
                bbox=(x, y, w, h),
                conf=float(conf),
                source="yolov8-face",
                ver=MODEL_VER["face"],
                text=None,
            )
        )
        kind_counts["face"] = kind_counts.get("face", 0) + 1
        warnings.append(warning_for_kind(kind))
    
    # 3) Landmarks detection
    for (cls_name, x, y, w, h, conf) in landmarks(img_bytes, conf_th=0.25):
        findings.append(
            ImageFinding(
                kind=cls_name,             
                bbox=(x, y, w, h),
                conf=conf,
                source="yolov8-landmarks",
                ver="YOLOv8-landmarks-0.1",
                text=None,
            )
        )
        kind_counts[cls_name] = kind_counts.get(cls_name, 0) + 1
        warnings.append(warning_for_kind(cls_name))

    # 4) Risk score (weights defined in config/default.yaml)
    risk = score(kind_counts)

    # 5) SAM Segmentation for high-confidence detections (not “risk”)
    masks = []
    for finding in findings:
        if finding.conf >= 0.85:  # detection confidence threshold
            x, y, w, h = finding.bbox  # normalized xywh
            # convert to pixel xyxy, clamp to image bounds
            x1 = max(0, min(W - 1, int(round(x * W))))
            y1 = max(0, min(H - 1, int(round(y * H))))
            x2 = max(0, min(W,     int(round((x + w) * W))))
            y2 = max(0, min(H,     int(round((y + h) * H))))
            if x2 > x1 and y2 > y1:
                # If SAM expects pixels, pass np_img; else pass img_bytes as your function requires
                mask = segment_within_bbox(np_img, (x1, y1, x2, y2))
                masks.append(mask)

    # DEBUGGING PURPOSES : Image with bbounding boxes and SAM segmentation
    overlay = np_img.copy()
    for f in findings:
        x, y, w, h = f.bbox  # normalized xywh
        x1 = int(x * W)
        y1 = int(y * H)
        x2 = int((x + w) * W)
        y2 = int((y + h) * H)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)  # green box
        cv2.putText(
            overlay,
            f.kind,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    if masks:
        fname,ext = os.path.splitext(filename)
        path="./tests/output"
        combined_mask = masks[0].copy()
        for m in masks[1:]:
            combined_mask |= m
        overlay = visualize_mask(overlay, combined_mask, alpha=0.5)
        Image.fromarray(overlay).save(f"{path}/{fname}_masks{ext}")
        
        # 6) Inpainting with laMa 
        mask_pil = Image.fromarray((combined_mask.astype(np.uint8) * 255)).convert("L")
        mask_pil = mask_pil.resize(pil_img.size, Image.NEAREST)
        mask_pil = mask_pil.point(lambda p: 255 if p > 127 else 0, mode="L")
        
        img_path  = f"{path}/{fname}_src{ext}"       # use PNG to avoid JPEG artifacts
        mask_path = f"{path}/{fname}_mask{ext}"
        save_path = f"{path}/{fname}_inpainted{ext}"
        
        pil_img.save(img_path)
        mask_pil.save(mask_path)
        inpaint(img_path, mask_path, save_path)

    return AnalyzeImageResponse(
        findings=findings,
        riskScore=risk,
        imageShape=(W, H),
        coordSpace="normalized",  # your bboxes in findings are normalized
        degraded=False,
        warnings=warnings,
        masks=masks,
    )
