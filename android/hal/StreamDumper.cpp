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

#define LOG_TAG "StreamDumper"

#include "StreamDumper.h"

#include <log/log.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <algorithm>

namespace android {
namespace audio {

StreamDumper::StreamDumper(AudioStreamType type,
                           const std::string& dumpDir,
                           const std::string& timestamp,
                           uint32_t baseCounter)
    : mType(type),
      mDumpDirectory(dumpDir),
      mTimestamp(timestamp),
      mBaseCounter(baseCounter),
      mFileIndex(0),
      mBufferOffset(0),
      mCurrentFileSize(0),
      mBytesSinceFlush(0),
      mTotalBytesWritten(0),
      mFileCount(0),
      mIsValid(false) {

    // Allocate buffer
    mBuffer.resize(BUFFER_SIZE);

    // Open first file
    if (OpenNewFile()) {
        mIsValid = true;
        ALOGI("StreamDumper created for %s, first file: %s",
              GetStreamTypeString(), mCurrentFilename.c_str());
    } else {
        ALOGE("StreamDumper failed to create initial file");
    }
}

StreamDumper::~StreamDumper() {
    ForceClose();
    ALOGD("StreamDumper destroyed, total files: %u, total bytes: %zu",
          mFileCount, mTotalBytesWritten);
}

ssize_t StreamDumper::WriteData(const void* buffer, size_t size) {
    if (!mIsValid || buffer == nullptr || size == 0) {
        return -1;
    }

    std::lock_guard<std::mutex> lock(mMutex);

    const char* data = static_cast<const char*>(buffer);
    size_t bytesRemaining = size;
    size_t totalWritten = 0;

    while (bytesRemaining > 0) {
        // Check if we need to switch to a new file
        if (mCurrentFileSize >= MAX_FILE_SIZE) {
            ALOGI("File size reached %zuMB, switching to new file",
                  MAX_FILE_SIZE / (1024 * 1024));
            CloseCurrentFile(true);
            if (!OpenNewFile()) {
                ALOGE("Failed to open new file after size limit");
                mIsValid = false;
                return -1;
            }
        }

        // Calculate how much we can write to buffer
        size_t spaceInBuffer = BUFFER_SIZE - mBufferOffset;
        size_t bytesToCopy = std::min(bytesRemaining, spaceInBuffer);

        // Copy to buffer
        memcpy(mBuffer.data() + mBufferOffset, data, bytesToCopy);
        mBufferOffset += bytesToCopy;
        data += bytesToCopy;
        bytesRemaining -= bytesToCopy;
        totalWritten += bytesToCopy;

        // Flush if buffer is full
        if (mBufferOffset >= BUFFER_SIZE) {
            if (!FlushBuffer()) {
                ALOGE("Failed to flush buffer");
                mIsValid = false;
                return -1;
            }
        }

        // Check if we should flush based on bytes since last flush
        if (mBytesSinceFlush >= FLUSH_THRESHOLD) {
            mFile.flush();
            mBytesSinceFlush = 0;
            ALOGV("Periodic flush at %zuMB", mCurrentFileSize / (1024 * 1024));
        }
    }

    return static_cast<ssize_t>(totalWritten);
}

void StreamDumper::ForceClose() {
    std::lock_guard<std::mutex> lock(mMutex);

    if (mFile.is_open()) {
        // Flush any remaining data in buffer
        if (mBufferOffset > 0) {
            mFile.write(mBuffer.data(), mBufferOffset);
            mCurrentFileSize += mBufferOffset;
            mTotalBytesWritten += mBufferOffset;
            mBufferOffset = 0;
        }

        CloseCurrentFile(true);
    }

    mIsValid = false;
}

bool StreamDumper::OpenNewFile() {
    // Generate filename with .tmp suffix
    mCurrentFilename = GenerateFilename(false);
    std::string tmpFilename = GenerateFilename(true);
    mCurrentFilePath = mDumpDirectory + tmpFilename;

    // Open file
    mFile.open(mCurrentFilePath, std::ios::binary | std::ios::trunc);
    if (!mFile.is_open()) {
        ALOGE("Failed to open dump file: %s", mCurrentFilePath.c_str());
        return false;
    }

    // Reset counters for new file
    mCurrentFileSize = 0;
    mBytesSinceFlush = 0;
    mBufferOffset = 0;
    mFileCount++;
    mFileIndex++;

    ALOGD("Opened new dump file: %s", mCurrentFilePath.c_str());
    return true;
}

void StreamDumper::CloseCurrentFile(bool complete) {
    if (!mFile.is_open()) {
        return;
    }

    // Close the file
    mFile.close();

    if (complete && mCurrentFileSize > 0) {
        // Rename from .tmp to .pcm
        std::string finalPath = mDumpDirectory + mCurrentFilename;

        if (rename(mCurrentFilePath.c_str(), finalPath.c_str()) == 0) {
            ALOGI("Renamed dump file: %s -> %s",
                  mCurrentFilePath.c_str(), mCurrentFilename.c_str());

            // Notify manager
            AudioDumpManager::GetInstance().OnDumpFileCompleted(mCurrentFilename);
        } else {
            ALOGE("Failed to rename dump file: %s", strerror(errno));
        }
    } else {
        // Remove incomplete file
        unlink(mCurrentFilePath.c_str());
        ALOGW("Removed incomplete dump file: %s", mCurrentFilePath.c_str());
    }

    mCurrentFilePath.clear();
}

bool StreamDumper::FlushBuffer() {
    if (mBufferOffset == 0) {
        return true;
    }

    if (!mFile.is_open()) {
        ALOGE("Cannot flush: file not open");
        return false;
    }

    mFile.write(mBuffer.data(), mBufferOffset);
    if (!mFile.good()) {
        ALOGE("Failed to write to dump file");
        return false;
    }

    mCurrentFileSize += mBufferOffset;
    mTotalBytesWritten += mBufferOffset;
    mBytesSinceFlush += mBufferOffset;
    mBufferOffset = 0;

    return true;
}

std::string StreamDumper::GenerateFilename(bool withTmp) const {
    char filename[256];
    snprintf(filename, sizeof(filename), "audio_%s_%s_%u_%u.%s",
             GetStreamTypeString(),
             mTimestamp.c_str(),
             mBaseCounter,
             mFileIndex,
             withTmp ? "pcm.tmp" : "pcm");
    return std::string(filename);
}

const char* StreamDumper::GetStreamTypeString() const {
    return (mType == AudioStreamType::STREAM_OUT) ? "streamout" : "streamin";
}

} // namespace audio
} // namespace android
