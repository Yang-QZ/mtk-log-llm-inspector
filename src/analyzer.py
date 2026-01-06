"""Analysis and segment merging utilities."""

from typing import List, Dict, Any, Optional
from datetime import datetime


class AudioSegment:
    """Represents a merged audio state segment."""

    def __init__(
        self,
        state: str,
        start_window: int,
        end_window: int,
        confidence_avg: float,
        evidence: List[str],
        reasons: List[str]
    ):
        """Initialize an audio segment.
        
        Args:
            state: Audio state (PLAYING, MUTED, UNKNOWN)
            start_window: Starting window index (inclusive)
            end_window: Ending window index (inclusive)
            confidence_avg: Average confidence across windows
            evidence: Combined evidence from all windows
            reasons: Reasons from all windows
        """
        self.state = state
        self.start_window = start_window
        self.end_window = end_window
        self.confidence_avg = confidence_avg
        self.evidence = evidence
        self.reasons = reasons

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary."""
        return {
            "state": self.state,
            "start_window": self.start_window,
            "end_window": self.end_window,
            "window_count": self.end_window - self.start_window + 1,
            "confidence_avg": round(self.confidence_avg, 2),
            "evidence": self.evidence[:5],  # Limit to 5 evidence items
            "reasons": self.reasons
        }


class WindowAnalyzer:
    """Analyzes windows and merges consecutive windows with the same state."""

    def merge_windows(self, window_results: List[Dict[str, Any]]) -> List[AudioSegment]:
        """Merge consecutive windows with the same final_state into segments.
        
        Args:
            window_results: List of analysis results from each window
                Each result should have: window_idx, final_state, confidence, reason, evidence
                
        Returns:
            List of merged AudioSegment objects
        """
        if not window_results:
            return []
        
        segments = []
        current_segment = None
        
        for result in window_results:
            state = result["final_state"]
            window_idx = result["window_idx"]
            confidence = result["confidence"]
            reason = result["reason"]
            evidence = result.get("evidence", [])
            
            if current_segment is None:
                # Start new segment
                current_segment = {
                    "state": state,
                    "start_window": window_idx,
                    "end_window": window_idx,
                    "confidences": [confidence],
                    "evidence": list(evidence),
                    "reasons": [reason]
                }
            elif current_segment["state"] == state:
                # Extend current segment
                current_segment["end_window"] = window_idx
                current_segment["confidences"].append(confidence)
                current_segment["evidence"].extend(evidence)
                current_segment["reasons"].append(reason)
            else:
                # State changed, save current segment and start new one
                segments.append(self._create_segment(current_segment))
                current_segment = {
                    "state": state,
                    "start_window": window_idx,
                    "end_window": window_idx,
                    "confidences": [confidence],
                    "evidence": list(evidence),
                    "reasons": [reason]
                }
        
        # Save last segment
        if current_segment is not None:
            segments.append(self._create_segment(current_segment))
        
        return segments

    def _create_segment(self, segment_data: Dict[str, Any]) -> AudioSegment:
        """Create AudioSegment from accumulated data."""
        # Calculate average confidence
        confidences = segment_data["confidences"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Deduplicate evidence while preserving order
        seen = set()
        unique_evidence = []
        for item in segment_data["evidence"]:
            if item not in seen:
                seen.add(item)
                unique_evidence.append(item)
        
        return AudioSegment(
            state=segment_data["state"],
            start_window=segment_data["start_window"],
            end_window=segment_data["end_window"],
            confidence_avg=avg_confidence,
            evidence=unique_evidence,
            reasons=segment_data["reasons"]
        )

    def generate_report(
        self,
        segments: List[AudioSegment],
        window_results: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete analysis report.
        
        Args:
            segments: List of merged segments
            window_results: Raw window analysis results
            metadata: Analysis metadata (file path, settings, etc.)
            
        Returns:
            Complete report dictionary
        """
        return {
            "metadata": metadata,
            "summary": {
                "total_windows": len(window_results),
                "total_segments": len(segments),
                "states_distribution": self._count_states(segments)
            },
            "window_results": window_results,
            "merged_segments": [seg.to_dict() for seg in segments]
        }

    def _count_states(self, segments: List[AudioSegment]) -> Dict[str, int]:
        """Count segments by state."""
        counts = {"PLAYING": 0, "MUTED": 0, "UNKNOWN": 0}
        for seg in segments:
            counts[seg.state] = counts.get(seg.state, 0) + 1
        return counts

    def generate_markdown_report(
        self,
        segments: List[AudioSegment],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate markdown summary report.
        
        Args:
            segments: List of merged segments
            metadata: Analysis metadata
            
        Returns:
            Markdown-formatted report string
        """
        lines = []
        lines.append("# Audio State Analysis Report")
        lines.append("")
        lines.append(f"**Analysis Time:** {metadata.get('timestamp', 'N/A')}")
        lines.append(f"**Log File:** {metadata.get('log_file', 'N/A')}")
        lines.append(f"**Total Windows:** {metadata.get('total_windows', 0)}")
        lines.append(f"**Total Segments:** {len(segments)}")
        lines.append("")
        
        lines.append("## Segments Summary")
        lines.append("")
        
        for i, segment in enumerate(segments, 1):
            lines.append(f"### Segment {i}: {segment.state}")
            lines.append(f"- **Windows:** {segment.start_window} to {segment.end_window} "
                        f"({segment.end_window - segment.start_window + 1} windows)")
            lines.append(f"- **Average Confidence:** {segment.confidence_avg:.2f}")
            lines.append("")
            
            lines.append("**Key Evidence (up to 5 lines):**")
            lines.append("```")
            for evidence_line in segment.evidence[:5]:
                lines.append(evidence_line)
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines)
