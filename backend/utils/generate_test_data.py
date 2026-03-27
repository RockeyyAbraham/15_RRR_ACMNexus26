import cv2
import os
import argparse
import numpy as np

def generate_pirated_copy_cv2(input_path, output_dir):
    """Generate 'pirated' versions of video using OpenCV (fallback for ffmpeg)."""
    if not os.path.exists(input_path):
        print(f"❌ Input video not found: {input_path}")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {input_path}")
        return

    # Metadata
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # 1. Low Resolution (240p)
    low_res_path = os.path.join(output_dir, f"{base_name}_240p.mp4")
    out_low = cv2.VideoWriter(low_res_path, fourcc, fps, (int(width * (240/height)), 240))

    # 2. Cropped (4:3)
    cropped_path = os.path.join(output_dir, f"{base_name}_cropped.mp4")
    crop_w = int(height * 4/3)
    start_x = (width - crop_w) // 2
    out_crop = cv2.VideoWriter(cropped_path, fourcc, fps, (crop_w, height))

    print(f"--- Processing Video with OpenCV (FFmpeg fallback) ---")
    frame_count = 0
    while cap.isOpened() and frame_count < 300: # Limit to first 300 frames for speed
        ret, frame = cap.read()
        if not ret:
            break

        # 240p
        low_frame = cv2.resize(frame, (int(width * (240/height)), 240))
        out_low.write(low_frame)

        # Cropped
        if start_x >= 0:
            crop_frame = frame[:, start_x:start_x+crop_w]
            out_crop.write(crop_frame)

        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    out_low.release()
    out_crop.release()

    print(f"✓ Success - Generated 240p and Cropped versions using OpenCV")
    print(f"✨ Test data generated in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel Test Data Generator - OpenCV Fallback")
    parser.add_argument("input", help="Path to original video")
    parser.add_argument("--outdir", default="assets/videos/pirated", help="Output directory")
    
    args = parser.parse_args()
    generate_pirated_copy_cv2(args.input, args.outdir)
