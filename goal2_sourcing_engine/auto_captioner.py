import os
import time
import requests
import subprocess
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AutoCaptioner:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    def float_to_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def transcribe_audio_to_srt(self, audio_path: str) -> str:
        """
        Transcribes audio using Groq's Whisper API and generates SRT subtitle content.
        Returns the SRT content as a string, or None if failed.
        """
        if not self.api_key:
            print("[-] Groq API Key not found for transcription.")
            return None

        if not os.path.exists(audio_path):
            print(f"[-] Audio file not found: {audio_path}")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json"
        }

        try:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (os.path.basename(audio_path), f, "audio/mp3")
                }
                print(f"[Captioner] Sending audio to Groq Whisper: {os.path.basename(audio_path)}...")
                response = requests.post(self.endpoint, headers=headers, data=data, files=files, timeout=45)
                response.raise_for_status()
                
            res_json = response.json()
            segments = res_json.get("segments", [])
            
            if not segments:
                print("[-] No segments returned in transcription response.")
                # fallback to raw text block if no segments but text exists
                text = res_json.get("text", "")
                if text:
                    segments = [{"start": 0.0, "end": len(text)/15.0, "text": text}]
                else:
                    return None

            srt_parts = []
            for i, seg in enumerate(segments, 1):
                start = self.float_to_srt_time(seg["start"])
                end = self.float_to_srt_time(seg["end"])
                text = seg["text"].strip()
                srt_parts.append(f"{i}\n{start} --> {end}\n{text}\n\n")

            return "".join(srt_parts)

        except Exception as e:
            print(f"[-] Transcription error: {e}")
            return None

    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str) -> bool:
        """
        Uses FFmpeg to burn subtitles from an SRT file into a video.
        Uses relative paths for the subtitle file to bypass Windows drive letter formatting bugs.
        """
        if not os.path.exists(video_path):
            print(f"[-] Video not found: {video_path}")
            return False

        if not os.path.exists(srt_path):
            print(f"[-] Subtitle file not found: {srt_path}")
            return False

        # Get relative paths for subtitles to avoid windows drive letter filter escaping issues
        cwd = os.getcwd()
        rel_srt_path = os.path.relpath(srt_path, cwd).replace("\\", "/")
        
        # FFmpeg filter description: force a high-end bold centered subtitle look
        # PrimaryColour: white (&H00FFFFFF), Outline: black (&H00000000)
        # Fontname: Arial (highly compatible) or Outfit if installed, size 18
        vf_filter = (
            f"subtitles='{rel_srt_path}':force_style="
            f"'Fontname=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,"
            f"Alignment=2,MarginV=40'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", vf_filter,
            "-c:a", "copy",
            output_path
        ]

        try:
            print(f"[Captioner] Running FFmpeg burn-in...")
            # Use shell=True on Windows to ensure ffmpeg is found correctly in environment
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[+] Subtitles burned in successfully: {output_path}")
                return True
            return False
        except subprocess.CalledProcessError as e:
            print(f"[-] FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')}")
            return False
        except Exception as e:
            print(f"[-] Error running FFmpeg: {e}")
            return False

    def caption_video(self, video_path: str, audio_path: str, output_path: str) -> Optional[str]:
        """
        Complete pipeline: Audio transcription -> SRT creation -> Video burn-in.
        Returns path to captioned video if successful.
        """
        srt_content = self.transcribe_audio_to_srt(audio_path)
        if not srt_content:
            print("[-] Captioning failed: unable to transcribe audio.")
            return None

        # Write SRT file temporarily in working directory to keep path simple
        temp_srt = f"temp_subs_{int(time.time())}.srt"
        try:
            with open(temp_srt, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            success = self.burn_subtitles(video_path, temp_srt, output_path)
            if success:
                return output_path
            return None
        finally:
            if os.path.exists(temp_srt):
                try:
                    os.remove(temp_srt)
                except:
                    pass
