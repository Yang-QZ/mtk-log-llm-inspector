"""Log parsing and filtering utilities."""

import re
from typing import List, Optional


# Default audio-related tags commonly found in Android logcat
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
    """Parser for Android logcat files."""

    def __init__(self, audio_tags: Optional[List[str]] = None):
        """Initialize the log parser.
        
        Args:
            audio_tags: List of audio-related tags to filter for. If None, uses default list.
        """
        self.audio_tags = audio_tags if audio_tags is not None else DEFAULT_AUDIO_TAGS

    def parse_file(self, file_path: str) -> List[str]:
        """Parse a logcat file and return all lines.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of log lines (stripped of trailing whitespace)
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.rstrip() for line in f if line.strip()]
        return lines

    def filter_audio_lines(self, lines: List[str]) -> List[str]:
        """Filter lines to only include audio-related content.
        
        This looks for lines containing any of the configured audio tags.
        It's case-insensitive and matches whole words.
        
        Args:
            lines: List of log lines
            
        Returns:
            Filtered list containing only audio-related lines
        """
        if not self.audio_tags:
            # If no tags specified, return all lines
            return lines
        
        # Create a regex pattern that matches any of the audio tags
        # Use word boundaries for more accurate matching
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
        
        Args:
            file_path: Path to the log file
            
        Returns:
            Filtered list of audio-related log lines
        """
        lines = self.parse_file(file_path)
        return self.filter_audio_lines(lines)
