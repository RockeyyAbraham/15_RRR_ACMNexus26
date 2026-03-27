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

    # 3. Color Shift (Brightness/Contrast)
    color_shift_path = os.path.join(output_dir, f"{base_name}_colorshift.mp4")
    out_color = cv2.VideoWriter(color_shift_path, fourcc, fps, (width, height))

    # 4. Extreme (240p + Crop + Color Shift)
    extreme_path = os.path.join(output_dir, f"{base_name}_extreme.mp4")
    out_extreme = cv2.VideoWriter(extreme_path, fourcc, fps, (crop_w, 240))

    print(f"--- Processing Video with OpenCV (All Piracy Types) ---")
    frame_count = 0
    while cap.isOpened() and frame_count < 300: # Limit for speed
        ret, frame = cap.read()
        if not ret:
            break

        # 1. 240p
        low_frame = cv2.resize(frame, (int(width * (240/height)), 240))
        out_low.write(low_frame)

        # 2. Cropped
        if start_x >= 0:
            crop_frame = frame[:, start_x:start_x+crop_w]
            out_crop.write(crop_frame)

        # 3. Color Shift (Simulate camcorder/filter)
        # Increase brightness and contrast
        color_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)
        out_color.write(color_frame)

        # 4. Extreme
        # Resize the cropped frame down to 240p tall, then apply color shift
        if start_x >= 0:
            ext_frame = cv2.resize(crop_frame, (int(crop_w * (240/height)), 240))
            ext_frame = cv2.convertScaleAbs(ext_frame, alpha=1.3, beta=40)
            out_extreme.write(ext_frame)

        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    out_low.release()
    out_crop.release()
    out_color.release()
    out_extreme.release()

    print(f"✓ Success - Generated 240p, Cropped, ColorShift, and Extreme versions.")
    print(f"✨ Test data generated in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel Test Data Generator - OpenCV Fallback")
    parser.add_argument("input", help="Path to original video")
    parser.add_argument("--outdir", default="assets/videos/pirated", help="Output directory")
    
    args = parser.parse_args()
    generate_pirated_copy_cv2(args.input, args.outdir)
