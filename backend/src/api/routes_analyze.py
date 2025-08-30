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

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import Optional

from src.schemas.analyze_text import AnalyzeTextRequest, AnalyzeTextResponse
from src.schemas.analyze_image import AnalyzeImageResponse
from src.services.image_pipeline import analyze_image
from src.services.video_pipeline import analyze_video

router = APIRouter()

@router.post("/image", response_model=AnalyzeImageResponse)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    modes: Optional[str] = Form(None),
    policy: Optional[str] = Form(None),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    content = await file.read()
    return await analyze_image(content, modes=modes, policy=policy)

@router.post("/video", response_model=AnalyzeImageResponse)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    modes: Optional[str] = Form(None),
    policy: Optional[str] = Form(None),
):
    if file.content_type not in {"video/mp4", "video/quicktime"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    content = await file.read()
    return await analyze_video(content, modes=modes, policy=policy)
