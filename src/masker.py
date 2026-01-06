"""Data masking utilities for removing sensitive information."""

import re
from typing import List


class DataMasker:
    """Masks sensitive data in log lines."""

    def __init__(self):
        """Initialize the data masker with regex patterns."""
        # Pattern for email addresses
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Pattern for IPv4 addresses
        self.ipv4_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # Pattern for IPv6 addresses (simplified)
        self.ipv6_pattern = re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
        )
        
        # Pattern for device serial numbers (common formats)
        # Matches patterns like: 12345678, ABC123DEF456, Serial:XXXXXXXXX
        self.serial_pattern = re.compile(
            r'\b(?:serial|Serial|SERIAL|SN|sn)[:\s]*([A-Z0-9]{8,})\b|'
            r'\b([A-Z0-9]{8}[A-Z0-9]*)\b(?=\s|$)',
            re.IGNORECASE
        )
        
        # Pattern for MAC addresses
        self.mac_pattern = re.compile(
            r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        )

    def mask_line(self, line: str) -> str:
        """Mask sensitive data in a single line.
        
        Args:
            line: Log line to mask
            
        Returns:
            Masked log line
        """
        # Mask emails
        line = self.email_pattern.sub('[EMAIL]', line)
        
        # Mask IP addresses
        line = self.ipv4_pattern.sub('[IPv4]', line)
        line = self.ipv6_pattern.sub('[IPv6]', line)
        
        # Mask MAC addresses
        line = self.mac_pattern.sub('[MAC]', line)
        
        # Mask serial numbers (more conservative - only if preceded by serial keyword)
        # This is intentionally simple to avoid false positives
        line = re.sub(
            r'(?i)\b(?:serial|SN)[:\s]*[A-Z0-9]{8,}\b',
            '[SERIAL]',
            line
        )
        
        return line

    def mask_lines(self, lines: List[str]) -> List[str]:
        """Mask sensitive data in multiple lines.
        
        Args:
            lines: List of log lines to mask
            
        Returns:
            List of masked log lines
        """
        return [self.mask_line(line) for line in lines]
