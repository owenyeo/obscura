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

import re
import phonenumbers
from typing import List, Tuple, Optional

# Compile patterns once
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Luhn-like 13–19 digits (spaced/dashed). Y
CARD_RE  = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
# Simple postal/house-number-ish cues (tune for your locale)
ADDRESS_CUES = re.compile(r"\b(\d+\s+[A-Za-z]{2,}|\bBlk\s*\d+|\bAve|\bAvenue|\bRd\.?|\bRoad|\bStreet|\bSt\.?)\b", re.I)

def classify_ocr_text(s: str) -> Optional[str]:
    """
    Map raw OCR text -> PII kind (email|phone|credit_card|address_text) or None.
    """
    s_clean = s.strip()
    if not s_clean:
        return None
    # Email
    if EMAIL_RE.search(s_clean):
        return "email"
    # Phone (try to parse any long digit span as a number)
    for m in re.finditer(r"[+()0-9\- \.]{7,}", s_clean):
        cand = m.group(0)
        try:
            n = phonenumbers.parse(cand, None)
            if phonenumbers.is_valid_number(n):
                return "phone"
        except Exception:
            pass
    # Credit card
    if CARD_RE.search(s_clean):
        return "credit_card"
    # Address-ish
    if ADDRESS_CUES.search(s_clean):
        return "address_text"
    return None

def mask_text_for_privacy(kind: str, s: str) -> str:
    """
    Optional: return a masked version of OCR text so you never echo raw PII.
    """
    if kind == "email":
        return re.sub(r"(^.).*?(@)", r"\1***\2", s)
    if kind == "phone":
        return re.sub(r"\d", "•", s)
    if kind == "credit_card":
        return re.sub(r"\d(?=\d{4})", "•", s)
    return s  # keep generic/addresses as-is or implement a smarter masker