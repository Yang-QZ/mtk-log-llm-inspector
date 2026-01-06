"""Log chunking utilities for splitting logs into overlapping windows."""

from typing import List, Tuple


class LogChunker:
    """Splits log lines into overlapping windows."""

    def __init__(self, chunk_size: int = 200, overlap: int = 50):
        """Initialize the chunker.
        
        Args:
            chunk_size: Number of lines per chunk
            overlap: Number of lines to overlap between consecutive chunks
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_lines(self, lines: List[str]) -> List[Tuple[int, List[str]]]:
        """Split lines into overlapping windows.
        
        Args:
            lines: List of log lines to chunk
            
        Returns:
            List of tuples (window_index, window_lines) where window_index is 0-based
        """
        if not lines:
            return []
        
        windows = []
        window_idx = 0
        start = 0
        
        while start < len(lines):
            end = min(start + self.chunk_size, len(lines))
            window = lines[start:end]
            windows.append((window_idx, window))
            
            # Move to next window
            window_idx += 1
            start += self.chunk_size - self.overlap
            
            # If we've covered all lines, break
            if end == len(lines):
                break
        
        return windows
