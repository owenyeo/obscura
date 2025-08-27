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

from fastapi.testclient import TestClient
from src.main import app
from io import BytesIO
import base64

client = TestClient(app)

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_text_analyze():
    r = client.post("/analyze/text", json={"text": "Mail me at a@b.com or +65 9123 4567"})
    assert r.status_code == 200
    body = r.json()
    assert "findings" in body
    assert isinstance(body["riskScore"], int)

def test_image_analyze_empty_returns_200():
    # a tiny blank png (won't find PII but should return 200)
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAD+wGmE3+gYwAAAABJRU5ErkJggg==")
    r = client.post("/analyze/image", files={"file": ("x.png", png, "image/png")})
    assert r.status_code == 200
    data = r.json()
    print(data)
    assert "findings" in data
    assert "riskScore" in data

def test_image_analyze_preview():
    from fastapi.testclient import TestClient
    from src.main import app
    client = TestClient(app)

    with open("tests/assets/sample.png", "rb") as f:
        r = client.post("/analyze/image", files={"file": ("sample.png", f, "image/png")})
    print("\nRESPONSE:", r.status_code, r.json()) 

    assert r.status_code == 200