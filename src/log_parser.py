"""Log parsing and filtering utilities.
日志解析和过滤工具。
"""

import re
from typing import List, Optional


# Default audio-related tags commonly found in Android logcat
# Android日志中常见的音频相关标签
DEFAULT_AUDIO_TAGS = [
    "AudioFlinger",
    "AudioTrack",
    "AudioPolicyService",
    "AudioSystem",
    "AudioManager",
    "MediaPlayer",
    "AudioService",
    "audio_hw",
    "AudioEffect",
    "AudioMixer",
    "AudioRecord",
    "PlaybackThread",
    "RecordThread",
    "audio",
]


class LogParser:
    """Parser for Android logcat files.
    Android日志文件解析器。
    """

    def __init__(self, audio_tags: Optional[List[str]] = None):
        """Initialize the log parser.
        初始化日志解析器。
        
        Args:
            audio_tags: List of audio-related tags to filter for. If None, uses default list.
                       音频相关标签列表，用于过滤。如果为None，则使用默认列表。
        """
        self.audio_tags = audio_tags if audio_tags is not None else DEFAULT_AUDIO_TAGS

    def parse_file(self, file_path: str) -> List[str]:
        """Parse a logcat file and return all lines.
        解析日志文件并返回所有行。
        
        Args:
            file_path: Path to the log file (日志文件路径)
            
        Returns:
            List of log lines (stripped of trailing whitespace)
            日志行列表（去除尾部空白字符）
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.rstrip() for line in f if line.strip()]
        return lines

    def filter_audio_lines(self, lines: List[str]) -> List[str]:
        """Filter lines to only include audio-related content.
        过滤日志行，只保留音频相关的内容。
        
        This looks for lines containing any of the configured audio tags.
        It's case-insensitive and matches whole words.
        查找包含任何配置的音频标签的行。
        不区分大小写，匹配完整单词。
        
        Args:
            lines: List of log lines (日志行列表)
            
        Returns:
            Filtered list containing only audio-related lines
            仅包含音频相关行的过滤列表
        """
        if not self.audio_tags:
            # If no tags specified, return all lines
            # 如果未指定标签，返回所有行
            return lines
        
        # Create a regex pattern that matches any of the audio tags
        # 创建匹配任何音频标签的正则表达式模式
        # Use word boundaries for more accurate matching
        # 使用单词边界以获得更准确的匹配
        pattern = re.compile(
            r'\b(' + '|'.join(re.escape(tag) for tag in self.audio_tags) + r')\b',
            re.IGNORECASE
        )
        
        filtered = []
        for line in lines:
            if pattern.search(line):
                filtered.append(line)
        
        return filtered

    def parse_and_filter(self, file_path: str) -> List[str]:
        """Parse a file and filter for audio-related lines.
        解析文件并过滤音频相关的行。
        
        Args:
            file_path: Path to the log file (日志文件路径)
            
        Returns:
            Filtered list of audio-related log lines
            音频相关日志行的过滤列表
        """
        lines = self.parse_file(file_path)
        return self.filter_audio_lines(lines)
