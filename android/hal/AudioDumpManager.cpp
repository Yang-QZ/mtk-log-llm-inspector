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

#define LOG_TAG "AudioDumpManager"

#include "AudioDumpManager.h"
#include "StreamDumper.h"

#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <ctime>

namespace android {
namespace audio {

AudioDumpManager& AudioDumpManager::GetInstance() {
    static AudioDumpManager instance;
    return instance;
}

AudioDumpManager::AudioDumpManager()
    : mDumpDirectory(DEFAULT_DUMP_DIR),
      mQueueFilePath(std::string(DEFAULT_DUMP_DIR) + QUEUE_FILE_NAME),
      mInitialized(false) {
    ALOGD("AudioDumpManager constructed");
}

AudioDumpManager::~AudioDumpManager() {
    Shutdown();
    ALOGD("AudioDumpManager destroyed");
}

bool AudioDumpManager::Initialize() {
    std::lock_guard<std::mutex> lock(mMutex);

    if (mInitialized) {
        ALOGW("AudioDumpManager already initialized");
        return true;
    }

    // Ensure dump directory exists
    if (!EnsureDumpDirectory()) {
        ALOGE("Failed to create dump directory: %s", mDumpDirectory.c_str());
        return false;
    }

    mInitialized = true;
    ALOGI("AudioDumpManager initialized, dump directory: %s", mDumpDirectory.c_str());
    return true;
}

void AudioDumpManager::Shutdown() {
    std::lock_guard<std::mutex> lock(mMutex);

    if (!mInitialized) {
        return;
    }

    // Clear the queue
    while (!mCompletedFiles.empty()) {
        mCompletedFiles.pop();
    }

    mInitialized = false;
    ALOGI("AudioDumpManager shutdown");
}

bool AudioDumpManager::IsStreamOutDumpEnabled() const {
    char value[PROPERTY_VALUE_MAX] = {0};
    property_get(PROP_STREAMOUT_DUMP, value, "0");
    return (strcmp(value, "1") == 0);
}

bool AudioDumpManager::IsStreamInDumpEnabled() const {
    char value[PROPERTY_VALUE_MAX] = {0};
    property_get(PROP_STREAMIN_DUMP, value, "0");
    return (strcmp(value, "1") == 0);
}

std::unique_ptr<StreamDumper> AudioDumpManager::CreateStreamDumper(AudioStreamType type) {
    // Check if dump is enabled for this stream type
    bool enabled = (type == AudioStreamType::STREAM_OUT)
                   ? IsStreamOutDumpEnabled()
                   : IsStreamInDumpEnabled();

    if (!enabled) {
        ALOGV("Dump not enabled for stream type %d", static_cast<int>(type));
        return nullptr;
    }

    // Ensure manager is initialized
    if (!mInitialized) {
        if (!Initialize()) {
            ALOGE("Failed to initialize AudioDumpManager");
            return nullptr;
        }
    }

    // Generate unique counter
    uint32_t counter = GetNextCounter();

    // Get timestamp
    time_t now = time(nullptr);
    struct tm* timeinfo = localtime(&now);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y%m%d_%H%M%S", timeinfo);

    // Create StreamDumper
    auto dumper = std::make_unique<StreamDumper>(type, mDumpDirectory, timestamp, counter);

    ALOGI("Created StreamDumper for type %d with counter %u",
          static_cast<int>(type), counter);

    return dumper;
}

void AudioDumpManager::OnDumpFileCompleted(const std::string& filename) {
    std::lock_guard<std::mutex> lock(mMutex);

    // Add to memory queue
    mCompletedFiles.push(filename);

    // Append to .queue file
    if (!AppendToQueueFile(filename)) {
        ALOGW("Failed to append to queue file: %s", filename.c_str());
    }

    // Notify via logcat - this is the key notification for Windows monitor
    ALOGI("AUDIO_DUMP_READY: %s", filename.c_str());

    ALOGD("Dump file completed and queued: %s", filename.c_str());
}

bool AudioDumpManager::EnsureDumpDirectory() {
    struct stat st;
    if (stat(mDumpDirectory.c_str(), &st) == 0) {
        if (S_ISDIR(st.st_mode)) {
            return true;
        }
        ALOGE("%s exists but is not a directory", mDumpDirectory.c_str());
        return false;
    }

    // Directory doesn't exist, try to create it
    if (mkdir(mDumpDirectory.c_str(), 0755) != 0) {
        ALOGE("Failed to create directory %s: %s",
              mDumpDirectory.c_str(), strerror(errno));
        return false;
    }

    ALOGI("Created dump directory: %s", mDumpDirectory.c_str());
    return true;
}

bool AudioDumpManager::AppendToQueueFile(const std::string& filename) {
    std::ofstream file(mQueueFilePath, std::ios::app);
    if (!file.is_open()) {
        ALOGE("Failed to open queue file: %s", mQueueFilePath.c_str());
        return false;
    }

    file << filename << "\n";
    file.close();

    return true;
}

uint32_t AudioDumpManager::GetNextCounter() {
    return mFileCounter.fetch_add(1, std::memory_order_relaxed);
}

} // namespace audio
} // namespace android
