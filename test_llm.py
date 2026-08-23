import asyncio
import os
import sys

# Set env vars to ensure we test what we just changed
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["OLLAMA_MODEL"] = "llama3.1:8b"

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test():
    from backend.main import health_llm
    
    print("Testing /api/health/llm...")
    res = await health_llm()
    print("Health result:", res)
    
    if not res.get("llm_available"):
        print("LLM is not available! Skipping assistant test.")
        return
        
    print("\nTesting AssistantChat...")
    from backend.services.assistant_service import AssistantService
    service = AssistantService()
    
    # Empty DB file to prevent issues if migrations.db isn't setup for test script
    # This just needs to yield a response
    
    async for chunk in service.get_chat_response("How many migrations have I run?"):
        print(chunk, end="")
        
    print("\n\nDone testing.")

if __name__ == "__main__":
    asyncio.run(test())
