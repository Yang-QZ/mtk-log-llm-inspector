/*
 * Copyright (C) 2024 Audio Dump Automation System
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef STREAM_DUMPER_H
#define STREAM_DUMPER_H

#include "AudioDumpManager.h"

#include <cstdint>
#include <string>
#include <mutex>
#include <fstream>
#include <vector>
#include <memory>

namespace android {
namespace audio {

/**
 * StreamDumper - Stream processor for individual audio stream dump
 *
 * Features:
 * - Manages dump files for a single audio stream
 * - File naming: audio_{streamout/streamin}_{timestamp}_{counter}.pcm
 * - Uses .tmp suffix during writing, renames when complete
 * - Automatic file switching: closes current file and creates new one at 100MB
 * - Optimized: 256KB buffer, flush every 10MB
 *
 * Provides:
 * - WriteData(buffer, size): Write audio data to dump file
 * - ForceClose(): Force close current file
 */
class StreamDumper {
public:
    /**
     * Constructor
     * @param type The audio stream type
     * @param dumpDir The dump directory path
     * @param timestamp Base timestamp for file naming
     * @param baseCounter Base counter for file naming
     */
    StreamDumper(AudioStreamType type,
                 const std::string& dumpDir,
                 const std::string& timestamp,
                 uint32_t baseCounter);

    /**
     * Destructor - closes any open file
     */
    ~StreamDumper();

    /**
     * Disable copy
     */
    StreamDumper(const StreamDumper&) = delete;
    StreamDumper& operator=(const StreamDumper&) = delete;

    /**
     * Write audio data to dump file
     * @param buffer Pointer to audio data
     * @param size Size of audio data in bytes
     * @return Number of bytes written, or -1 on error
     */
    ssize_t WriteData(const void* buffer, size_t size);

    /**
     * Force close the current dump file
     * The file will be renamed from .tmp to .pcm and notification sent
     */
    void ForceClose();

    /**
     * Check if dumper is in valid state
     * @return true if dumper is ready to write
     */
    bool IsValid() const { return mIsValid; }

    /**
     * Get current file size
     * @return Current file size in bytes
     */
    size_t GetCurrentFileSize() const { return mCurrentFileSize; }

    /**
     * Get total bytes written across all files
     * @return Total bytes written
     */
    size_t GetTotalBytesWritten() const { return mTotalBytesWritten; }

    /**
     * Get number of files created
     * @return Number of files created
     */
    uint32_t GetFileCount() const { return mFileCount; }

private:
    /**
     * Open a new dump file
     * @return true if successful
     */
    bool OpenNewFile();

    /**
     * Close current file and notify manager
     * @param complete Whether the file is complete (not forced closed due to error)
     */
    void CloseCurrentFile(bool complete = true);

    /**
     * Flush buffer to file
     * @return true if successful
     */
    bool FlushBuffer();

    /**
     * Generate filename for current file
     * @param withTmp If true, add .tmp suffix
     * @return Generated filename
     */
    std::string GenerateFilename(bool withTmp) const;

    /**
     * Get stream type string for filename
     * @return "streamout" or "streamin"
     */
    const char* GetStreamTypeString() const;

    // Configuration constants
    static constexpr size_t BUFFER_SIZE = 256 * 1024;          // 256KB buffer
    static constexpr size_t FLUSH_THRESHOLD = 10 * 1024 * 1024; // Flush every 10MB
    static constexpr size_t MAX_FILE_SIZE = 100 * 1024 * 1024;  // 100MB max file size

    // Member variables
    AudioStreamType mType;            // Stream type
    std::string mDumpDirectory;       // Dump directory
    std::string mTimestamp;           // Base timestamp
    uint32_t mBaseCounter;            // Base counter from manager
    uint32_t mFileIndex;              // Current file index (for multiple files)

    std::mutex mMutex;                // Protects file operations
    std::ofstream mFile;              // Current output file
    std::string mCurrentFilePath;     // Current file path (with .tmp)
    std::string mCurrentFilename;     // Current filename (without path)

    std::vector<char> mBuffer;        // Write buffer
    size_t mBufferOffset;             // Current position in buffer
    size_t mCurrentFileSize;          // Bytes written to current file
    size_t mBytesSinceFlush;          // Bytes written since last flush
    size_t mTotalBytesWritten;        // Total bytes across all files

    uint32_t mFileCount;              // Number of files created
    bool mIsValid;                    // Valid state flag
};

} // namespace audio
} // namespace android

#endif // STREAM_DUMPER_H
