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

#ifndef AUDIO_DUMP_MANAGER_H
#define AUDIO_DUMP_MANAGER_H

#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <atomic>
#include <thread>
#include <fstream>

#define LOG_TAG "AudioDumpManager"
#include <log/log.h>
#include <cutils/properties.h>

namespace android {
namespace audio {

/**
 * Audio stream type enumeration
 */
enum class AudioStreamType {
    STREAM_OUT,  // Playback stream
    STREAM_IN    // Recording stream
};

// Forward declaration
class StreamDumper;

/**
 * AudioDumpManager - Core manager for audio dump automation (Singleton)
 *
 * Features:
 * - Monitors system properties for dump enable/disable
 * - Manages dump directory /data/vendor/audio_dump/
 * - Maintains completed file queue (memory queue + .queue text file)
 * - Notifies via logcat: ALOGI("AUDIO_DUMP_READY: filename")
 * - Creates StreamDumper instances for individual audio streams
 */
class AudioDumpManager {
public:
    /**
     * Get singleton instance
     */
    static AudioDumpManager& GetInstance();

    /**
     * Delete copy constructor and assignment operator
     */
    AudioDumpManager(const AudioDumpManager&) = delete;
    AudioDumpManager& operator=(const AudioDumpManager&) = delete;

    /**
     * Initialize the manager
     * @return true if initialization successful, false otherwise
     */
    bool Initialize();

    /**
     * Shutdown the manager
     */
    void Shutdown();

    /**
     * Check if streamout dump is enabled
     * @return true if vendor.streamout.pcm.dump=1
     */
    bool IsStreamOutDumpEnabled() const;

    /**
     * Check if streamin dump is enabled
     * @return true if vendor.streamin.pcm.dump=1
     */
    bool IsStreamInDumpEnabled() const;

    /**
     * Create a StreamDumper for the specified stream type
     * @param type The audio stream type (STREAM_OUT or STREAM_IN)
     * @return Unique pointer to StreamDumper, nullptr if dump not enabled or error
     */
    std::unique_ptr<StreamDumper> CreateStreamDumper(AudioStreamType type);

    /**
     * Called by StreamDumper when a dump file is completed
     * @param filename The completed dump file name (not full path)
     */
    void OnDumpFileCompleted(const std::string& filename);

    /**
     * Get the dump directory path
     * @return The dump directory path
     */
    const std::string& GetDumpDirectory() const { return mDumpDirectory; }

    /**
     * Get the queue file path
     * @return The queue file path
     */
    const std::string& GetQueueFilePath() const { return mQueueFilePath; }

private:
    /**
     * Private constructor for singleton
     */
    AudioDumpManager();

    /**
     * Destructor
     */
    ~AudioDumpManager();

    /**
     * Ensure dump directory exists
     * @return true if directory exists or was created
     */
    bool EnsureDumpDirectory();

    /**
     * Append filename to .queue file
     * @param filename The filename to append
     * @return true if successful
     */
    bool AppendToQueueFile(const std::string& filename);

    /**
     * Generate unique counter for file naming
     * @return Next counter value
     */
    uint32_t GetNextCounter();

    // Member variables
    std::string mDumpDirectory;       // /data/vendor/audio_dump/
    std::string mQueueFilePath;       // /data/vendor/audio_dump/.queue

    std::mutex mMutex;                // Protects shared data
    std::queue<std::string> mCompletedFiles;  // Queue of completed files
    std::atomic<uint32_t> mFileCounter{0};    // Counter for unique file names

    bool mInitialized;

    // System property names
    static constexpr const char* PROP_STREAMOUT_DUMP = "vendor.streamout.pcm.dump";
    static constexpr const char* PROP_STREAMIN_DUMP = "vendor.streamin.pcm.dump";

    // Default dump directory
    static constexpr const char* DEFAULT_DUMP_DIR = "/data/vendor/audio_dump/";
    static constexpr const char* QUEUE_FILE_NAME = ".queue";
};

} // namespace audio
} // namespace android

#endif // AUDIO_DUMP_MANAGER_H
