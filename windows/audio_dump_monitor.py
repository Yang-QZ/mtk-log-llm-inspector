#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Dump Monitor for Windows

This module monitors Android device for audio dump files and automatically
pulls them to local storage. It uses two mechanisms:
1. Real-time logcat monitoring for immediate notification
2. Periodic queue file polling as backup mechanism

Features:
- Real-time logcat listener for AUDIO_DUMP_READY notifications
- Backup polling mechanism via .queue file
- Concurrent file pulling with multiple worker threads
- Statistics reporting
- Duplicate prevention
- Configurable parameters

Usage:
    python audio_dump_monitor.py
    python audio_dump_monitor.py --config custom_config.json
"""

import argparse
import json
import logging
import os
import queue
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Set


class Config:
    """Configuration manager for audio dump monitor."""

    # Default configuration values
    DEFAULTS = {
        "device_dump_path": "/data/vendor/audio_dump/",
        "device_queue_file": "/data/vendor/audio_dump/.queue",
        "local_save_path": "./audio_dumps",
        "use_logcat": True,
        "poll_interval": 10,  # seconds
        "pull_workers": 2,
        "stats_interval": 60,  # seconds
        "adb_timeout": 30,  # seconds
        "max_retries": 3,
        "retry_delay": 2,  # seconds
        "log_file": "audio_dump_monitor.log",
        "log_level": "INFO",
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to JSON configuration file
        """
        self._config = self.DEFAULTS.copy()

        if config_file and os.path.exists(config_file):
            self._load_config(config_file)

    def _load_config(self, config_file: str) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                self._config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load config file: {e}")

    def __getattr__(self, name: str):
        """Get configuration value by attribute access."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._config.get(name)

    def get(self, key: str, default=None):
        """Get configuration value with optional default."""
        return self._config.get(key, default)


@dataclass
class Statistics:
    """Statistics tracker for audio dump operations."""

    files_pulled: int = 0
    files_failed: int = 0
    bytes_transferred: int = 0
    start_time: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_success(self, file_size: int) -> None:
        """Record a successful file pull."""
        with self._lock:
            self.files_pulled += 1
            self.bytes_transferred += file_size

    def add_failure(self) -> None:
        """Record a failed file pull."""
        with self._lock:
            self.files_failed += 1

    def get_summary(self) -> str:
        """Get formatted summary string."""
        with self._lock:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)

            if elapsed > 0:
                speed = self.bytes_transferred / elapsed
                speed_str = self._format_size(speed) + "/s"
            else:
                speed_str = "N/A"

            return (
                f"Statistics Summary:\n"
                f"  Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
                f"  Files Pulled: {self.files_pulled}\n"
                f"  Files Failed: {self.files_failed}\n"
                f"  Total Transferred: {self._format_size(self.bytes_transferred)}\n"
                f"  Average Speed: {speed_str}"
            )

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size to human readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


class AudioDumpMonitor:
    """
    Main audio dump monitor class.

    Monitors Android device for completed audio dump files and
    pulls them to local storage.
    """

    # Regex pattern to match AUDIO_DUMP_READY logcat messages
    LOGCAT_PATTERN = re.compile(r"AUDIO_DUMP_READY:\s+(\S+)")

    def __init__(self, config: Config):
        """
        Initialize the monitor.

        Args:
            config: Configuration object
        """
        self.config = config
        self.stats = Statistics()
        self.logger = self._setup_logging()

        # Task queue for files to pull
        self.task_queue: queue.Queue = queue.Queue()

        # Set of processed files to prevent duplicates
        self.processed_files: Set[str] = set()
        self.processed_lock = threading.Lock()

        # Control flags
        self.running = False
        self.threads: list = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging with file and console handlers."""
        logger = logging.getLogger("AudioDumpMonitor")
        logger.setLevel(getattr(logging, self.config.log_level, logging.INFO))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        # File handler
        log_file = self.config.log_file
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        return logger

    def _run_adb_command(
        self, args: list, timeout: Optional[int] = None, check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run an adb command.

        Args:
            args: Command arguments (without 'adb' prefix)
            timeout: Command timeout in seconds
            check: Whether to raise exception on failure

        Returns:
            CompletedProcess result
        """
        cmd = ["adb"] + args
        timeout = timeout or self.config.adb_timeout
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )

    def _is_file_processed(self, filename: str) -> bool:
        """Check if file has already been processed."""
        with self.processed_lock:
            return filename in self.processed_files

    def _mark_file_processed(self, filename: str) -> None:
        """Mark file as processed."""
        with self.processed_lock:
            self.processed_files.add(filename)

    def logcat_listener_thread(self) -> None:
        """
        Thread function to listen for logcat AUDIO_DUMP_READY messages.

        Uses subprocess.Popen to stream logcat output in real-time.
        """
        self.logger.info("Logcat listener started")

        while self.running:
            try:
                # Start logcat process
                process = subprocess.Popen(
                    ["adb", "logcat", "-s", "AudioDumpManager:I", "-v", "raw"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )

                # Read lines from logcat
                for line in iter(process.stdout.readline, ""):
                    if not self.running:
                        break

                    # Match AUDIO_DUMP_READY pattern
                    match = self.LOGCAT_PATTERN.search(line)
                    if match:
                        filename = match.group(1)
                        self.logger.debug(f"Logcat detected: {filename}")

                        if not self._is_file_processed(filename):
                            self._mark_file_processed(filename)
                            self.task_queue.put(filename)
                            self.logger.info(f"Queued from logcat: {filename}")

                process.terminate()
                process.wait()

            except subprocess.SubprocessError as e:
                self.logger.error(f"Logcat error: {e}")
                if self.running:
                    time.sleep(5)  # Wait before retry

        self.logger.info("Logcat listener stopped")

    def poll_queue_thread(self) -> None:
        """
        Thread function to periodically poll .queue file on device.

        This is a backup mechanism in case logcat messages are missed.
        """
        self.logger.info("Queue poller started")

        while self.running:
            try:
                # Read .queue file from device
                result = self._run_adb_command(
                    ["shell", f"cat {self.config.device_queue_file}"],
                    check=False,
                )

                if result.returncode == 0 and result.stdout.strip():
                    files = result.stdout.strip().split("\n")

                    for filename in files:
                        filename = filename.strip()
                        if filename and not self._is_file_processed(filename):
                            self._mark_file_processed(filename)
                            self.task_queue.put(filename)
                            self.logger.info(f"Queued from poll: {filename}")

            except subprocess.TimeoutExpired:
                self.logger.warning("Queue poll timeout")
            except subprocess.SubprocessError as e:
                self.logger.error(f"Queue poll error: {e}")

            # Wait for next poll interval
            for _ in range(int(self.config.poll_interval)):
                if not self.running:
                    break
                time.sleep(1)

        self.logger.info("Queue poller stopped")

    def pull_worker_thread(self, worker_id: int) -> None:
        """
        Worker thread to pull files from device.

        Args:
            worker_id: Worker thread identifier
        """
        self.logger.info(f"Pull worker {worker_id} started")

        while self.running:
            try:
                # Get filename from queue with timeout
                filename = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                success = self.pull_and_delete(filename)
                if success:
                    self.logger.info(f"Worker {worker_id}: Pulled {filename}")
                else:
                    self.logger.warning(f"Worker {worker_id}: Failed {filename}")

            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")

            finally:
                self.task_queue.task_done()

        self.logger.info(f"Pull worker {worker_id} stopped")

    def pull_and_delete(self, filename: str) -> bool:
        """
        Pull file from device and delete it.

        Args:
            filename: Name of file to pull

        Returns:
            True if successful, False otherwise
        """
        device_path = self.config.device_dump_path + filename
        local_dir = Path(self.config.local_save_path)
        local_path = local_dir / filename

        # Ensure local directory exists
        local_dir.mkdir(parents=True, exist_ok=True)

        # Retry loop
        for attempt in range(self.config.max_retries):
            try:
                # Pull file from device
                result = self._run_adb_command(
                    ["pull", device_path, str(local_path)],
                    check=True,
                )

                # Get file size
                file_size = local_path.stat().st_size if local_path.exists() else 0

                # Delete file and remove from .queue on device
                queue_file = self.config.device_queue_file
                delete_cmd = f"rm {device_path} && sed -i '/{filename}/d' {queue_file}"
                self._run_adb_command(["shell", delete_cmd], check=False)

                # Record statistics
                self.stats.add_success(file_size)
                return True

            except subprocess.CalledProcessError as e:
                self.logger.warning(
                    f"Pull attempt {attempt + 1} failed for {filename}: {e}"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)

            except Exception as e:
                self.logger.error(f"Unexpected error pulling {filename}: {e}")
                break

        self.stats.add_failure()
        return False

    def stats_reporter_thread(self) -> None:
        """Thread function to periodically report statistics."""
        self.logger.info("Stats reporter started")

        while self.running:
            # Wait for stats interval
            for _ in range(int(self.config.stats_interval)):
                if not self.running:
                    break
                time.sleep(1)

            if self.running:
                summary = self.stats.get_summary()
                self.logger.info(f"\n{summary}")
                print(f"\n{summary}\n")

        self.logger.info("Stats reporter stopped")

    def check_adb_device(self) -> bool:
        """
        Check if adb device is connected.

        Returns:
            True if device is connected, False otherwise
        """
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Check if any device is listed
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if "\tdevice" in line:
                    return True

            return False

        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def run(self) -> None:
        """Main loop to start all monitoring threads."""
        self.logger.info("=" * 50)
        self.logger.info("Audio Dump Monitor Starting")
        self.logger.info("=" * 50)

        # Check adb device
        if not self.check_adb_device():
            self.logger.error("No adb device connected!")
            print("Error: No adb device connected. Please check device connection.")
            return

        self.logger.info("Device connected")
        self.running = True

        # Start logcat listener thread (if enabled)
        if self.config.use_logcat:
            logcat_thread = threading.Thread(
                target=self.logcat_listener_thread,
                name="LogcatListener",
                daemon=True,
            )
            logcat_thread.start()
            self.threads.append(logcat_thread)

        # Start queue poller thread
        poll_thread = threading.Thread(
            target=self.poll_queue_thread,
            name="QueuePoller",
            daemon=True,
        )
        poll_thread.start()
        self.threads.append(poll_thread)

        # Start pull worker threads
        for i in range(self.config.pull_workers):
            worker_thread = threading.Thread(
                target=self.pull_worker_thread,
                args=(i,),
                name=f"PullWorker-{i}",
                daemon=True,
            )
            worker_thread.start()
            self.threads.append(worker_thread)

        # Start stats reporter thread
        stats_thread = threading.Thread(
            target=self.stats_reporter_thread,
            name="StatsReporter",
            daemon=True,
        )
        stats_thread.start()
        self.threads.append(stats_thread)

        self.logger.info(f"Started {len(self.threads)} threads")
        print(f"Monitor running. Press Ctrl+C to stop.")
        print(f"Saving files to: {os.path.abspath(self.config.local_save_path)}")

        # Main loop - wait for interrupt
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            print("\nStopping...")

        self.stop()

    def stop(self) -> None:
        """Stop all monitoring threads."""
        self.logger.info("Stopping monitor...")
        self.running = False

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)

        # Print final statistics
        summary = self.stats.get_summary()
        self.logger.info(f"Final {summary}")
        print(f"\n{summary}")

        self.logger.info("Monitor stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audio Dump Monitor - Automatically pull audio dumps from Android device"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Override local save path",
    )

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

    # Override output path if specified
    if args.output:
        config._config["local_save_path"] = args.output

    # Create and run monitor
    monitor = AudioDumpMonitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
