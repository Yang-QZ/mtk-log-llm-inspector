"""Data masking utilities for removing sensitive information.
数据脱敏工具 - 用于移除日志中的敏感信息。
"""

import re
from typing import List


class DataMasker:
    """Masks sensitive data in log lines.
    敏感数据脱敏器 - 对日志行中的敏感数据进行脱敏处理。
    """

    def __init__(self):
        """Initialize the data masker with regex patterns.
        使用正则表达式模式初始化数据脱敏器。
        """
        # Pattern for email addresses (邮箱地址匹配模式)
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Pattern for IPv4 addresses (IPv4地址匹配模式)
        self.ipv4_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # Pattern for IPv6 addresses (simplified) (IPv6地址匹配模式，简化版)
        self.ipv6_pattern = re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
        )
        
        # Pattern for device serial numbers (common formats)
        # 设备序列号匹配模式（常见格式）
        # Matches patterns like: 12345678, ABC123DEF456, Serial:XXXXXXXXX
        # 匹配如: 12345678, ABC123DEF456, Serial:XXXXXXXXX 等格式
        self.serial_pattern = re.compile(
            r'\b(?:serial|Serial|SERIAL|SN|sn)[:\s]*([A-Z0-9]{8,})\b|'
            r'\b([A-Z0-9]{8}[A-Z0-9]*)\b(?=\s|$)',
            re.IGNORECASE
        )
        
        # Pattern for MAC addresses (MAC地址匹配模式)
        self.mac_pattern = re.compile(
            r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        )

    def mask_line(self, line: str) -> str:
        """Mask sensitive data in a single line.
        对单行日志中的敏感数据进行脱敏。
        
        Args:
            line: Log line to mask (要脱敏的日志行)
            
        Returns:
            Masked log line (脱敏后的日志行)
        """
        # Mask emails (脱敏邮箱地址)
        line = self.email_pattern.sub('[EMAIL]', line)
        
        # Mask IP addresses (脱敏IP地址)
        line = self.ipv4_pattern.sub('[IPv4]', line)
        line = self.ipv6_pattern.sub('[IPv6]', line)
        
        # Mask MAC addresses (脱敏MAC地址)
        line = self.mac_pattern.sub('[MAC]', line)
        
        # Mask serial numbers (more conservative - only if preceded by serial keyword)
        # 脱敏序列号（更保守的方式 - 仅当前面有序列号关键字时）
        # This is intentionally simple to avoid false positives
        # 这样设计是为了避免误判
        line = re.sub(
            r'(?i)\b(?:serial|SN)[:\s]*[A-Z0-9]{8,}\b',
            '[SERIAL]',
            line
        )
        
        return line

    def mask_lines(self, lines: List[str]) -> List[str]:
        """Mask sensitive data in multiple lines.
        对多行日志中的敏感数据进行脱敏。
        
        Args:
            lines: List of log lines to mask (要脱敏的日志行列表)
            
        Returns:
            List of masked log lines (脱敏后的日志行列表)
        """
        return [self.mask_line(line) for line in lines]
