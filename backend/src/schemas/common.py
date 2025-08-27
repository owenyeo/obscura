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

from pydantic import BaseModel, Field
from typing import Literal, Tuple, Optional

KindText = Literal["email", "phone", "national_id", "address_text"]
KindImage = Literal[
    "face",
    "license_plate",
    "document_id",
    "address_sign",
    # PII via OCR:
    "email",
    "phone",
    "credit_card",
    "address_text",
    "dob",
    "national_id",
    "passport",
    "iban",
    "bic",
]

class TextFinding(BaseModel):
    kind: KindText
    span: Tuple[int, int] = Field(..., description="UTF-16 indices")
    conf: float
    source: str
    ver: str

class ImageFinding(BaseModel):
    kind: KindImage
    bbox: Tuple[float, float, float, float]  # normalized x,y,w,h
    conf: float
    source: str
    ver: str
    text: Optional[str] = None  # for OCR-derived items
