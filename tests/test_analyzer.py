"""Tests for analyzer module."""

import pytest
from src.analyzer import WindowAnalyzer, AudioSegment


def test_audio_segment_creation():
    """Test AudioSegment creation."""
    segment = AudioSegment(
        state="PLAYING",
        start_window=0,
        end_window=2,
        confidence_avg=0.85,
        evidence=["Line 1", "Line 2"],
        reasons=["Reason 1", "Reason 2"]
    )
    
    assert segment.state == "PLAYING"
    assert segment.start_window == 0
    assert segment.end_window == 2
    assert segment.confidence_avg == 0.85


def test_audio_segment_to_dict():
    """Test AudioSegment to_dict conversion."""
    segment = AudioSegment(
        state="MUTED",
        start_window=5,
        end_window=7,
        confidence_avg=0.92,
        evidence=["E1", "E2", "E3"],
        reasons=["R1"]
    )
    
    data = segment.to_dict()
    
    assert data["state"] == "MUTED"
    assert data["start_window"] == 5
    assert data["end_window"] == 7
    assert data["window_count"] == 3  # 7 - 5 + 1
    assert data["confidence_avg"] == 0.92
    assert data["evidence"] == ["E1", "E2", "E3"]


def test_audio_segment_limits_evidence():
    """Test that to_dict limits evidence to 5 items."""
    segment = AudioSegment(
        state="PLAYING",
        start_window=0,
        end_window=0,
        confidence_avg=0.8,
        evidence=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
        reasons=["R"]
    )
    
    data = segment.to_dict()
    
    assert len(data["evidence"]) == 5


def test_merge_windows_single():
    """Test merging a single window."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {
            "window_idx": 0,
            "final_state": "PLAYING",
            "confidence": 0.9,
            "reason": "Track active",
            "evidence": ["Line 1", "Line 2"]
        }
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    assert len(segments) == 1
    assert segments[0].state == "PLAYING"
    assert segments[0].start_window == 0
    assert segments[0].end_window == 0


def test_merge_windows_same_state():
    """Test merging consecutive windows with same state."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {
            "window_idx": 0,
            "final_state": "PLAYING",
            "confidence": 0.9,
            "reason": "Track active",
            "evidence": ["Line 1"]
        },
        {
            "window_idx": 1,
            "final_state": "PLAYING",
            "confidence": 0.85,
            "reason": "Still playing",
            "evidence": ["Line 2"]
        },
        {
            "window_idx": 2,
            "final_state": "PLAYING",
            "confidence": 0.88,
            "reason": "Continues",
            "evidence": ["Line 3"]
        }
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    # Should merge all three windows into one segment
    assert len(segments) == 1
    assert segments[0].state == "PLAYING"
    assert segments[0].start_window == 0
    assert segments[0].end_window == 2
    assert segments[0].confidence_avg == pytest.approx((0.9 + 0.85 + 0.88) / 3)


def test_merge_windows_state_changes():
    """Test merging with state changes."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {
            "window_idx": 0,
            "final_state": "PLAYING",
            "confidence": 0.9,
            "reason": "Playing",
            "evidence": ["E1"]
        },
        {
            "window_idx": 1,
            "final_state": "PLAYING",
            "confidence": 0.85,
            "reason": "Still playing",
            "evidence": ["E2"]
        },
        {
            "window_idx": 2,
            "final_state": "MUTED",
            "confidence": 0.95,
            "reason": "Muted",
            "evidence": ["E3"]
        },
        {
            "window_idx": 3,
            "final_state": "MUTED",
            "confidence": 0.92,
            "reason": "Still muted",
            "evidence": ["E4"]
        },
        {
            "window_idx": 4,
            "final_state": "UNKNOWN",
            "confidence": 0.5,
            "reason": "Unclear",
            "evidence": ["E5"]
        }
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    # Should create 3 segments: PLAYING(0-1), MUTED(2-3), UNKNOWN(4)
    assert len(segments) == 3
    
    assert segments[0].state == "PLAYING"
    assert segments[0].start_window == 0
    assert segments[0].end_window == 1
    
    assert segments[1].state == "MUTED"
    assert segments[1].start_window == 2
    assert segments[1].end_window == 3
    
    assert segments[2].state == "UNKNOWN"
    assert segments[2].start_window == 4
    assert segments[2].end_window == 4


def test_merge_windows_deduplicates_evidence():
    """Test that merging deduplicates evidence."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {
            "window_idx": 0,
            "final_state": "PLAYING",
            "confidence": 0.9,
            "reason": "R1",
            "evidence": ["E1", "E2"]
        },
        {
            "window_idx": 1,
            "final_state": "PLAYING",
            "confidence": 0.85,
            "reason": "R2",
            "evidence": ["E2", "E3"]  # E2 is duplicate
        }
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    assert len(segments) == 1
    # Should have E1, E2, E3 (E2 not duplicated)
    assert len(segments[0].evidence) == 3
    assert "E1" in segments[0].evidence
    assert "E2" in segments[0].evidence
    assert "E3" in segments[0].evidence


def test_merge_windows_empty():
    """Test merging empty window results."""
    analyzer = WindowAnalyzer()
    
    segments = analyzer.merge_windows([])
    
    assert len(segments) == 0


def test_generate_report():
    """Test report generation."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {
            "window_idx": 0,
            "final_state": "PLAYING",
            "confidence": 0.9,
            "reason": "Playing",
            "evidence": ["E1"]
        }
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    metadata = {
        "log_file": "/path/to/log.txt",
        "timestamp": "2024-01-06T10:00:00"
    }
    
    report = analyzer.generate_report(segments, window_results, metadata)
    
    assert "metadata" in report
    assert "summary" in report
    assert "window_results" in report
    assert "merged_segments" in report
    
    assert report["summary"]["total_windows"] == 1
    assert report["summary"]["total_segments"] == 1


def test_count_states():
    """Test state counting through generate_report."""
    analyzer = WindowAnalyzer()
    
    window_results = [
        {"window_idx": 0, "final_state": "PLAYING", "confidence": 0.9, "reason": "R1", "evidence": []},
        {"window_idx": 1, "final_state": "PLAYING", "confidence": 0.85, "reason": "R2", "evidence": []},
        {"window_idx": 2, "final_state": "MUTED", "confidence": 0.95, "reason": "R3", "evidence": []},
        {"window_idx": 3, "final_state": "PLAYING", "confidence": 0.9, "reason": "R5", "evidence": []},
        {"window_idx": 4, "final_state": "UNKNOWN", "confidence": 0.5, "reason": "R4", "evidence": []},
    ]
    
    segments = analyzer.merge_windows(window_results)
    
    metadata = {"log_file": "/test.log", "timestamp": "2024-01-06"}
    report = analyzer.generate_report(segments, window_results, metadata)
    
    # Verify state counts through the public API
    # Should have: PLAYING (0-1), MUTED (2), PLAYING (3), UNKNOWN (4) = 2 PLAYING, 1 MUTED, 1 UNKNOWN
    counts = report["summary"]["states_distribution"]
    assert counts["PLAYING"] == 2
    assert counts["MUTED"] == 1
    assert counts["UNKNOWN"] == 1


def test_generate_markdown_report():
    """Test markdown report generation."""
    analyzer = WindowAnalyzer()
    
    segments = [
        AudioSegment(
            state="PLAYING",
            start_window=0,
            end_window=2,
            confidence_avg=0.88,
            evidence=["Evidence 1", "Evidence 2"],
            reasons=["Reason 1"]
        )
    ]
    
    metadata = {
        "timestamp": "2024-01-06T10:00:00",
        "log_file": "/path/to/log.txt",
        "total_windows": 3
    }
    
    markdown = analyzer.generate_markdown_report(segments, metadata)
    
    assert "# Audio State Analysis Report" in markdown
    assert "PLAYING" in markdown
    assert "Evidence 1" in markdown
    assert "0 to 2" in markdown
