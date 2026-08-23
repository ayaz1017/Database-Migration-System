import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, Mock

from backend.services.llm_service import extract_json_from_llm, LLMService

def test_extract_json_perfect():
    raw = '{"key": "value"}'
    assert extract_json_from_llm(raw) == {"key": "value"}

def test_extract_json_markdown():
    raw = "```json\n{\"key\": \"value\"}\n```"
    assert extract_json_from_llm(raw) == {"key": "value"}
    
    raw2 = "```\n{\"key\": \"value\"}\n```"
    assert extract_json_from_llm(raw2) == {"key": "value"}

def test_extract_json_padding():
    raw = "Here is your output:\n{\"key\": \"value\"}\nHope that helps!"
    assert extract_json_from_llm(raw) == {"key": "value"}

def test_extract_json_failure():
    raw = "I'm sorry, I cannot do that."
    with pytest.raises(ValueError, match="Failed to parse valid JSON from LLM"):
        extract_json_from_llm(raw)

@pytest.mark.asyncio
async def test_generate_response(mock_httpx_post):
    service = LLMService()
    
    response_json = await service.generate_response("test prompt")
    assert json.loads(response_json) == {"status": "success"}
    
    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    assert "api/chat" in args[0]
    assert kwargs["json"]["messages"][0]["content"] == "test prompt"
    assert kwargs["json"]["format"] == "json"

@pytest.mark.asyncio
async def test_retry_on_timeout():
    service = LLMService()
    service.max_retries = 2
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "message": {"content": "{\"retry\": \"success\"}"}
        }
        
        mock_post.side_effect = [
            httpx.ReadTimeout("Timeout 1"),
            httpx.ReadTimeout("Timeout 2"),
            mock_response
        ]
        
        with patch("asyncio.sleep", new_callable=AsyncMock):
            response_json = await service.generate_response("retry test")
        
        assert json.loads(response_json) == {"retry": "success"}
        assert mock_post.call_count == 3
