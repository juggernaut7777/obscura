import os
import json
import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

# Load .env automatically
load_dotenv()

app = FastAPI()

# Configuration - Look for either key name
NVIDIA_API_KEY = os.getenv("NVAPI_KEY") or os.getenv("NVIDIA_API_KEY") or ""
# Llama 3.3 70B is very fast and reliable for testing
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

@app.post("/v1/messages")
async def proxy_anthropic_to_nvidia(request: Request):
    # 1. Capture the Anthropic request from Claude Code
    anthropic_data = await request.json()
    print(f"\n[PROXY] Incoming Request: {json.dumps(anthropic_data.get('messages', []), indent=2)}")
    
    # 2. Extract messages and system prompt
    messages = anthropic_data.get("messages", [])
    system_prompt = anthropic_data.get("system", "")
    
    # 3. Build the OpenAI-style payload for NVIDIA NIM
    openai_messages = []
    if system_prompt:
        openai_messages.append({"role": "system", "content": system_prompt})
    
    for msg in messages:
        # Convert Anthropic roles/content to OpenAI format
        role = msg.get("role")
        content = msg.get("content")
        
        # Handle complex content (like tool use/images) if necessary
        # For now, simple text support for basic coding
        openai_messages.append({"role": role, "content": str(content)})

    nvidia_payload = {
        "model": NVIDIA_MODEL,
        "messages": openai_messages,
        "max_tokens": anthropic_data.get("max_tokens", 4096),
        "stream": anthropic_data.get("stream", False),
        "temperature": anthropic_data.get("temperature", 0.7),
    }

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    # 4. Forward to NVIDIA and return the response
    async def stream_nvidia():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", NVIDIA_BASE_URL, headers=headers, json=nvidia_payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        # In a full production version, we would translate 
                        # the OpenAI JSON chunks back into Anthropic JSON chunks here.
                        # For now, we're building the foundation.
                        yield line + "\n"

    if nvidia_payload["stream"]:
        return StreamingResponse(stream_nvidia(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(NVIDIA_BASE_URL, headers=headers, json=nvidia_payload)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"[PROXY] Claude -> NVIDIA Proxy starting on http://localhost:8083")
    print(f"[PROXY] Using Model: {NVIDIA_MODEL}")
    print(f"[PROXY] API Key: {NVIDIA_API_KEY[:12]}...") 
    uvicorn.run(app, host="0.0.0.0", port=8083)
