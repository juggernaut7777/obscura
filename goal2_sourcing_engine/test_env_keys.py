import os
import sys
import asyncio
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_nvidia():
    key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVAPI_KEY")
    if not key:
        return "MISSING"
    try:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta/llama-3.2-11b-vision-instruct",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return "WORKING"
            else:
                # Try another model name
                payload["model"] = "meta/llama3-8b-instruct"
                resp2 = await client.post(url, headers=headers, json=payload)
                if resp2.status_code == 200:
                    return f"WORKING (fallback model: {resp2.json().get('model')})"
                return f"FAILED ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"ERROR: {e}"

async def test_groq():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return "MISSING"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return "WORKING"
            else:
                return f"FAILED ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"ERROR: {e}"

async def test_gemini():
    results = []
    for i in range(1, 8):
        key_name = "GEMINI_API_KEY" if i == 1 else f"GEMINI_API_KEY_{i}"
        key = os.environ.get(key_name)
        if not key:
            results.append(f"{key_name}: MISSING")
            continue
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": "hello"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    results.append(f"{key_name}: WORKING")
                else:
                    results.append(f"{key_name}: FAILED ({resp.status_code})")
        except Exception as e:
            results.append(f"{key_name}: ERROR: {e}")
    return "\n".join(results)

async def test_xai():
    key = os.environ.get("XAI_API_KEY")
    if not key:
        return "MISSING"
    try:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return "WORKING"
            else:
                return f"FAILED ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"ERROR: {e}"

async def main():
    print("Testing NVIDIA NIM...")
    nv_res = await test_nvidia()
    print(f"NVIDIA API Key: {nv_res}")
    
    print("\nTesting Groq...")
    groq_res = await test_groq()
    print(f"Groq API Key: {groq_res}")
    
    print("\nTesting xAI...")
    xai_res = await test_xai()
    print(f"xAI API Key: {xai_res}")
    
    print("\nTesting Gemini Pooled Keys...")
    gemini_res = await test_gemini()
    print(gemini_res)

if __name__ == "__main__":
    asyncio.run(main())
