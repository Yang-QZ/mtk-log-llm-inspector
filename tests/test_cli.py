"""Integration test for CLI with mocked API."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from src.cli import analyze_command


def create_mock_response(state="PLAYING", confidence=0.9):
    """Create a mock API response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "final_state": state,
                        "confidence": confidence,
                        "reason": f"Test {state} state",
                        "evidence": ["Evidence line 1", "Evidence line 2"],
                        "next_actions": ["Monitor status"]
                    })
                }
            }
        ]
    }
    return mock_response


@patch('src.bailian_client.requests.post')
def test_cli_full_workflow(mock_post):
    """Test complete CLI workflow with mocked API."""
    # Mock API responses
    mock_post.return_value = create_mock_response()
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    log_file = Path(temp_dir) / "test.log"
    out_dir = Path(temp_dir) / "output"
    
    try:
        # Create a test log file
        log_content = """
01-06 10:15:23.456  1234  1235 I AudioFlinger: Track started
01-06 10:15:23.457  1234  1235 D AudioTrack: Buffer obtained
01-06 10:15:23.458  1234  1235 I AudioPolicyService: Output active
        """.strip()
        
        log_file.write_text(log_content)
        
        # Create mock args
        class Args:
            log = str(log_file)
            out = str(out_dir)
            chunk_size = 10
            overlap = 2
            model = "qwen-plus"
            debug = False
            mask = False
        
        # Set API key for test
        with patch.dict('os.environ', {'BAILIAN_API_KEY': 'test-key'}):
            result = analyze_command(Args())
        
        # Check that command succeeded
        assert result == 0
        
        # Verify output files exist
        assert (out_dir / "report.json").exists()
        assert (out_dir / "report.md").exists()
        
        # Verify JSON report structure
        with open(out_dir / "report.json") as f:
            report = json.load(f)
        
        assert "metadata" in report
        assert "summary" in report
        assert "window_results" in report
        assert "merged_segments" in report
        
        # Verify Markdown report
        md_content = (out_dir / "report.md").read_text()
        assert "# Audio State Analysis Report" in md_content
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


@patch('src.bailian_client.requests.post')
def test_cli_with_debug_mode(mock_post):
    """Test CLI with debug mode enabled."""
    mock_post.return_value = create_mock_response()
    
    temp_dir = tempfile.mkdtemp()
    log_file = Path(temp_dir) / "test.log"
    out_dir = Path(temp_dir) / "output"
    
    try:
        log_file.write_text("01-06 10:15:23.456  1234  1235 I AudioFlinger: Test")
        
        class Args:
            log = str(log_file)
            out = str(out_dir)
            chunk_size = 10
            overlap = 2
            model = "qwen-plus"
            debug = True
            mask = False
        
        with patch.dict('os.environ', {'BAILIAN_API_KEY': 'test-key'}):
            result = analyze_command(Args())
        
        assert result == 0
        
        # Verify debug files exist
        debug_dir = out_dir / "debug"
        assert debug_dir.exists()
        
        # Should have request and response files
        debug_files = list(debug_dir.glob("*.json"))
        assert len(debug_files) >= 2  # At least one request and one response
        
    finally:
        shutil.rmtree(temp_dir)


@patch('src.bailian_client.requests.post')
def test_cli_with_masking(mock_post):
    """Test CLI with data masking enabled."""
    mock_post.return_value = create_mock_response()
    
    temp_dir = tempfile.mkdtemp()
    log_file = Path(temp_dir) / "test.log"
    out_dir = Path(temp_dir) / "output"
    
    try:
        # Log with sensitive data
        log_file.write_text(
            "01-06 10:15:23.456  1234  1235 I AudioFlinger: user@example.com connected from 192.168.1.1"
        )
        
        class Args:
            log = str(log_file)
            out = str(out_dir)
            chunk_size = 10
            overlap = 2
            model = "qwen-plus"
            debug = False
            mask = True
        
        with patch.dict('os.environ', {'BAILIAN_API_KEY': 'test-key'}):
            result = analyze_command(Args())
        
        assert result == 0
        
        # Verify the API was called with masked data
        # Get the first call's payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        # Check that sensitive data was masked in the messages
        messages = payload['messages']
        user_message = messages[1]['content']
        
        assert "[EMAIL]" in user_message or "user@example.com" not in user_message
        assert "[IPv4]" in user_message or "192.168.1.1" not in user_message
        
    finally:
        shutil.rmtree(temp_dir)


def test_cli_missing_log_file():
    """Test CLI with missing log file."""
    class Args:
        log = "/nonexistent/file.log"
        out = "/tmp/output"
        chunk_size = 200
        overlap = 50
        model = "qwen-plus"
        debug = False
        mask = False
    
    result = analyze_command(Args())
    assert result == 1  # Should return error code


def test_cli_without_api_key():
    """Test CLI without API key set."""
    temp_dir = tempfile.mkdtemp()
    log_file = Path(temp_dir) / "test.log"
    
    try:
        log_file.write_text("01-06 10:15:23.456  1234  1235 I AudioFlinger: Test")
        
        class Args:
            log = str(log_file)
            out = str(Path(temp_dir) / "output")
            chunk_size = 10
            overlap = 2
            model = "qwen-plus"
            debug = False
            mask = False
        
        # Ensure BAILIAN_API_KEY is not set
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_command(Args())
        
        assert result == 1  # Should return error code
        
    finally:
        shutil.rmtree(temp_dir)
