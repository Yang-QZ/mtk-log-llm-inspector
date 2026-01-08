"""Analysis and segment merging utilities.
分析和片段合并工具。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class AudioSegment:
    """Represents a merged audio state segment.
    表示合并后的音频状态片段。
    """

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
        初始化音频片段。
        
        Args:
            state: Audio state (PLAYING, MUTED, UNKNOWN)
                  音频状态（播放中、静音、未知）
            start_window: Starting window index (inclusive)
                         起始窗口索引（包含）
            end_window: Ending window index (inclusive)
                       结束窗口索引（包含）
            confidence_avg: Average confidence across windows
                           跨窗口的平均置信度
            evidence: Combined evidence from all windows
                     来自所有窗口的组合证据
            reasons: Reasons from all windows
                    来自所有窗口的原因
        """
        self.state = state
        self.start_window = start_window
        self.end_window = end_window
        self.confidence_avg = confidence_avg
        self.evidence = evidence
        self.reasons = reasons

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary.
        将片段转换为字典。
        """
        return {
            "state": self.state,
            "start_window": self.start_window,
            "end_window": self.end_window,
            "window_count": self.end_window - self.start_window + 1,
            "confidence_avg": round(self.confidence_avg, 2),
            "evidence": self.evidence[:5],  # Limit to 5 evidence items (限制为5个证据项)
            "reasons": self.reasons
        }


class WindowAnalyzer:
    """Analyzes windows and merges consecutive windows with the same state.
    分析窗口并合并具有相同状态的连续窗口。
    """

    def merge_windows(self, window_results: List[Dict[str, Any]]) -> List[AudioSegment]:
        """Merge consecutive windows with the same final_state into segments.
        将具有相同最终状态的连续窗口合并为片段。
        
        Args:
            window_results: List of analysis results from each window
                          每个窗口的分析结果列表
                Each result should have: window_idx, final_state, confidence, reason, evidence
                每个结果应包含: window_idx, final_state, confidence, reason, evidence
                
        Returns:
            List of merged AudioSegment objects
            合并后的AudioSegment对象列表
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
                # Start new segment (开始新片段)
                current_segment = {
                    "state": state,
                    "start_window": window_idx,
                    "end_window": window_idx,
                    "confidences": [confidence],
                    "evidence": list(evidence),
                    "reasons": [reason]
                }
            elif current_segment["state"] == state:
                # Extend current segment (扩展当前片段)
                current_segment["end_window"] = window_idx
                current_segment["confidences"].append(confidence)
                current_segment["evidence"].extend(evidence)
                current_segment["reasons"].append(reason)
            else:
                # State changed, save current segment and start new one
                # 状态改变，保存当前片段并开始新片段
                segments.append(self._create_segment(current_segment))
                current_segment = {
                    "state": state,
                    "start_window": window_idx,
                    "end_window": window_idx,
                    "confidences": [confidence],
                    "evidence": list(evidence),
                    "reasons": [reason]
                }
        
        # Save last segment (保存最后一个片段)
        if current_segment is not None:
            segments.append(self._create_segment(current_segment))
        
        return segments

    def _create_segment(self, segment_data: Dict[str, Any]) -> AudioSegment:
        """Create AudioSegment from accumulated data.
        从累积的数据创建AudioSegment。
        """
        # Calculate average confidence (计算平均置信度)
        confidences = segment_data["confidences"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Deduplicate evidence while preserving order
        # 去重证据，同时保持顺序
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
        生成完整的分析报告。
        
        Args:
            segments: List of merged segments (合并后的片段列表)
            window_results: Raw window analysis results (原始窗口分析结果)
            metadata: Analysis metadata (file path, settings, etc.)
                     分析元数据（文件路径、设置等）
            
        Returns:
            Complete report dictionary (完整的报告字典)
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
        """Count segments by state.
        按状态统计片段数量。
        """
        counts = {"PLAYING": 0, "MUTED": 0, "UNKNOWN": 0}
        for seg in segments:
            counts[seg.state] += 1
        return counts

    def generate_markdown_report(
        self,
        segments: List[AudioSegment],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate markdown summary report.
        生成Markdown格式的摘要报告。
        
        Args:
            segments: List of merged segments (合并后的片段列表)
            metadata: Analysis metadata (分析元数据)
            
        Returns:
            Markdown-formatted report string (Markdown格式的报告字符串)
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
