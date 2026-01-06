"""Tests for chunker module."""

import pytest
from src.chunker import LogChunker


def test_chunker_initialization():
    """Test chunker initialization."""
    chunker = LogChunker(chunk_size=100, overlap=20)
    assert chunker.chunk_size == 100
    assert chunker.overlap == 20


def test_chunker_invalid_params():
    """Test that invalid parameters raise errors."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        LogChunker(chunk_size=0)
    
    with pytest.raises(ValueError, match="overlap must be non-negative"):
        LogChunker(chunk_size=100, overlap=-1)
    
    with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
        LogChunker(chunk_size=100, overlap=100)


def test_chunk_lines_basic():
    """Test basic chunking without overlap."""
    chunker = LogChunker(chunk_size=3, overlap=0)
    lines = ["L1", "L2", "L3", "L4", "L5"]
    
    windows = chunker.chunk_lines(lines)
    
    # Should have 2 windows: [L1,L2,L3] and [L4,L5]
    assert len(windows) == 2
    assert windows[0] == (0, ["L1", "L2", "L3"])
    assert windows[1] == (1, ["L4", "L5"])


def test_chunk_lines_with_overlap():
    """Test chunking with overlap."""
    chunker = LogChunker(chunk_size=4, overlap=2)
    lines = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    
    windows = chunker.chunk_lines(lines)
    
    # Window 0: L1,L2,L3,L4 (indices 0-3)
    # Window 1: L3,L4,L5,L6 (indices 2-5, starts at 0+4-2=2)
    # Window 2: L5,L6,L7    (indices 4-6, starts at 2+4-2=4)
    assert len(windows) == 3
    assert windows[0] == (0, ["L1", "L2", "L3", "L4"])
    assert windows[1] == (1, ["L3", "L4", "L5", "L6"])
    assert windows[2] == (2, ["L5", "L6", "L7"])


def test_chunk_lines_exact_fit():
    """Test chunking when lines fit exactly."""
    chunker = LogChunker(chunk_size=3, overlap=0)
    lines = ["L1", "L2", "L3", "L4", "L5", "L6"]
    
    windows = chunker.chunk_lines(lines)
    
    assert len(windows) == 2
    assert windows[0] == (0, ["L1", "L2", "L3"])
    assert windows[1] == (1, ["L4", "L5", "L6"])


def test_chunk_lines_empty():
    """Test chunking empty list."""
    chunker = LogChunker(chunk_size=10, overlap=2)
    lines = []
    
    windows = chunker.chunk_lines(lines)
    
    assert len(windows) == 0


def test_chunk_lines_single_line():
    """Test chunking a single line."""
    chunker = LogChunker(chunk_size=10, overlap=2)
    lines = ["L1"]
    
    windows = chunker.chunk_lines(lines)
    
    assert len(windows) == 1
    assert windows[0] == (0, ["L1"])


def test_chunk_lines_smaller_than_chunk_size():
    """Test chunking when total lines < chunk_size."""
    chunker = LogChunker(chunk_size=10, overlap=2)
    lines = ["L1", "L2", "L3"]
    
    windows = chunker.chunk_lines(lines)
    
    assert len(windows) == 1
    assert windows[0] == (0, ["L1", "L2", "L3"])


def test_chunk_default_values():
    """Test default chunk_size and overlap values."""
    chunker = LogChunker()  # Uses defaults: chunk_size=200, overlap=50
    assert chunker.chunk_size == 200
    assert chunker.overlap == 50


def test_chunk_large_overlap():
    """Test chunking with large overlap."""
    chunker = LogChunker(chunk_size=5, overlap=4)
    lines = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    
    windows = chunker.chunk_lines(lines)
    
    # Each window advances by chunk_size - overlap = 5 - 4 = 1
    # Window 0: L1-L5 (0-4)
    # Window 1: L2-L6 (1-5)
    # Window 2: L3-L7 (2-6)
    assert len(windows) == 3
    assert windows[0][1] == ["L1", "L2", "L3", "L4", "L5"]
    assert windows[1][1] == ["L2", "L3", "L4", "L5", "L6"]
    assert windows[2][1] == ["L3", "L4", "L5", "L6", "L7"]
