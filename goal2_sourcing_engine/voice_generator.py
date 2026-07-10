import os
import sys
import urllib.parse
import subprocess
import shutil
import asyncio
import aiohttp
from typing import Optional

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

class VoiceGenerator:
    def __init__(self, base_url: str = "http://127.0.0.1:8769", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        # Same fallback key or .env key
        self.api_key = api_key or os.getenv("GLABS_API_KEY", "")
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def generate_glabs_voice(self, text: str, voice_name: str) -> Optional[bytes]:
        """Try to generate speech using G-Labs Voice Studio local server."""
        payload = {
            "text": text,
            "voice": voice_name,
            "speed": 1.0
        }
        
        async with aiohttp.ClientSession() as session:
            # We will try both the voice base URL and the main G-Labs API URL (as fallback/alternate ports)
            urls = [
                f"{self.base_url}/api/voice/generate",
                f"http://127.0.0.1:8765/api/voice/generate"
            ]
            for url in urls:
                try:
                    safe_print(f"[*] Voice: Attempting G-Labs Voice Studio at {url}...")
                    async with session.post(url, headers=self.headers, json=payload, timeout=15) as resp:
                        if resp.status == 200:
                            safe_print(f"[OK] Voice: Successfully generated voice via G-Labs Voice Studio.")
                            return await resp.read()
                        elif resp.status == 202:
                            # If async, get status or task
                            data = await resp.json()
                            task_id = data.get("task_id")
                            if task_id:
                                # Poll for voice completion
                                poll_url = f"{self.base_url}/api/status/{task_id}"
                                safe_print(f"[*] Voice: Queued voice task {task_id}, polling...")
                                for _ in range(15):
                                    await asyncio.sleep(2)
                                    async with session.get(poll_url, headers=self.headers, timeout=5) as p_resp:
                                        if p_resp.status == 200:
                                            p_data = await p_resp.json()
                                            if p_data.get("status") == "completed":
                                                results = p_data.get("results", [])
                                                if results:
                                                    async with session.get(results[0], timeout=30) as f_resp:
                                                        if f_resp.status == 200:
                                                            return await f_resp.read()
                                            elif p_data.get("status") == "failed":
                                                break
                except Exception as e:
                    safe_print(f"[!] Voice: G-Labs server request failed on {url}: {e}")
        return None

    async def generate_google_tts(self, text: str, lang: str = "en") -> Optional[bytes]:
        """Zero-dependency fallback using Google Translate's public TTS endpoint."""
        safe_print("[*] Voice: Attempting Google Translate TTS fallback...")
        if not text or not text.strip():
            safe_print("[!] Voice: Empty text provided to Google TTS.")
            return None

        # Split text into chunks by sentences/punctuation to keep under 150 chars without splitting words
        import re
        sentences = re.split(r'([.!?\n,])', text)
        chunks = []
        current_chunk = ""
        
        # Reconstruct sentences with punctuation
        i = 0
        while i < len(sentences):
            part = sentences[i]
            punct = sentences[i+1] if i+1 < len(sentences) else ""
            sentence = (part + punct).strip()
            i += 2
            
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) + 1 <= 150:
                current_chunk = (current_chunk + " " + sentence).strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If a single sentence is > 150 chars, split it by characters as fallback
                if len(sentence) > 150:
                    sub_chunks = [sentence[j:j+150] for j in range(0, len(sentence), 150)]
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1]
                else:
                    current_chunk = sentence
                    
        if current_chunk:
            chunks.append(current_chunk)

        audio_data = bytearray()
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            for idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Add delay between chunks (except first) to prevent Google Translate rate limits/bans
                if idx > 0:
                    await asyncio.sleep(0.5)
                    
                chunk_encoded = urllib.parse.quote(chunk)
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&q={chunk_encoded}"
                try:
                    async with session.get(url, headers=headers, timeout=15) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            audio_data.extend(data)
                        else:
                            safe_print(f"[!] Voice: Google TTS chunk failed with status {resp.status} for text: '{chunk}'")
                            return None
                except Exception as e:
                    safe_print(f"[!] Voice: Google TTS chunk error: {repr(e)}")
                    return None
        
        if len(audio_data) > 0:
            safe_print(f"[OK] Voice: Successfully generated voice via Google TTS ({len(chunks)} chunks).")
            return bytes(audio_data)
        return None

    async def generate_fish_speech(self, text: str) -> Optional[str]:
        """Fallback using fishaudio/fish-speech-1 via Gradio client (returns path)."""
        safe_print("[*] Voice: Attempting Fish Speech Gradio Client fallback...")
        try:
            from gradio_client import Client
            
            def _call_gradio():
                client = Client("fishaudio/fish-speech-1")
                result = client.predict(text=text, api_name="/infer")
                # Gradio return formats vary, but typically it returns a tuple or a path string
                return result[0] if isinstance(result, tuple) else result

            audio_path = await asyncio.to_thread(_call_gradio)
            if audio_path and os.path.exists(audio_path):
                safe_print(f"[OK] Voice: Successfully generated voice via Fish Speech: {audio_path}")
                return audio_path
        except Exception as e:
            safe_print(f"[!] Voice: Fish Speech Gradio Client failed: {e}")
        return None

    async def generate_gemini_tts(self, text: str, voice_name: str = "Puck") -> Optional[bytes]:
        """Generate speech using Google Gemini 3.1 Flash TTS API, converting the raw PCM to MP3."""
        safe_print(f"[*] Voice: Attempting Gemini 3.1 Flash TTS with voice '{voice_name}'...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            safe_print("[!] Voice: No GEMINI_API_KEY found in environment.")
            return None
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Read the following text transcript exactly as audio. Do not generate any text, markdown, or chat response. Repeat this transcript: {text}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name
                        }
                    }
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        import base64
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
                    if resp.status != 200:
                        safe_print(f"[!] Voice: Gemini TTS API returned status {resp.status}")
                        return None
                        
                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return None
                        
                    base64_audio = candidates[0]["content"]["parts"][0]["inlineData"]["data"]
                    audio_bytes = base64.b64decode(base64_audio)
                    
                    # Convert raw PCM (s16be, 24000Hz) to MP3 using local ffmpeg
                    if shutil.which("ffmpeg"):
                        # Save temp PCM
                        temp_pcm = os.path.join(os.getcwd(), "output", "temp_gemini_raw.wav")
                        os.makedirs(os.path.dirname(temp_pcm), exist_ok=True)
                        with open(temp_pcm, "wb") as f:
                            f.write(audio_bytes)
                            
                        # Convert to MP3
                        temp_mp3 = temp_pcm.replace("raw.wav", "converted.mp3")
                        cmd = [
                            "ffmpeg", "-f", "s16le", "-ar", "24000", "-ac", "1",
                            "-i", temp_pcm, temp_mp3, "-y"
                        ]
                        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        # Read converted MP3 bytes
                        if os.path.exists(temp_mp3):
                            with open(temp_mp3, "rb") as f:
                                converted_bytes = f.read()
                            try:
                                os.remove(temp_pcm)
                                os.remove(temp_mp3)
                            except: pass
                            safe_print(f"[OK] Voice: Successfully generated and converted Gemini TTS to MP3.")
                            return converted_bytes
                    else:
                        safe_print("[!] Voice: ffmpeg not found in PATH. Returning raw PCM bytes.")
                        return audio_bytes
            except Exception as e:
                safe_print(f"[!] Voice: Gemini TTS failed: {e}")
        return None

    async def generate_edge_tts(self, text: str, voice: str = "en-US-AriaNeural") -> Optional[bytes]:
        """Generate speech using Microsoft Edge TTS (free, high quality, no API key needed).
        
        Recommended voices:
        - Female: en-US-AriaNeural, en-US-JennyNeural, en-GB-SoniaNeural
        - Male: en-US-GuyNeural, en-US-AndrewNeural, en-GB-RyanNeural
        """
        safe_print(f"[*] Voice: Attempting Edge TTS with voice '{voice}'...")
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(text, voice)
            audio_chunks = bytearray()
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.extend(chunk["data"])
            
            if len(audio_chunks) > 0:
                safe_print(f"[OK] Voice: Successfully generated voice via Edge TTS ({len(audio_chunks)} bytes).")
                return bytes(audio_chunks)
            else:
                safe_print("[!] Voice: Edge TTS returned empty audio.")
                return None
                
        except ImportError:
            safe_print("[!] Voice: edge-tts package not installed. Run: pip install edge-tts")
            return None
        except Exception as e:
            safe_print(f"[!] Voice: Edge TTS failed: {e}")
            return None

    async def generate_audio(self, text: str, voice_name: str = "default", output_path: str = None) -> Optional[str]:
        """Generate audio track using best available engine, saving it to output_path.
        
        Fallback order:
        1. Explicit Gemini TTS (if requested by voice_name)
        2. G-Labs Voice Studio (custom voices, local server)
        3. Edge TTS (Microsoft neural voices, free, high quality)
        4. Google Translate TTS (robotic, last resort)
        5. Fish Speech (Gradio, slow)
        """
        if not output_path:
            output_path = os.path.join(os.getcwd(), "output", "temp_tts.mp3")
        
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # 0. Check if Gemini TTS is explicitly requested
        if voice_name and any(v in voice_name.lower() for v in ("gemini", "puck", "charon", "kore", "aoede", "fenrir")):
            g_voice = "Puck"
            for v in ["Puck", "Charon", "Kore", "Aoede", "Fenrir"]:
                if v.lower() in voice_name.lower():
                    g_voice = v
                    break
            audio_bytes = await self.generate_gemini_tts(text, g_voice)
            if audio_bytes:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                return output_path
                
        # 1. Try G-Labs Voice Studio
        audio_bytes = await self.generate_glabs_voice(text, voice_name)
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return output_path
        
        # 2. Try Edge TTS (Microsoft neural voices — free, high quality)
        edge_voice = "en-US-AriaNeural"  # Default: natural female voice
        if voice_name:
            vn_low = voice_name.lower()
            if "jenny" in vn_low:
                edge_voice = "en-US-JennyNeural"
            elif "aria" in vn_low:
                edge_voice = "en-US-AriaNeural"
            elif "sonia" in vn_low:
                edge_voice = "en-GB-SoniaNeural"
            elif "guy" in vn_low:
                edge_voice = "en-US-GuyNeural"
            elif "andrew" in vn_low:
                edge_voice = "en-US-AndrewNeural"
            elif "ryan" in vn_low:
                edge_voice = "en-GB-RyanNeural"
            elif any(m in vn_low for m in ("male", "guy", "man", "deep")):
                edge_voice = "en-US-GuyNeural"
            elif any(m in vn_low for m in ("british", "uk", "london")):
                edge_voice = "en-GB-SoniaNeural"
        
        audio_bytes = await self.generate_edge_tts(text, edge_voice)
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return output_path
            
        # 3. Try Google Translate TTS
        audio_bytes = await self.generate_google_tts(text)
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return output_path
            
        # 4. Try Gradio Fish Speech
        temp_fish_path = await self.generate_fish_speech(text)
        if temp_fish_path and os.path.exists(temp_fish_path):
            shutil.copy(temp_fish_path, output_path)
            return output_path
            
        safe_print("[!] Voice: All voice generation options failed.")
        return None

    def get_duration(self, file_path: str) -> float:
        """Get the duration of a media file using ffprobe."""
        import json
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", file_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get("format", {}).get("duration", 0.0))
        except Exception:
            pass
        return 0.0

    def combine_video_audio(self, video_path: str, audio_path: str, output_path: str = None) -> Optional[str]:
        """Mux video and audio streams using local ffmpeg command."""
        if not output_path:
            output_path = video_path.replace(".mp4", "_ugc.mp4")
            
        if not os.path.exists(video_path):
            safe_print(f"[!] Voice: Input video path does not exist: {video_path}")
            return None
        if not os.path.exists(audio_path):
            safe_print(f"[!] Voice: Input audio path does not exist: {audio_path}")
            return None
            
        if not shutil.which("ffmpeg"):
            safe_print("[!] Voice: ffmpeg executable was not found in System PATH. Audio muxing skipped.")
            return None
            
        # Detect durations to decide if we need to loop or preserve video duration
        vid_dur = self.get_duration(video_path)
        aud_dur = self.get_duration(audio_path)
        
        safe_print(f"[*] Voice: Video duration: {vid_dur:.2f}s, Audio duration: {aud_dur:.2f}s")
        
        if aud_dur > vid_dur and vid_dur > 0:
            # Audio is longer than video, loop the video to match audio length
            safe_print(f"[*] Voice: Audio is longer than video. Looping video to match audio duration...")
            cmd = [
                "ffmpeg", "-stream_loop", "-1", "-i", video_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", output_path, "-y"
            ]
        else:
            # Video is longer than or equal to audio. Play video fully and let audio go silent at the end.
            safe_print(f"[*] Voice: Video is longer than or equal to audio. Preserving full video duration...")
            cmd = [
                "ffmpeg", "-i", video_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                output_path, "-y"
            ]
            
        try:
            safe_print(f"[*] Voice: Muxing audio and video with ffmpeg...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            safe_print(f"[OK] Voice: Successfully muxed video and audio -> {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            safe_print(f"[!] Voice: ffmpeg failed with error: {e.stderr}")
        except Exception as e:
            safe_print(f"[!] Voice: Error executing ffmpeg: {e}")
        return None

def test_tts():
    gen = VoiceGenerator()
    loop = asyncio.get_event_loop()
    audio_path = loop.run_until_complete(gen.generate_audio("Obscura luxury streetwear lookbook campaign"))
    print(f"Generated Audio Path: {audio_path}")

if __name__ == "__main__":
    test_tts()
