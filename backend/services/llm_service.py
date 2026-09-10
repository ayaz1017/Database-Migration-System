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

# If OPENAI_API_KEY is present, we use OpenAI. Otherwise, fallback to local Ollama.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize OpenAI client lazily if needed
_openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        logger.warning("openai package not installed but OPENAI_API_KEY is set. Falling back to Ollama.")
        OPENAI_API_KEY = None

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
        self.use_openai = bool(OPENAI_API_KEY and _openai_client)
        if self.use_openai:
            self.openai_client = _openai_client
            self.model = OPENAI_MODEL
        else:
            self.ollama_client = ollama.AsyncClient(host=OLLAMA_BASE_URL)
            self.model = OLLAMA_MODEL
    
    async def generate_response(self, prompt: str) -> str:
        """Single response — used for schema analysis and SQL translation"""
        print(f"\n--- SENDING PROMPT TO LLM ({'OpenAI' if self.use_openai else 'Ollama'}) ---\n{prompt[:200]}...\n----------------------------\n")
        
        try:
            if self.use_openai:
                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=2048,
                    ),
                    timeout=120.0
                )
                content = response.choices[0].message.content
            else:
                response = await asyncio.wait_for(
                    self.ollama_client.chat(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0.1, "num_predict": 2048}
                    ),
                    timeout=120.0
                )
                content = response.message.content

        except asyncio.TimeoutError:
            raise TimeoutError("LLM analysis request timed out after 120s")

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
            if self.use_openai:
                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7
                    ),
                    timeout=60.0
                )
                return response.choices[0].message.content
            else:
                response = await asyncio.wait_for(
                    self.ollama_client.chat(
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
        """Streaming — used by Flux assistant SSE endpoint."""
        first_logged = False

        if self.use_openai:
            stream = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if not content:
                    continue
                if not first_logged:
                    logger.info(f"[Flux stream] first chunk from OpenAI ({self.model}): {repr(content[:100])}")
                    first_logged = True
                yield content

        else:
            async for chunk in await self.ollama_client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": 0.7}
            ):
                if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                    content = chunk.message.content
                elif isinstance(chunk, dict):
                    content = chunk.get('message', {}).get('content', '')
                else:
                    content = ''

                if not content:
                    continue

                if not first_logged:
                    logger.info(f"[Flux stream] first chunk from Ollama ({self.model}): {repr(content[:100])}")
                    first_logged = True

                yield content
