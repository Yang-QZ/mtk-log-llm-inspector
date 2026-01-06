"""Tests for bailian_client module."""

import pytest
import json
import os
from unittest.mock import Mock, patch
from src.bailian_client import BailianClient


def test_client_initialization_with_api_key():
    """Test client initialization with explicit API key."""
    client = BailianClient(api_key="test-key-123")
    assert client.api_key == "test-key-123"
    assert client.model == "qwen-plus"  # Default model


def test_client_initialization_from_env():
    """Test client initialization from environment variables."""
    with patch.dict(os.environ, {
        "BAILIAN_API_KEY": "env-key-456",
        "BAILIAN_MODEL": "qwen-turbo"
    }):
        client = BailianClient()
        assert client.api_key == "env-key-456"
        assert client.model == "qwen-turbo"


def test_client_initialization_no_api_key():
    """Test that initialization fails without API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="BAILIAN_API_KEY must be set"):
            BailianClient()


def test_client_custom_base_url():
    """Test client with custom base URL."""
    client = BailianClient(
        api_key="test-key",
        base_url="https://custom.api.com"
    )
    assert client.base_url == "https://custom.api.com"


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_success(mock_post):
    """Test successful log window analysis."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "final_state": "PLAYING",
                        "confidence": 0.9,
                        "reason": "Track is active",
                        "evidence": ["Line 1", "Line 2"],
                        "next_actions": ["Monitor"]
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    result = client.analyze_log_window(
        system_prompt="System prompt",
        log_content="Log content"
    )
    
    assert result["final_state"] == "PLAYING"
    assert result["confidence"] == 0.9
    assert result["reason"] == "Track is active"
    assert len(result["evidence"]) == 2
    assert len(result["next_actions"]) == 1


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_invalid_state(mock_post):
    """Test that invalid state raises error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "final_state": "INVALID_STATE",
                        "confidence": 0.9,
                        "reason": "Reason",
                        "evidence": [],
                        "next_actions": []
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="Invalid final_state"):
        client.analyze_log_window("System prompt", "Log content")


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_missing_field(mock_post):
    """Test that missing required field raises error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "final_state": "PLAYING",
                        "confidence": 0.9,
                        # Missing "reason", "evidence", "next_actions"
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="Missing required field"):
        client.analyze_log_window("System prompt", "Log content")


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_invalid_json(mock_post):
    """Test that invalid JSON raises error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Not a valid JSON"
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="not valid JSON"):
        client.analyze_log_window("System prompt", "Log content")


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_invalid_confidence(mock_post):
    """Test that invalid confidence raises error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "final_state": "PLAYING",
                        "confidence": 1.5,  # Invalid: > 1.0
                        "reason": "Reason",
                        "evidence": [],
                        "next_actions": []
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="Invalid confidence"):
        client.analyze_log_window("System prompt", "Log content")


@patch('src.bailian_client.requests.post')
def test_analyze_log_window_no_choices(mock_post):
    """Test that response without choices raises error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": []
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="No choices in API response"):
        client.analyze_log_window("System prompt", "Log content")


@patch('src.bailian_client.requests.post')
def test_get_raw_response(mock_post):
    """Test getting raw API response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "response-123",
        "choices": [{"message": {"content": "test"}}]
    }
    mock_post.return_value = mock_response
    
    client = BailianClient(api_key="test-key")
    result = client.get_raw_response("System prompt", "Log content")
    
    assert result["id"] == "response-123"
    assert "choices" in result


def test_default_base_url():
    """Test default base URL."""
    client = BailianClient(api_key="test-key")
    assert "dashscope.aliyuncs.com" in client.base_url
