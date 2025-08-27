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

from typing import List, Dict
from src.schemas.common import ImageFinding
from src.schemas.analyze_image import AnalyzeImageResponse
from src.models.ocr import ocr
from src.models.faces import faces
from src.models.pii_from_text import classify_ocr_text, mask_text_for_privacy
from src.services.risk_scoring import score
from src.services.utils_warnings import warning_for_kind

MODEL_VER = {"ocr": "paddleocr-2.7", "pii_rules": "pii-regex-1.0", "face": "YOLOv8"}

async def analyze_image(img_bytes: bytes, modes: str | None, policy: str | None) -> AnalyzeImageResponse:
    findings: List[ImageFinding] = []
    warnings: List[str] = []
    kind_counts: Dict[str, int] = {}

    # 1) OCR to extract text blocks + coords
    ocr_lines = ocr(img_bytes)

    # 2) Classify each OCR line as PII (email/phone/credit_card/address_text)
    for raw_text, (x, y, w, h), conf in ocr_lines:
        kind = classify_ocr_text(raw_text)
        if not kind:
            continue

        masked = mask_text_for_privacy(kind, raw_text)
        findings.append(
            ImageFinding(
                kind=kind,
                bbox=(x, y, w, h),     # normalized 0..1
                conf=float(min(1.0, conf)),  # OCR conf as a proxy
                source="ocr+rules",
                ver=f"{MODEL_VER['ocr']}|{MODEL_VER['pii_rules']}",
                text=masked,           # masked text for UI tooltip
            )
        )
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        warnings.append(warning_for_kind(kind))
    
    for (x, y, w, h, conf) in faces(img_bytes, conf_th=0.5):
        findings.append(
            ImageFinding(
                kind="face",
                bbox=(x, y, w, h),
                conf=conf,
                source="yolov8-face",
                ver=MODEL_VER["face"],
                text=None,
            )
        )
        kind_counts["face"] = kind_counts.get("face", 0) + 1

    # 3) Risk score (weights defined in config/default.yaml)
    risk = score(kind_counts)

    return AnalyzeImageResponse(
        findings=findings,
        riskScore=risk,
        imageShape=(0, 0),
        coordSpace="normalized",
        degraded=False,
        warnings=warnings,
    )
