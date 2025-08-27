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

from typing import List
from src.schemas.common import TextFinding
from src.schemas.analyze_text import AnalyzeTextRequest, AnalyzeTextResponse
from src.models.regex_rules import find_emails, find_phones
from src.models.text_ner import find_addresses_stub
from src.services.risk_scoring import score

MODEL_VER = {"regex": "regex-1.0", "ner": "stub-addr-0.1"}

async def analyze_text(req: AnalyzeTextRequest) -> AnalyzeTextResponse:
    text = req.text
    findings: List[TextFinding] = []

    for s, e in find_emails(text):
        findings.append(TextFinding(kind="email", span=(s, e), conf=0.99, source="regex", ver=MODEL_VER["regex"]))
    for s, e in find_phones(text):
        findings.append(TextFinding(kind="phone", span=(s, e), conf=0.98, source="regex", ver=MODEL_VER["regex"]))

    for s, e, conf in find_addresses_stub(text):
        findings.append(TextFinding(kind="address_text", span=(s, e), conf=conf, source="ner", ver=MODEL_VER["ner"]))

    counts = {}
    for f in findings:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    risk = score(counts)

    return AnalyzeTextResponse(findings=findings, riskScore=risk, degraded=False, warnings=[])
