"""Utilities for generating piracy variants and running dual-engine analytics."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import cv2
import numpy as np


@dataclass
class VariantSpec:
    filename: str
    description: str
    issue_type: str
    family: str  # video or audio


VARIANT_SPECS: List[VariantSpec] = [
    VariantSpec("240p.mp4", "240p Compression", "video_compression", "video"),
    VariantSpec("colorshift.mp4", "Color Shifted", "color_manipulation", "video"),
    VariantSpec("cropped.mp4", "Cropped", "spatial_crop", "video"),
    VariantSpec("extreme.mp4", "Extreme Degradation", "extreme_degradation", "video"),
    VariantSpec("letterbox.mp4", "Letterboxed", "letterbox", "video"),
    VariantSpec("mirrored.mp4", "Mirrored", "mirroring", "video"),
    VariantSpec("rotate.mp4", "Rotation", "rotation", "video"),
    VariantSpec("stretch.mp4", "Aspect Ratio Stretch", "aspect_ratio_distortion", "video"),
    VariantSpec("watermark.mp4", "Watermark", "watermark_overlay", "video"),
    VariantSpec("lowbitrate.mp4", "Low Bitrate (64kbps)", "audio_low_bitrate", "audio"),
    VariantSpec("pitchshift.mp4", "Pitch Shifted (+2 semitones)", "audio_pitch_shift", "audio"),
    VariantSpec("speed_audio.mp4", "Speed Change (1.5x audio)", "audio_speed_change", "audio"),
    VariantSpec("mono.mp4", "Mono Conversion", "audio_channel_mix", "audio"),
    VariantSpec("equalized.mp4", "Bass Boosted", "audio_equalization", "audio"),
    VariantSpec("trimmed.mp4", "Trimmed (30s)", "temporal_trim", "audio"),
    VariantSpec("noisy.mp4", "Background Noise", "audio_noise_overlay", "audio"),
    VariantSpec("phase_inverted.mp4", "Phase Inverted", "audio_phase_inversion", "audio"),
]


def _find_ffmpeg() -> Optional[str]:
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    common = Path(r"C:\Users\rishi\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
    if common.exists():
        return str(common)

    from shutil import which

    resolved = which("ffmpeg")
    return resolved


def _open_video_writer(path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(path), fourcc, fps if fps > 0 else 30.0, (width, height))


def _generate_240p_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    scale = 240.0 / max(h, 1)
    out_w = max(2, int(w * scale))
    out_h = 240
    writer = _open_video_writer(output_path, fps, out_w, out_h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        resized = cv2.resize(frame, (out_w, out_h))
        writer.write(resized)
        frames += 1

    cap.release()
    writer.release()


def _generate_colorshift_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = _open_video_writer(output_path, fps, w, h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + 24) % 180
        shifted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        writer.write(shifted)
        frames += 1

    cap.release()
    writer.release()


def _generate_cropped_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    x = int(w * 0.1)
    y = int(h * 0.1)
    cw = int(w * 0.8)
    ch = int(h * 0.8)
    writer = _open_video_writer(output_path, fps, cw, ch)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        cropped = frame[y : y + ch, x : x + cw]
        writer.write(cropped)
        frames += 1

    cap.release()
    writer.release()


def _generate_extreme_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    scale = 240.0 / max(h, 1)
    sw = max(2, int(w * scale))
    sh = 240
    x = int(sw * 0.1)
    y = int(sh * 0.1)
    cw = int(sw * 0.8)
    ch = int(sh * 0.8)
    writer = _open_video_writer(output_path, fps, cw, ch)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (sw, sh))
        cropped = small[y : y + ch, x : x + cw]
        noise = np.random.normal(0, 25, cropped.shape).astype(np.int16)
        noisy = np.clip(cropped.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        blurred = cv2.GaussianBlur(noisy, (3, 3), 0)
        writer.write(blurred)
        frames += 1

    cap.release()
    writer.release()


def _generate_letterbox_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    target_h = int(w * 9 / 21)
    resized_h = max(2, target_h - 80)
    resized_w = int(w * resized_h / max(h, 1))
    writer = _open_video_writer(output_path, fps, w, target_h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        resized = cv2.resize(frame, (resized_w, resized_h))
        canvas = np.zeros((target_h, w, 3), dtype=np.uint8)
        y0 = (target_h - resized_h) // 2
        x0 = (w - resized_w) // 2
        canvas[y0 : y0 + resized_h, x0 : x0 + resized_w] = resized
        writer.write(canvas)
        frames += 1

    cap.release()
    writer.release()


def _generate_mirrored_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = _open_video_writer(output_path, fps, w, h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(cv2.flip(frame, 1))
        frames += 1

    cap.release()
    writer.release()


def _generate_rotate_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = _open_video_writer(output_path, fps, h, w)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
        frames += 1

    cap.release()
    writer.release()


def _generate_stretch_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    new_w = int(h * 4 / 3)
    writer = _open_video_writer(output_path, fps, new_w, h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(cv2.resize(frame, (new_w, h)))
        frames += 1

    cap.release()
    writer.release()


def _generate_watermark_variant(input_path: Path, output_path: Path, max_frames: int = 300):
    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = _open_video_writer(output_path, fps, w, h)

    frames = 0
    while frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.putText(frame, "PIRATED COPY", (32, max(40, h - 48)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        writer.write(frame)
        frames += 1

    cap.release()
    writer.release()


def _run_ffmpeg(ffmpeg_path: str, args: List[str]):
    cmd = [ffmpeg_path, *args]
    subprocess.run(cmd, check=True, capture_output=True)


def _generate_audio_variant_with_ffmpeg(input_path: Path, output_path: Path, variant: str, ffmpeg_path: str):
    if variant == "lowbitrate.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-c:v", "copy", "-c:a", "aac", "-b:a", "64k", "-y", str(output_path)])
    elif variant == "pitchshift.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-af", "asetrate=44100*1.12246,atempo=0.8909", "-c:v", "copy", "-y", str(output_path)])
    elif variant == "speed_audio.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-filter:a", "atempo=1.5", "-c:v", "copy", "-y", str(output_path)])
    elif variant == "mono.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-ac", "1", "-c:v", "copy", "-y", str(output_path)])
    elif variant == "equalized.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-filter:a", "equalizer=f=100:width_type=h:width=100:g=10", "-c:v", "copy", "-y", str(output_path)])
    elif variant == "trimmed.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-t", "30", "-c", "copy", "-y", str(output_path)])
    elif variant == "noisy.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-filter:a", "volume=0.9", "-c:v", "copy", "-y", str(output_path)])
    elif variant == "phase_inverted.mp4":
        _run_ffmpeg(ffmpeg_path, ["-i", str(input_path), "-filter:a", "volume=-1.0", "-c:v", "copy", "-y", str(output_path)])
    else:
        raise ValueError(f"Unknown audio variant: {variant}")


def generate_piracy_variants(original_video: Path, output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = _find_ffmpeg()
    results: List[Dict[str, Any]] = []

    for spec in VARIANT_SPECS:
        output_path = output_dir / spec.filename
        item: Dict[str, Any] = {
            "filename": spec.filename,
            "description": spec.description,
            "issue_type": spec.issue_type,
            "family": spec.family,
            "path": str(output_path),
            "status": "generated",
            "note": None,
        }

        try:
            if spec.filename == "240p.mp4":
                _generate_240p_variant(original_video, output_path)
            elif spec.filename == "colorshift.mp4":
                _generate_colorshift_variant(original_video, output_path)
            elif spec.filename == "cropped.mp4":
                _generate_cropped_variant(original_video, output_path)
            elif spec.filename == "extreme.mp4":
                _generate_extreme_variant(original_video, output_path)
            elif spec.filename == "letterbox.mp4":
                _generate_letterbox_variant(original_video, output_path)
            elif spec.filename == "mirrored.mp4":
                _generate_mirrored_variant(original_video, output_path)
            elif spec.filename == "rotate.mp4":
                _generate_rotate_variant(original_video, output_path)
            elif spec.filename == "stretch.mp4":
                _generate_stretch_variant(original_video, output_path)
            elif spec.filename == "watermark.mp4":
                _generate_watermark_variant(original_video, output_path)
            else:
                if not ffmpeg_path:
                    raise RuntimeError("ffmpeg not available")
                _generate_audio_variant_with_ffmpeg(original_video, output_path, spec.filename, ffmpeg_path)

            if not output_path.exists():
                raise RuntimeError("variant output file was not created")
        except Exception as exc:
            # Keep the benchmark flowing even when an audio filter is unavailable.
            shutil.copy2(original_video, output_path)
            item["status"] = "fallback_copy"
            item["note"] = f"{type(exc).__name__}: {exc}"

        results.append(item)

    return results


def run_piracy_benchmark(
    original_video: Path,
    output_dir: Path,
    dual_engine: Any,
    progress_cb: Optional[Callable[[str], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    if progress_cb:
        progress_cb("generating_variants")
    variants = generate_piracy_variants(original_video, output_dir)

    analytics: List[Dict[str, Any]] = []

    for variant in variants:
        if cancel_cb and cancel_cb():
            raise RuntimeError("Job cancelled")

        if progress_cb:
            progress_cb(f"analyzing_{variant['filename']}")

        result = dual_engine.detect_piracy(str(Path(variant["path"])), str(original_video), mode="dual")
        analytics.append(
            {
                "filename": variant["filename"],
                "description": variant["description"],
                "issue_type": variant["issue_type"],
                "generation_status": variant["status"],
                "generation_note": variant["note"],
                "video_confidence": round(float(result.get("video_confidence", 0.0)), 2),
                "audio_confidence": round(float(result.get("audio_confidence", 0.0)), 2),
                "combined_confidence": round(float(result.get("combined_confidence", 0.0)), 2),
                "pattern_score": round(float(result.get("pattern_score", 0.0)), 2),
                "adaptive_threshold": round(float(result.get("adaptive_threshold", 0.0)), 2),
                "decision_reason": result.get("decision_reason", "unknown"),
                "is_detected": bool(result.get("is_match", False)),
            }
        )

    detected = sum(1 for item in analytics if item["is_detected"])
    total = len(analytics)

    return {
        "variant_count": total,
        "detected_count": detected,
        "detection_rate": round((detected / total) * 100.0, 2) if total else 0.0,
        "variants": analytics,
        "output_dir": str(output_dir),
    }
