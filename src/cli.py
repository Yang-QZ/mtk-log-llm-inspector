"""Command-line interface for MTK Log LLM Inspector.
MTK日志大语言模型分析器的命令行界面。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .bailian_client import BailianClient
from .log_parser import LogParser
from .chunker import LogChunker
from .masker import DataMasker
from .analyzer import WindowAnalyzer


def load_system_prompt() -> str:
    """Load system prompt from docs/prompt.md.
    从docs/prompt.md加载系统提示词。
    """
    # Find prompt.md relative to this file
    # 查找相对于此文件的prompt.md
    current_dir = Path(__file__).parent.parent
    prompt_path = current_dir / "docs" / "prompt.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt not found at {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_debug_files(
    output_dir: Path,
    window_idx: int,
    request_data: dict,
    response_data: dict
):
    """Save request and response JSON for debugging.
    保存请求和响应JSON用于调试。
    
    Args:
        output_dir: Output directory (should be out/debug/)
                   输出目录（应为out/debug/）
        window_idx: Window index (窗口索引)
        request_data: Request data to save (will redact auth)
                     要保存的请求数据（会隐藏授权信息）
        response_data: Response data to save (要保存的响应数据)
    """
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Redact authorization header from request
    # 从请求中隐藏授权头
    if "headers" in request_data:
        headers = request_data["headers"].copy()
        if "Authorization" in headers:
            headers["Authorization"] = "[REDACTED]"
        request_data = {**request_data, "headers": headers}
    
    # Save request (保存请求)
    request_file = debug_dir / f"window_{window_idx}_request.json"
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, indent=2)
    
    # Save response (保存响应)
    response_file = debug_dir / f"window_{window_idx}_response.json"
    with open(response_file, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=2)


def analyze_command(args):
    """Execute the analyze command.
    执行分析命令。
    """
    # Validate input file (验证输入文件)
    log_path = Path(args.log)
    if not log_path.exists():
        print(f"Error: Log file not found: {args.log}", file=sys.stderr)
        return 1
    
    # Create output directory (创建输出目录)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components (初始化组件)
    try:
        client = BailianClient(model=args.model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please set BAILIAN_API_KEY environment variable", file=sys.stderr)
        return 1
    
    parser = LogParser()
    chunker = LogChunker(chunk_size=args.chunk_size, overlap=args.overlap)
    analyzer = WindowAnalyzer()
    masker = DataMasker() if args.mask else None
    
    # Load system prompt (加载系统提示词)
    try:
        system_prompt = load_system_prompt()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    print(f"Parsing log file: {args.log}")
    
    # Parse and filter log file (解析和过滤日志文件)
    lines = parser.parse_and_filter(str(log_path))
    print(f"Found {len(lines)} audio-related lines")
    
    # Apply masking if requested (如果需要，应用数据脱敏)
    if masker:
        print("Applying data masking...")
        lines = masker.mask_lines(lines)
    
    # Chunk the lines (对日志行进行分块)
    windows = chunker.chunk_lines(lines)
    print(f"Split into {len(windows)} windows (chunk_size={args.chunk_size}, overlap={args.overlap})")
    
    # Analyze each window (分析每个窗口)
    window_results = []
    for window_idx, window_lines in windows:
        print(f"Analyzing window {window_idx + 1}/{len(windows)}...", end=" ", flush=True)
        
        log_content = "\n".join(window_lines)
        
        try:
            # Analyze with LLM (使用大语言模型分析)
            result = client.analyze_log_window(system_prompt, log_content)
            
            # Add window index to result (将窗口索引添加到结果中)
            result["window_idx"] = window_idx
            window_results.append(result)
            
            print(f"✓ State: {result['final_state']} (confidence: {result['confidence']:.2f})")
            
            # Save debug files if requested (如果需要，保存调试文件)
            if args.debug:
                # Prepare request data for debug output
                # 准备调试输出的请求数据
                request_data = {
                    "url": f"{client.base_url}/chat/completions",
                    "headers": {
                        "Authorization": f"Bearer {client.api_key}",
                        "Content-Type": "application/json"
                    },
                    "payload": {
                        "model": client.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Analyze this log window:\n\n{log_content}"}
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    }
                }
                
                # For response, we save the parsed result
                # 对于响应，我们保存解析后的结果
                response_data = {
                    "parsed_result": result,
                    "window_lines_count": len(window_lines)
                }
                
                save_debug_files(out_dir, window_idx, request_data, response_data)
        
        except Exception as e:
            print(f"✗ Error: {e}")
            # Add failed result (添加失败的结果)
            window_results.append({
                "window_idx": window_idx,
                "final_state": "UNKNOWN",
                "confidence": 0.0,
                "reason": f"Analysis failed: {str(e)}",
                "evidence": [],
                "next_actions": ["Retry analysis", "Check API connectivity"]
            })
    
    # Merge segments (合并片段)
    print("\nMerging consecutive windows with same state...")
    segments = analyzer.merge_windows(window_results)
    print(f"Created {len(segments)} merged segments")
    
    # Generate reports (生成报告)
    metadata = {
        "log_file": str(log_path.absolute()),
        "timestamp": datetime.now().isoformat(),
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "model": client.model,
        "masking_enabled": args.mask,
        "total_windows": len(windows),
        "total_lines": len(lines)
    }
    
    # JSON report (JSON报告)
    report = analyzer.generate_report(segments, window_results, metadata)
    json_path = out_dir / "report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved to: {json_path}")
    
    # Markdown report (Markdown报告)
    markdown_content = analyzer.generate_markdown_report(segments, metadata)
    md_path = out_dir / "report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"Markdown report saved to: {md_path}")
    
    if args.debug:
        print(f"Debug files saved to: {out_dir / 'debug'}")
    
    print("\n✓ Analysis complete!")
    return 0


def main():
    """Main entry point for CLI.
    CLI的主入口点。
    """
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Analyze Android logcat files using Alibaba Cloud Bailian (Qwen) LLM"
                   "\n使用阿里云百炼（通义千问）大语言模型分析Android日志文件"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command (分析命令)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a log file (分析日志文件)")
    analyze_parser.add_argument(
        "--log",
        required=True,
        help="Path to input log file (输入日志文件路径)"
    )
    analyze_parser.add_argument(
        "--out",
        required=True,
        help="Path to output directory (输出目录路径)"
    )
    analyze_parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Number of lines per window (default: 200) (每个窗口的行数，默认：200)"
    )
    analyze_parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Number of overlapping lines between windows (default: 50) (窗口之间的重叠行数，默认：50)"
    )
    analyze_parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (default: from BAILIAN_MODEL env or qwen-plus) "
             "(大模型名称，默认：从BAILIAN_MODEL环境变量或qwen-plus)"
    )
    analyze_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (saves request/response JSON) (启用调试模式，保存请求/响应JSON)"
    )
    analyze_parser.add_argument(
        "--mask",
        action="store_true",
        help="Enable data masking for sensitive information (启用敏感信息脱敏)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "analyze":
        return analyze_command(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
