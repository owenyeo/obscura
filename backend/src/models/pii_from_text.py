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
# Simple postal/house-number-ish cues
ADDRESS_CUES = re.compile(r"\b(\d+\s+[A-Za-z]{2,}|\bBlk\s*\d+|\bAve|\bAvenue|\bRd\.?|\bRoad|\bStreet|\bSt\.?)\b", re.I)

PHONE_RE = re.compile(r"[+()0-9\- \.]{7,}")

# National IDs
NATIONAL_ID_RE = re.compile(r"\b[A-Z0-9]{8,12}\b")

# Passport numbers 
PASSPORT_RE = re.compile(r"\b([A-Z]{1,2}[0-9]{6,8})\b", re.I)

# Dates of birth (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.)
DOB_RE = re.compile(r"\b(0?[1-9]|[12][0-9]|3[01])[- /.](0?[1-9]|1[0-2])[- /.](19|20)\d{2}\b")

# IBAN (international bank account number) – 15–34 alphanumeric
IBAN_RE = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b")

# Swift/BIC code 
BIC_RE = re.compile(r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b")

# License plates 
LICENSE_PLATE_RE = re.compile(r"\b([A-Z]{1,3}[- ]?\d{1,4}[A-Z]{0,3})\b", re.I)

def classify_ocr_text(s: str) -> Optional[str]:
    s_clean = s.strip()
    if not s_clean:
        return None

    # Email
    if EMAIL_RE.search(s_clean):
        return "email"

    # Phone
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

    # DOB
    if DOB_RE.search(s_clean):
        return "dob"

    # National ID
    if NATIONAL_ID_RE.search(s_clean):
        return "national_id"

    # Passport
    if PASSPORT_RE.search(s_clean):
        return "passport"

    # IBAN
    if IBAN_RE.search(s_clean):
        return "iban"

    # BIC
    if BIC_RE.search(s_clean):
        return "bic"

    # License plate
    if LICENSE_PLATE_RE.search(s_clean):
        return "license_plate"

    # Address-ish
    if ADDRESS_CUES.search(s_clean):
        return "address_text"

    return None

def mask_text_for_privacy(kind: str, s: str) -> str:
    if kind == "email":
        return re.sub(r"(^.).*?(@)", r"\1***\2", s)
    if kind == "phone":
        return re.sub(r"\d", "•", s)
    if kind == "credit_card":
        return re.sub(r"\d(?=\d{4})", "•", s)
    if kind in {"ssn", "passport", "national_id", "license_plate"}:
        return re.sub(r"[A-Z0-9]", "•", s, flags=re.I)
    if kind in {"iban", "bic"}:
        return s[:4] + "•••" + s[-4:]
    if kind == "dob":
        return "••/••/••••"
    return s