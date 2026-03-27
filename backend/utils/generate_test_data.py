import subprocess
import os
import argparse
import sys

def run_ffmpeg_command(command, description):
    """Run an ffmpeg command and handle errors."""
    print(f"--- {description} ---")
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✓ Success")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: ffmpeg not found. Please ensure it is installed and in your PATH.")
        return False
    return True

def generate_pirated_copy(input_path, output_dir):
    """Generate various 'pirated' versions of the input video."""
    if not os.path.exists(input_path):
        print(f"❌ Input video not found: {input_path}")
        return

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    # 1. Low Resolution (240p)
    low_res_path = os.path.join(output_dir, f"{base_name}_240p.mp4")
    run_ffmpeg_command([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=-1:240",
        "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
        low_res_path
    ], "Generating 240p version")

    # 2. Heavily Compressed (Low Bitrate)
    compressed_path = os.path.join(output_dir, f"{base_name}_compressed.mp4")
    run_ffmpeg_command([
        "ffmpeg", "-y", "-i", input_path,
        "-b:v", "200k", "-maxrate", "200k", "-bufsize", "400k",
        compressed_path
    ], "Generating heavily compressed version")

    # 3. Cropped (4:3 aspect ratio from center)
    cropped_path = os.path.join(output_dir, f"{base_name}_cropped.mp4")
    run_ffmpeg_command([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "crop=ih*4/3:ih",
        cropped_path
    ], "Generating cropped (4:3) version")

    # 4. Temporal Clip (10 seconds from middle)
    # First get duration
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", input_path
        ], capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        start_time = max(0, duration / 2 - 5)
        
        clip_path = os.path.join(output_dir, f"{base_name}_clip.mp4")
        run_ffmpeg_command([
            "ffmpeg", "-y", "-i", input_path,
            "-ss", str(start_time), "-t", "10",
            "-c", "copy",
            clip_path
        ], "Generating 10-second temporal clip")
    except Exception as e:
        print(f"⚠ Could not generate temporal clip: {e}")

    # 5. Combined (240p + Cropped + Compressed)
    combined_path = os.path.join(output_dir, f"{base_name}_extreme_piracy.mp4")
    run_ffmpeg_command([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=-1:240,crop=ih*4/3:ih",
        "-b:v", "150k",
        combined_path
    ], "Generating extreme piracy version (240p + crop + compress)")

    print(f"\n✨ All 'pirated' copies generated in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel Test Data Generator - Simulate Piracy")
    parser.add_argument("input", help="Path to the original video file")
    parser.add_argument("--outdir", default="assets/videos/pirated", help="Output directory for generated copies")
    
    args = parser.parse_args()
    
    # Ensure backend/utils exists
    os.makedirs("backend/utils", exist_ok=True)
    
    generate_pirated_copy(args.input, args.outdir)
