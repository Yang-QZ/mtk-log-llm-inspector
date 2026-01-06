"""Command-line interface for MTK Log LLM Inspector."""

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
    """Load system prompt from docs/prompt.md."""
    # Find prompt.md relative to this file
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
    
    Args:
        output_dir: Output directory (should be out/debug/)
        window_idx: Window index
        request_data: Request data to save (will redact auth)
        response_data: Response data to save
    """
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Redact authorization header from request
    if "headers" in request_data:
        headers = request_data["headers"].copy()
        if "Authorization" in headers:
            headers["Authorization"] = "[REDACTED]"
        request_data = {**request_data, "headers": headers}
    
    # Save request
    request_file = debug_dir / f"window_{window_idx}_request.json"
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, indent=2)
    
    # Save response
    response_file = debug_dir / f"window_{window_idx}_response.json"
    with open(response_file, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=2)


def analyze_command(args):
    """Execute the analyze command."""
    # Validate input file
    log_path = Path(args.log)
    if not log_path.exists():
        print(f"Error: Log file not found: {args.log}", file=sys.stderr)
        return 1
    
    # Create output directory
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
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
    
    # Load system prompt
    try:
        system_prompt = load_system_prompt()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    print(f"Parsing log file: {args.log}")
    
    # Parse and filter log file
    lines = parser.parse_and_filter(str(log_path))
    print(f"Found {len(lines)} audio-related lines")
    
    # Apply masking if requested
    if masker:
        print("Applying data masking...")
        lines = masker.mask_lines(lines)
    
    # Chunk the lines
    windows = chunker.chunk_lines(lines)
    print(f"Split into {len(windows)} windows (chunk_size={args.chunk_size}, overlap={args.overlap})")
    
    # Analyze each window
    window_results = []
    for window_idx, window_lines in windows:
        print(f"Analyzing window {window_idx + 1}/{len(windows)}...", end=" ", flush=True)
        
        log_content = "\n".join(window_lines)
        
        try:
            # Analyze with LLM
            result = client.analyze_log_window(system_prompt, log_content)
            
            # Add window index to result
            result["window_idx"] = window_idx
            window_results.append(result)
            
            print(f"✓ State: {result['final_state']} (confidence: {result['confidence']:.2f})")
            
            # Save debug files if requested
            if args.debug:
                # Prepare request data for debug output
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
                response_data = {
                    "parsed_result": result,
                    "window_lines_count": len(window_lines)
                }
                
                save_debug_files(out_dir, window_idx, request_data, response_data)
        
        except Exception as e:
            print(f"✗ Error: {e}")
            # Add failed result
            window_results.append({
                "window_idx": window_idx,
                "final_state": "UNKNOWN",
                "confidence": 0.0,
                "reason": f"Analysis failed: {str(e)}",
                "evidence": [],
                "next_actions": ["Retry analysis", "Check API connectivity"]
            })
    
    # Merge segments
    print("\nMerging consecutive windows with same state...")
    segments = analyzer.merge_windows(window_results)
    print(f"Created {len(segments)} merged segments")
    
    # Generate reports
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
    
    # JSON report
    report = analyzer.generate_report(segments, window_results, metadata)
    json_path = out_dir / "report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved to: {json_path}")
    
    # Markdown report
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
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Analyze Android logcat files using Alibaba Cloud Bailian (Qwen) LLM"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a log file")
    analyze_parser.add_argument(
        "--log",
        required=True,
        help="Path to input log file"
    )
    analyze_parser.add_argument(
        "--out",
        required=True,
        help="Path to output directory"
    )
    analyze_parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Number of lines per window (default: 200)"
    )
    analyze_parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Number of overlapping lines between windows (default: 50)"
    )
    analyze_parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (default: from BAILIAN_MODEL env or qwen-plus)"
    )
    analyze_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (saves request/response JSON)"
    )
    analyze_parser.add_argument(
        "--mask",
        action="store_true",
        help="Enable data masking for sensitive information"
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
