"""Tests for log_parser module."""

import pytest
from src.log_parser import LogParser, DEFAULT_AUDIO_TAGS
import tempfile
import os


def test_default_audio_tags():
    """Test that default audio tags are defined."""
    assert len(DEFAULT_AUDIO_TAGS) > 0
    assert "AudioFlinger" in DEFAULT_AUDIO_TAGS
    assert "AudioTrack" in DEFAULT_AUDIO_TAGS


def test_parser_initialization():
    """Test parser initialization with custom tags."""
    custom_tags = ["AudioFlinger", "MediaPlayer"]
    parser = LogParser(audio_tags=custom_tags)
    assert parser.audio_tags == custom_tags
    
    # Test default tags
    parser_default = LogParser()
    assert parser_default.audio_tags == DEFAULT_AUDIO_TAGS


def test_parse_file():
    """Test parsing a log file."""
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write("Line 1\n")
        f.write("Line 2\n")
        f.write("  \n")  # Empty line with whitespace
        f.write("Line 3\n")
        temp_path = f.name
    
    try:
        parser = LogParser()
        lines = parser.parse_file(temp_path)
        
        # Should skip empty lines and strip trailing whitespace
        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"
        assert lines[2] == "Line 3"
    finally:
        os.unlink(temp_path)


def test_filter_audio_lines():
    """Test filtering for audio-related lines."""
    parser = LogParser(audio_tags=["AudioFlinger", "AudioTrack"])
    
    lines = [
        "01-06 10:15:23.456  1234  1235 I AudioFlinger: Track started",
        "01-06 10:15:23.457  1234  1235 D SystemUI: UI updated",
        "01-06 10:15:23.458  1234  1235 D AudioTrack: Buffer obtained",
        "01-06 10:15:23.459  1234  1235 I ActivityManager: Activity started",
    ]
    
    filtered = parser.filter_audio_lines(lines)
    
    assert len(filtered) == 2
    assert "AudioFlinger" in filtered[0]
    assert "AudioTrack" in filtered[1]


def test_filter_case_insensitive():
    """Test that filtering is case-insensitive."""
    parser = LogParser(audio_tags=["AudioFlinger"])
    
    lines = [
        "Line with AUDIOFLINGER in caps",
        "Line with audioflinger in lowercase",
        "Line with AudioFlinger in mixed case",
        "Line with no match",
    ]
    
    filtered = parser.filter_audio_lines(lines)
    
    assert len(filtered) == 3


def test_filter_no_tags():
    """Test that filtering with no tags returns all lines."""
    parser = LogParser(audio_tags=[])
    
    lines = ["Line 1", "Line 2", "Line 3"]
    filtered = parser.filter_audio_lines(lines)
    
    assert len(filtered) == 3
    assert filtered == lines


def test_parse_and_filter():
    """Test combined parse and filter operation."""
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write("01-06 10:15:23.456  1234  1235 I AudioFlinger: Track started\n")
        f.write("01-06 10:15:23.457  1234  1235 D SystemUI: UI updated\n")
        f.write("01-06 10:15:23.458  1234  1235 D AudioTrack: Buffer obtained\n")
        temp_path = f.name
    
    try:
        parser = LogParser(audio_tags=["AudioFlinger", "AudioTrack"])
        lines = parser.parse_and_filter(temp_path)
        
        assert len(lines) == 2
        assert "AudioFlinger" in lines[0]
        assert "AudioTrack" in lines[1]
    finally:
        os.unlink(temp_path)


def test_word_boundary_matching():
    """Test that tag matching uses word boundaries."""
    parser = LogParser(audio_tags=["Audio"])
    
    lines = [
        "This has Audio as a word",
        "This has Audiofile which shouldn't match fully",
        "This has myAudio which shouldn't match fully",
    ]
    
    filtered = parser.filter_audio_lines(lines)
    
    # Only the first line should match (word boundary)
    assert len(filtered) == 1
    assert filtered[0] == lines[0]
