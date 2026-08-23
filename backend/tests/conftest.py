import pytest
from unittest.mock import AsyncMock, patch, Mock

@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        
        mock_response.json.return_value = {
            "model": "llama3",
            "created_at": "2023-10-01T12:00:00Z",
            "message": {
                "role": "assistant",
                "content": "{\"status\": \"success\"}"
            },
            "done": True
        }
        
        mock_post.return_value = mock_response
        yield mock_post
