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
from typing import List, Tuple

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

def find_emails(text: str) -> List[Tuple[int, int]]:
    return [m.span() for m in EMAIL_RE.finditer(text)]

def find_phones(text: str) -> List[Tuple[int, int]]:
    hits = []
    for m in re.finditer(r"[+()0-9\-\s]{7,}", text):
        candidate = m.group(0)
        try:
            n = phonenumbers.parse(candidate, None)
            if phonenumbers.is_valid_number(n):
                hits.append(m.span())
        except Exception:
            pass
    return hits
