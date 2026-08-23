import ollama
import os
import json
import re
import asyncio
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

def extract_json_from_llm(response_text: str) -> dict:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    cleaned_text = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', response_text, flags=re.DOTALL)
    match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Failed to parse valid JSON from LLM. Raw output: {response_text}")

class LLMService:
    def __init__(self):
        self.client = ollama.AsyncClient(host=OLLAMA_BASE_URL)
        self.model = OLLAMA_MODEL
    
    async def generate_response(self, prompt: str) -> str:
        """Single response — used for schema analysis and SQL translation"""
        print(f"\n--- SENDING PROMPT TO LLM ---\n{prompt[:200]}...\n----------------------------\n")
        
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": 0.1,  
                        "num_predict": 2048,
                    }
                ),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            raise TimeoutError("LLM analysis request timed out after 120s")

        content = response.message.content
        print("\n--- RAW LLM RESPONSE OBJECT ---")
        print(content)
        print("--- END RAW RESPONSE ---\n")
        
        try:
            parsed_json = extract_json_from_llm(content)
            return json.dumps(parsed_json)
        except ValueError:
            return content
    
    async def generate_chat_response(self, messages: list[dict]) -> str:
        """Multi-turn chat — used by Flux AI assistant"""
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.7}
                ),
                timeout=60.0
            )
            return response.message.content
        except asyncio.TimeoutError:
            raise TimeoutError("LLM chat request timed out after 60s")
    
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Streaming — used by Flux assistant SSE endpoint.
        
        The Ollama AsyncClient.chat(stream=True) returns an async generator of
        ChatResponse pydantic objects. Each chunk has a .message.content attribute
        containing the incremental text.
        """
        first_logged = False
        async for chunk in await self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={"temperature": 0.7}
        ):
            # Prefer attribute access (ChatResponse pydantic obj); dict fallback for safety
            if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                content = chunk.message.content
            elif isinstance(chunk, dict):
                content = chunk.get('message', {}).get('content', '')
            else:
                content = ''

            if not content:
                continue

            # Log the first 100 chars of each response to confirm Ollama is generating
            if not first_logged:
                logger.info(f"[Flux stream] first chunk from Ollama ({self.model}): {repr(content[:100])}")
                first_logged = True

            yield content
