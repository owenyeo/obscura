<!--
Copyright 2025 Obscura
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
-->
# Obscura — Backend

FastAPI service for detecting privacy risks in text/images and returning **findings + bounding boxes** for the frontend overlay.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh
# open http://localhost:8080/healthz
```

### Docker

```bash
docker build -t privacy-shadows-api ./backend
docker run -p 8080:8080 -w /app -v $(pwd)/backend:/app privacy-shadows-api
```

### Endpoints

- `POST /analyze/text` → findings (email/phone/address_stub), riskScore  
- `POST /analyze/image` (multipart) → findings (faces/ocr stubs), riskScore

See `src/api/routes_analyze.py` and `src/schemas/*`.
