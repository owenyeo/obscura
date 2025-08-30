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

import os
import cv2
import json
import tempfile
import numpy as np
from typing import List, Dict, Optional
from datetime import timedelta
import asyncio

from .image_pipeline import analyze_image  # reuse your existing image analyzer
from ..schemas.analyze_video import AnalyzeVideoResponse, FlaggedFrame  # define below

def _tiny_hsv_hist(frame_bgr: np.ndarray, size=(160, 90), h_bins=32, s_bins=32) -> np.ndarray:
    tiny = cv2.resize(frame_bgr, size, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(tiny, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [h_bins, s_bins], [0, 180, 0, 256])
    hist = cv2.normalize(hist, None).flatten()
    return hist

def _hist_delta(h1: np.ndarray, h2: np.ndarray) -> float:
    # L1 distance keeps it simple/fast
    return float(np.sum(np.abs(h1 - h2)))

def _time_from_idx(idx: int, fps: float) -> float:
    return idx / fps if fps > 0 else 0.0

def _select_frames_tier_a(video_path: str, fps_cap: float, stride: int, pad_frames: int, hist_thresh: float) -> Dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Failed to open video for selection")

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    decode_step = max(1, int(round(src_fps / fps_cap))) if fps_cap and src_fps > 0 else 1
    kept = set()
    last_hist = None
    frame_idx = -1
    read_idx = -1

    while True:
        # skip frames to honor fps_cap
        for _ in range(decode_step):
            ret = cap.grab()
            read_idx += 1
            if not ret:
                break
        if not ret:
            break

        ok, frame = cap.retrieve()
        if not ok:
            break
        frame_idx = read_idx

        keep_periodic = (frame_idx % stride == 0)

        if last_hist is None:
            last_hist = _tiny_hsv_hist(frame)
            kept.add(frame_idx)
            continue

        h = _tiny_hsv_hist(frame)
        d = _hist_delta(h, last_hist)
        keep_hist = d > hist_thresh

        if keep_periodic or keep_hist:
            kept.add(frame_idx)
            last_hist = h

    cap.release()

    # pad +/- N frames around every kept frame
    if pad_frames > 0:
        padded = set()
        for k in kept:
            for d in range(-pad_frames, pad_frames + 1):
                idx = k + d
                if 0 <= idx < total_frames:
                    padded.add(idx)
        kept = padded

    kept_sorted = sorted(kept)
    return {"kept": kept_sorted, "src_fps": float(src_fps), "total_frames": total_frames}

async def analyze_video(
    video_bytes: bytes,
    modes: Optional[str] = None,
    policy: Optional[str] = None,
    fps_cap: float = 24.0,
    stride: int = 100,
    pad_frames: int = 6,
    hist_thresh: float = 0.30,
) -> AnalyzeVideoResponse:
    # write to temp file (OpenCV needs a path)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name

    try:
        sel = await asyncio.to_thread(_select_frames_tier_a, video_path, fps_cap, stride, pad_frames, hist_thresh)
        kept = sel["kept"]
        src_fps = sel["src_fps"]

        # now extract those frames and reuse analyze_image() per frame
        cap = cv2.VideoCapture(video_path)
        flagged_frames: List[FlaggedFrame] = []
        peak_score = 0

        for idx in kept:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue

            # JPEG encode to bytes to pass into analyze_image()
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not ok:
                continue
            img_bytes = buf.tobytes()

            # reuse your existing image pipeline
            img_res = await analyze_image(img_bytes, modes=modes, policy=policy)

            # Build video-friendly item (normalized bboxes assumed from image analyzer)
            t = _time_from_idx(idx, src_fps)
            flagged_frames.append(
                FlaggedFrame(
                    frame_idx=idx,
                    time_s=round(t, 3),
                    timecode=str(timedelta(seconds=t)),
                    findings=img_res.findings,
                    riskScore=img_res.riskScore,
                    degraded=getattr(img_res, "degraded", False),
                    warnings=getattr(img_res, "warnings", []),
                )
            )
            peak_score = max(peak_score, img_res.riskScore or 0)

        cap.release()

        return AnalyzeVideoResponse(
            fps=src_fps,
            frame_count=sel["total_frames"],
            kept_count=len(flagged_frames),
            frames=flagged_frames,
            peak_score=peak_score,
            params={
                "fps_cap": fps_cap,
                "stride": stride,
                "pad_frames": pad_frames,
                "hist_thresh": hist_thresh,
            },
            warnings=[],
        )
    finally:
        try:
            os.remove(video_path)
        except Exception:
            pass