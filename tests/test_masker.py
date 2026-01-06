"""Tests for masker module."""

import pytest
from src.masker import DataMasker


def test_mask_email():
    """Test email masking."""
    masker = DataMasker()
    
    line = "User email is john.doe@example.com and admin@test.org"
    masked = masker.mask_line(line)
    
    assert "[EMAIL]" in masked
    assert "john.doe@example.com" not in masked
    assert "admin@test.org" not in masked


def test_mask_ipv4():
    """Test IPv4 address masking."""
    masker = DataMasker()
    
    line = "Connected to 192.168.1.1 and 10.0.0.5"
    masked = masker.mask_line(line)
    
    assert "[IPv4]" in masked
    assert "192.168.1.1" not in masked
    assert "10.0.0.5" not in masked


def test_mask_ipv6():
    """Test IPv6 address masking."""
    masker = DataMasker()
    
    line = "IPv6 address: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    masked = masker.mask_line(line)
    
    assert "[IPv6]" in masked
    assert "2001:0db8:85a3:0000:0000:8a2e:0370:7334" not in masked


def test_mask_mac_address():
    """Test MAC address masking."""
    masker = DataMasker()
    
    line = "Device MAC: 00:1A:2B:3C:4D:5E and 00-1A-2B-3C-4D-5F"
    masked = masker.mask_line(line)
    
    assert "[MAC]" in masked
    assert "00:1A:2B:3C:4D:5E" not in masked


def test_mask_serial_with_keyword():
    """Test serial number masking when preceded by keyword."""
    masker = DataMasker()
    
    line = "Device Serial: ABC123DEF456 and SN:XYZ789ABC012"
    masked = masker.mask_line(line)
    
    assert "[SERIAL]" in masked
    assert "ABC123DEF456" not in masked
    assert "XYZ789ABC012" not in masked


def test_mask_multiple_types():
    """Test masking multiple sensitive data types in one line."""
    masker = DataMasker()
    
    line = "email: user@test.com IP: 192.168.1.1 Serial: ABCD1234EFGH"
    masked = masker.mask_line(line)
    
    assert "[EMAIL]" in masked
    assert "[IPv4]" in masked
    assert "[SERIAL]" in masked
    assert "user@test.com" not in masked
    assert "192.168.1.1" not in masked


def test_mask_lines_multiple():
    """Test masking multiple lines."""
    masker = DataMasker()
    
    lines = [
        "User: test@example.com",
        "IP Address: 10.0.0.1",
        "Serial: SN:12345678"
    ]
    
    masked = masker.mask_lines(lines)
    
    assert len(masked) == 3
    assert "[EMAIL]" in masked[0]
    assert "[IPv4]" in masked[1]
    assert "[SERIAL]" in masked[2]


def test_mask_no_sensitive_data():
    """Test that lines without sensitive data remain unchanged."""
    masker = DataMasker()
    
    line = "This is a normal log line with no sensitive data"
    masked = masker.mask_line(line)
    
    assert masked == line


def test_mask_preserves_structure():
    """Test that masking preserves line structure."""
    masker = DataMasker()
    
    line = "01-06 10:15:23.456  1234  1235 I AudioFlinger: Connected from 192.168.1.5"
    masked = masker.mask_line(line)
    
    # Should preserve timestamp and other structure
    assert masked.startswith("01-06 10:15:23.456")
    assert "AudioFlinger" in masked
    assert "[IPv4]" in masked


def test_mask_case_insensitive_serial():
    """Test that serial keyword matching is case-insensitive."""
    masker = DataMasker()
    
    lines = [
        "serial: ABC12345678",
        "Serial: DEF12345678",
        "SERIAL: GHI12345678",
        "sn: JKL12345678"
    ]
    
    for line in lines:
        masked = masker.mask_line(line)
        assert "[SERIAL]" in masked


def test_mask_empty_line():
    """Test masking empty line."""
    masker = DataMasker()
    
    line = ""
    masked = masker.mask_line(line)
    
    assert masked == ""


def test_mask_lines_empty_list():
    """Test masking empty list."""
    masker = DataMasker()
    
    lines = []
    masked = masker.mask_lines(lines)
    
    assert masked == []
