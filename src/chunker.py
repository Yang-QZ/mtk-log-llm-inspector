"""Log chunking utilities for splitting logs into overlapping windows.
日志分块工具 - 将日志分割成重叠的滑动窗口。
"""

from typing import List, Tuple


class LogChunker:
    """Splits log lines into overlapping windows.
    日志分块器 - 将日志行分割成重叠的窗口。
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 50):
        """Initialize the chunker.
        初始化分块器。
        
        Args:
            chunk_size: Number of lines per chunk (每个块的行数)
            overlap: Number of lines to overlap between consecutive chunks (连续块之间的重叠行数)
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
        将日志行分割成重叠的滑动窗口。
        
        Args:
            lines: List of log lines to chunk (要分块的日志行列表)
            
        Returns:
            List of tuples (window_index, window_lines) where window_index is 0-based
            元组列表 (窗口索引, 窗口日志行)，窗口索引从0开始
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
            
            # Move to next window (移动到下一个窗口)
            window_idx += 1
            start += self.chunk_size - self.overlap
            
            # If we've covered all lines, break (如果已覆盖所有行，则退出)
            if end == len(lines):
                break
        
        return windows
