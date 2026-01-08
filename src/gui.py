"""GUI application for MTK Log LLM Inspector.
MTK日志大语言模型分析器的图形界面应用。

This module provides a Windows-compatible GUI interface for the log analyzer.
本模块为日志分析器提供Windows兼容的图形界面。
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

# Import analyzer components
from .bailian_client import BailianClient
from .log_parser import LogParser
from .chunker import LogChunker
from .masker import DataMasker
from .analyzer import WindowAnalyzer


class LogInspectorGUI:
    """Main GUI application class for MTK Log LLM Inspector.
    MTK日志大语言模型分析器的主GUI应用类。
    """
    
    def __init__(self, root):
        """Initialize the GUI application.
        初始化GUI应用程序。
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("MTK Log LLM Inspector - 日志分析工具")
        self.root.geometry("900x700")
        
        # Variables
        self.api_key_var = tk.StringVar()
        self.model_var = tk.StringVar(value="qwen-plus")
        self.log_file_path = tk.StringVar()
        self.spec_doc_text = ""
        self.chunk_size_var = tk.IntVar(value=200)
        self.overlap_var = tk.IntVar(value=50)
        self.mask_var = tk.BooleanVar(value=False)
        
        # Load saved API key if exists
        self._load_config()
        
        # Setup UI
        self._create_widgets()
        
        # Enable drag and drop
        self._setup_drag_drop()
    
    def _create_widgets(self):
        """Create all GUI widgets.
        创建所有GUI组件。
        """
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Configuration
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="配置 Configuration")
        self._create_config_tab(config_frame)
        
        # Tab 2: Analysis
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="分析 Analysis")
        self._create_analysis_tab(analysis_frame)
        
        # Tab 3: Results
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="结果 Results")
        self._create_results_tab(results_frame)
        
    def _create_config_tab(self, parent):
        """Create configuration tab.
        创建配置标签页。
        
        Args:
            parent: Parent frame
        """
        # API Key Section
        api_frame = ttk.LabelFrame(parent, text="LLM API 配置 Configuration", padding=10)
        api_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky='w', pady=5)
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        api_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Button(api_frame, text="保存 Save", command=self._save_api_key).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        ttk.Label(api_frame, text="模型 Model:").grid(row=1, column=0, sticky='w', pady=5)
        model_combo = ttk.Combobox(
            api_frame, 
            textvariable=self.model_var,
            values=["qwen-plus", "qwen-turbo", "qwen-max"],
            state='readonly',
            width=47
        )
        model_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        # Analysis Parameters Section
        param_frame = ttk.LabelFrame(parent, text="分析参数 Analysis Parameters", padding=10)
        param_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(param_frame, text="窗口大小 Chunk Size:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Spinbox(
            param_frame, 
            from_=50, 
            to=500, 
            textvariable=self.chunk_size_var,
            width=20
        ).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Label(param_frame, text="重叠行数 Overlap:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Spinbox(
            param_frame, 
            from_=0, 
            to=100, 
            textvariable=self.overlap_var,
            width=20
        ).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Checkbutton(
            param_frame,
            text="启用数据脱敏 Enable Data Masking",
            variable=self.mask_var
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
        
    def _create_analysis_tab(self, parent):
        """Create analysis tab.
        创建分析标签页。
        
        Args:
            parent: Parent frame
        """
        # File Selection Section
        file_frame = ttk.LabelFrame(parent, text="日志文件 Log File", padding=10)
        file_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(file_frame, text="文件路径 File Path:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(file_frame, textvariable=self.log_file_path, width=50).grid(
            row=0, column=1, sticky='ew', padx=5, pady=5
        )
        ttk.Button(file_frame, text="选择文件 Browse", command=self._browse_file).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # Drag and drop hint
        drop_label = ttk.Label(
            file_frame, 
            text="提示：您可以拖拽文件到窗口 Hint: You can drag and drop log files here",
            foreground="gray"
        )
        drop_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Specification Document Section
        spec_frame = ttk.LabelFrame(parent, text="规范文档 Specification Document", padding=10)
        spec_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        ttk.Label(
            spec_frame, 
            text="在此输入日志规范说明（各个日志字段的含义）\nEnter log specification (meaning of log fields):"
        ).pack(anchor='w', pady=5)
        
        self.spec_text = scrolledtext.ScrolledText(spec_frame, height=10, wrap=tk.WORD)
        self.spec_text.pack(fill='both', expand=True, pady=5)
        self.spec_text.insert(
            '1.0',
            "# 日志规范示例 Log Specification Example\n\n"
            "请在此输入您的日志规范文档，说明日志中各个字段和标签的含义。\n"
            "Please enter your log specification document here, explaining the meaning of fields and tags in the logs.\n\n"
            "例如 Example:\n"
            "- AudioFlinger: 音频混音器相关日志 Audio mixer related logs\n"
            "- Track started: 表示音频轨道开始播放 Indicates audio track started playing\n"
            "- Stream active: 音频流处于活动状态 Audio stream is active\n"
        )
        
        # Action Buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        self.analyze_btn = ttk.Button(
            action_frame,
            text="开始分析 Start Analysis",
            command=self._start_analysis
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(
            action_frame,
            text="停止 Stop",
            command=self._stop_analysis,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # Progress Section
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="就绪 Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(side='left', padx=5)
        
        self.progressbar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progressbar.pack(side='left', fill='x', expand=True, padx=5)
        
    def _create_results_tab(self, parent):
        """Create results tab.
        创建结果标签页。
        
        Args:
            parent: Parent frame
        """
        # Results display
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        ttk.Label(results_frame, text="分析结果 Analysis Results:", font=('TkDefaultFont', 10, 'bold')).pack(
            anchor='w', pady=5
        )
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill='both', expand=True, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="保存结果 Save Results", command=self._save_results).pack(
            side='left', padx=5
        )
        ttk.Button(button_frame, text="清除 Clear", command=self._clear_results).pack(
            side='left', padx=5
        )
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality.
        设置拖拽功能。
        """
        # Note: Basic tkinter doesn't support drag-drop on Windows directly
        # This would require tkinterdnd2 library for full functionality
        # For now, we'll add a note in the GUI
        pass
    
    def _load_config(self):
        """Load saved configuration.
        加载保存的配置。
        """
        config_path = Path.home() / ".mtk_log_inspector_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.api_key_var.set(config.get('api_key', ''))
                    self.model_var.set(config.get('model', 'qwen-plus'))
            except Exception:
                pass
    
    def _save_api_key(self):
        """Save API key to configuration file.
        保存API密钥到配置文件。
        """
        config_path = Path.home() / ".mtk_log_inspector_config.json"
        try:
            config = {
                'api_key': self.api_key_var.get(),
                'model': self.model_var.get()
            }
            with open(config_path, 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("成功 Success", "API密钥已保存 API key saved successfully")
        except Exception as e:
            messagebox.showerror("错误 Error", f"保存失败 Save failed: {str(e)}")
    
    def _browse_file(self):
        """Open file browser to select log file.
        打开文件浏览器选择日志文件。
        """
        filename = filedialog.askopenfilename(
            title="选择日志文件 Select Log File",
            filetypes=[
                ("Log files", "*.log *.txt"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.log_file_path.set(filename)
    
    def _start_analysis(self):
        """Start log analysis in a separate thread.
        在单独的线程中开始日志分析。
        """
        # Validate inputs
        if not self.api_key_var.get():
            messagebox.showerror("错误 Error", "请先配置API密钥 Please configure API key first")
            return
        
        if not self.log_file_path.get() or not Path(self.log_file_path.get()).exists():
            messagebox.showerror("错误 Error", "请选择有效的日志文件 Please select a valid log file")
            return
        
        # Disable analyze button and enable stop button
        self.analyze_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progressbar.start()
        
        # Get specification document
        self.spec_doc_text = self.spec_text.get('1.0', tk.END).strip()
        
        # Clear previous results
        self.results_text.delete('1.0', tk.END)
        
        # Start analysis in a separate thread
        self.analysis_thread = threading.Thread(target=self._run_analysis, daemon=True)
        self.analysis_thread.start()
    
    def _stop_analysis(self):
        """Stop the ongoing analysis.
        停止正在进行的分析。
        """
        # Note: Stopping a running thread is complex and not recommended
        # This is a placeholder for future implementation
        self.progress_var.set("正在停止... Stopping...")
        # In a real implementation, you would need to implement proper cancellation
    
    def _run_analysis(self):
        """Run the actual analysis (called in separate thread).
        运行实际的分析（在单独的线程中调用）。
        """
        try:
            self._update_progress("初始化组件... Initializing components...")
            
            # Set API key as environment variable temporarily
            os.environ['BAILIAN_API_KEY'] = self.api_key_var.get()
            
            # Initialize components
            client = BailianClient(model=self.model_var.get())
            parser = LogParser()
            chunker = LogChunker(
                chunk_size=self.chunk_size_var.get(),
                overlap=self.overlap_var.get()
            )
            analyzer = WindowAnalyzer()
            masker = DataMasker() if self.mask_var.get() else None
            
            # Load system prompt
            self._update_progress("加载系统提示词... Loading system prompt...")
            system_prompt = self._load_system_prompt()
            
            # Add specification document to system prompt if provided
            if self.spec_doc_text and len(self.spec_doc_text) > 50:
                system_prompt += f"\n\n## 日志规范文档 Log Specification Document\n\n{self.spec_doc_text}"
            
            # Parse and filter log
            self._update_progress("解析日志文件... Parsing log file...")
            log_path = Path(self.log_file_path.get())
            lines = parser.parse_and_filter(str(log_path))
            self._update_progress(f"找到 {len(lines)} 条音频相关日志 Found {len(lines)} audio-related lines")
            
            # Apply masking if needed
            if masker:
                self._update_progress("应用数据脱敏... Applying data masking...")
                lines = masker.mask_lines(lines)
            
            # Chunk the lines
            windows = chunker.chunk_lines(lines)
            self._update_progress(f"分割为 {len(windows)} 个窗口 Split into {len(windows)} windows")
            
            # Analyze each window
            window_results = []
            for window_idx, window_lines in windows:
                self._update_progress(
                    f"分析窗口 {window_idx + 1}/{len(windows)} Analyzing window {window_idx + 1}/{len(windows)}..."
                )
                
                log_content = "\n".join(window_lines)
                
                try:
                    result = client.analyze_log_window(system_prompt, log_content)
                    result["window_idx"] = window_idx
                    window_results.append(result)
                    
                    self._append_result(
                        f"窗口 Window {window_idx + 1}: {result['final_state']} "
                        f"(置信度 confidence: {result['confidence']:.2f})\n"
                    )
                except Exception as e:
                    window_results.append({
                        "window_idx": window_idx,
                        "final_state": "UNKNOWN",
                        "confidence": 0.0,
                        "reason": f"Analysis failed: {str(e)}",
                        "evidence": [],
                        "next_actions": ["Retry analysis"]
                    })
                    self._append_result(f"窗口 Window {window_idx + 1}: 错误 Error: {str(e)}\n")
            
            # Merge segments
            self._update_progress("合并片段... Merging segments...")
            segments = analyzer.merge_windows(window_results)
            
            # Generate report
            self._update_progress("生成报告... Generating report...")
            metadata = {
                "log_file": str(log_path.absolute()),
                "timestamp": datetime.now().isoformat(),
                "chunk_size": self.chunk_size_var.get(),
                "overlap": self.overlap_var.get(),
                "model": self.model_var.get(),
                "masking_enabled": self.mask_var.get(),
                "total_windows": len(windows),
                "total_lines": len(lines)
            }
            
            report = analyzer.generate_report(segments, window_results, metadata)
            markdown_content = analyzer.generate_markdown_report(segments, metadata)
            
            # Store results
            self.analysis_report = report
            self.markdown_report = markdown_content
            
            # Display results
            self._append_result("\n" + "="*50 + "\n")
            self._append_result(markdown_content)
            
            self._update_progress("✓ 分析完成！ Analysis complete!")
            messagebox.showinfo("完成 Complete", "日志分析已完成 Log analysis completed successfully!")
            
        except Exception as e:
            error_msg = f"分析错误 Analysis error: {str(e)}"
            self._update_progress(error_msg)
            self._append_result(f"\n错误 Error: {str(e)}\n")
            messagebox.showerror("错误 Error", error_msg)
        
        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
            self.root.after(0, lambda: self.progressbar.stop())
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from docs/prompt.md.
        从docs/prompt.md加载系统提示词。
        
        Returns:
            System prompt content
        """
        current_dir = Path(__file__).parent.parent
        prompt_path = current_dir / "docs" / "prompt.md"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"System prompt not found at {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _update_progress(self, message: str):
        """Update progress message.
        更新进度消息。
        
        Args:
            message: Progress message
        """
        self.root.after(0, lambda: self.progress_var.set(message))
    
    def _append_result(self, text: str):
        """Append text to results display.
        向结果显示添加文本。
        
        Args:
            text: Text to append
        """
        self.root.after(0, lambda: self.results_text.insert(tk.END, text))
        self.root.after(0, lambda: self.results_text.see(tk.END))
    
    def _save_results(self):
        """Save analysis results to file.
        保存分析结果到文件。
        """
        if not hasattr(self, 'analysis_report'):
            messagebox.showwarning("警告 Warning", "没有可保存的结果 No results to save")
            return
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="选择输出目录 Select Output Directory")
        if not output_dir:
            return
        
        output_path = Path(output_dir)
        
        try:
            # Save JSON report
            json_path = output_path / "report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_report, f, indent=2, ensure_ascii=False)
            
            # Save Markdown report
            md_path = output_path / "report.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(self.markdown_report)
            
            messagebox.showinfo(
                "成功 Success",
                f"结果已保存到 Results saved to:\n{json_path}\n{md_path}"
            )
        except Exception as e:
            messagebox.showerror("错误 Error", f"保存失败 Save failed: {str(e)}")
    
    def _clear_results(self):
        """Clear results display.
        清除结果显示。
        """
        self.results_text.delete('1.0', tk.END)


def main():
    """Main entry point for GUI application.
    GUI应用程序的主入口点。
    """
    root = tk.Tk()
    app = LogInspectorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
