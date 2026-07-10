import os
import sys
import time
import argparse
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional

# Import Router and Utilities
from generation_router import GenerationRouter, safe_print
from voice_generator import VoiceGenerator
from auto_captioner import AutoCaptioner

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_ugc")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_video_duration(video_path: str) -> float:
    """Helper to query video duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        safe_print(f"[-] Failed to read video duration: {e}. Defaulting to 5.0s")
        return 5.0

async def compile_ugc_ad(video_prompt: str, voice_text: str, voice_name: str, headless: bool, ref_image_paths: Optional[List[str]] = None):
    safe_print("=" * 60)
    safe_print("          OBSCURA UNIFIED UGC AD CREATOR PIPELINE")
    safe_print("=" * 60)
    
    router = GenerationRouter()
    voice_worker = VoiceGenerator()
    
    timestamp = int(time.time())
    audio_path = os.path.join(OUTPUT_DIR, f"narration_{timestamp}.mp3")
    
    # 1. Parallelize Video Generation and Audio Generation
    safe_print("[*] Launching video generation and audio voiceover in parallel...")
    
    video_task = asyncio.create_task(
        router.generate_video(
            prompt=video_prompt,
            ref_image_paths=ref_image_paths,
            aspect="9:16",
            output_prefix=f"raw_clip_{timestamp}"
        )
    )
    
    audio_task = asyncio.create_task(
        voice_worker.generate_audio(
            text=voice_text,
            voice_name=voice_name,
            output_path=audio_path
        )
    )
    
    # Wait for both to complete
    video_paths, audio_result = await asyncio.gather(video_task, audio_task)
    
    if not video_paths:
        safe_print("[!] Video generation failed via all providers in the cascade cascade.")
        return
    
    video_path = video_paths[0]
    
    if not audio_result or not os.path.exists(audio_result):
        safe_print("[!] Voice generation failed. Exiting.")
        return

    safe_print(f"[+] Video loop ready: {video_path}")
    safe_print(f"[+] Audio track ready: {audio_result}")

    # 2. Transcribe Audio for Auto-Captioning
    safe_print("\n[*] Transcribing audio track for auto-captioning...")
    captioner = AutoCaptioner()
    srt_content = captioner.transcribe_audio_to_srt(audio_result)
    
    temp_srt = None
    if srt_content:
        temp_srt = os.path.join(os.getcwd(), f"temp_subs_{timestamp}.srt")
        with open(temp_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)
        safe_print("[+] Transcribed text and generated subtitles.")
    else:
        safe_print("[-] Auto-captioning skipped (transcription failed or no API key).")

    # 3. Post-Processing & Muxing with FFmpeg
    safe_print("\n[*] Step 3: Performing advanced FFmpeg post-processing...")
    
    duration = get_video_duration(video_path)
    fps = 30
    total_frames = int(duration * fps)
    fade_out_start = max(0, total_frames - 25) # 25 frames fade out
    
    final_output_path = os.path.join(OUTPUT_DIR, f"ugc_ad_{timestamp}.mp4")
    
    # Check for brand logo
    logo_path = os.path.join(BASE_DIR, "obscura_logo.png")
    has_logo = os.path.exists(logo_path)
    
    # Check for background music assets
    music_path = None
    music_dir = os.path.join(BASE_DIR, "assets", "music")
    if os.path.exists(music_dir):
        music_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav"))]
        if music_files:
            music_path = random.choice(music_files)
            safe_print(f"[+] Found background music asset: {os.path.basename(music_path)}")
            
    filter_parts = []
    inputs = ["-i", video_path]
    
    # Video processing: scale, pad, fade-in, fade-out
    v_filter = f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fade=in:0:25,fade=out:{fade_out_start}:25"
    
    # Apply subtitles if generated
    if temp_srt:
        rel_srt_path = os.path.relpath(temp_srt, os.getcwd()).replace("\\", "/")
        v_filter += f",subtitles='{rel_srt_path}':force_style='Fontname=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=50'"
        
    v_filter += "[v_base]"
    filter_parts.append(v_filter)
    
    # Apply logo if exists
    if has_logo:
        inputs += ["-i", logo_path]
        filter_parts.append(f"[v_base][1:v]scale=150:-1[logo];[v_base][logo]overlay=main_w-overlay_w-30:30[v_final]")
        v_out_map = "[v_final]"
        logo_input_idx = 1
        audio_input_idx = 2
    else:
        v_out_map = "[v_base]"
        logo_input_idx = None
        audio_input_idx = 1
        
    inputs += ["-i", audio_result]
    
    music_input_idx = None
    if music_path:
        inputs += ["-i", music_path]
        music_input_idx = audio_input_idx + 1
        # Mix voiceover and background music (music volume set to 15%)
        filter_parts.append(f"[{audio_input_idx}:a]volume=1.0[voice];[{music_input_idx}:a]volume=0.15[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[a_final]")
        a_out_map = "[a_final]"
    else:
        a_out_map = f"{audio_input_idx}:a"
        
    filter_complex_str = ";".join(filter_parts)
    
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex_str,
        "-map", v_out_map,
        "-map", a_out_map,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        final_output_path
    ]
    
    try:
        safe_print(f"[*] Running FFmpeg Muxing command...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        if os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
            safe_print("\n" + "=" * 60)
            safe_print(f"🎉 SUCCESS! UGC Ad Creative compiled successfully.")
            safe_print(f"   Destination File: {final_output_path}")
            safe_print("=" * 60)
        else:
            safe_print("[!] FFmpeg execution completed, but final output is missing or empty.")
            
    except subprocess.CalledProcessError as e:
        safe_print(f"[-] FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        safe_print(f"[-] Failed to execute FFmpeg: {e}")
    finally:
        # Clean up temp subtitle file
        if temp_srt and os.path.exists(temp_srt):
            try:
                os.remove(temp_srt)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Generate complete captioned UGC video ads in one command.")
    parser.add_argument("--prompt", type=str, required=True, help="Video prompt description.")
    parser.add_argument("--script", type=str, required=True, help="Voiceover text narration script.")
    parser.add_argument("--voice", type=str, default="default", help="Voice model profile name.")
    parser.add_argument("--non-headless", action="store_true", help="Run Playwright video scraper in non-headless mode.")
    parser.add_argument("--refs", type=str, nargs="*", help="Optional list of reference image paths.")
    
    args = parser.parse_args()
    
    asyncio.run(compile_ugc_ad(
        video_prompt=args.prompt,
        voice_text=args.script,
        voice_name=args.voice,
        headless=not args.non_headless,
        ref_image_paths=args.refs
    ))

if __name__ == "__main__":
    main()
