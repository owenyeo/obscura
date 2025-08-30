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
from typing import List, Optional, Any
from .common import ImageFinding

class FlaggedFrame(BaseModel):
    frame_idx: int
    time_s: float
    timecode: str
    findings: List[ImageFinding] = Field(default_factory=list)  # or your concrete Finding schema
    riskScore: Optional[int] = 0
    degraded: bool = False
    warnings: list = []

class AnalyzeVideoResponse(BaseModel):
    fps: float
    frame_count: int
    kept_count: int
    frames: List[FlaggedFrame]
    peak_score: Optional[int] = 0
    params: dict
    warnings: List[str] = Field(default_factory=list)