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

/**
 * StreamOut Integration Example
 *
 * This file demonstrates how to integrate StreamDumper into
 * an existing Audio HAL StreamOut implementation.
 *
 * Key integration points:
 * 1. In constructor: Check property and create dumper
 * 2. In write(): Call WriteData() to dump audio data
 * 3. In destructor/close(): Call ForceClose() to finalize dump
 *
 * Note: This is an example file showing integration patterns.
 *       Actual implementation may vary based on your HAL version
 *       and architecture.
 */

#define LOG_TAG "StreamOut_Integration"

#include "AudioDumpManager.h"
#include "StreamDumper.h"

#include <log/log.h>
#include <cstdint>
#include <memory>

namespace android {
namespace audio {

/**
 * Example StreamOut class with dump integration
 *
 * This is a simplified example. Your actual StreamOut class
 * will have more methods and member variables.
 */
class StreamOutWithDump {
public:
    /**
     * Constructor - Initialize stream and optionally create dumper
     */
    StreamOutWithDump() {
        // ... existing initialization code ...

        // Integration Point 1: Create dumper if enabled
        initDumper();
    }

    /**
     * Destructor - Finalize dump if active
     */
    ~StreamOutWithDump() {
        // Integration Point 3: Close dumper before destruction
        closeDumper();

        // ... existing cleanup code ...
    }

    /**
     * Write audio data to hardware
     *
     * @param buffer Audio data buffer
     * @param bytes Size of data in bytes
     * @return Number of bytes written, or negative error code
     */
    ssize_t write(const void* buffer, size_t bytes) {
        // ... existing write logic ...

        // For this example, assume hw_write is your actual hardware write
        // ssize_t written = hw_write(buffer, bytes);
        ssize_t written = bytes; // Placeholder

        // Integration Point 2: Dump audio data if dumper is active
        if (written > 0 && mDumper) {
            mDumper->WriteData(buffer, static_cast<size_t>(written));
        }

        return written;
    }

    /**
     * Close the stream
     */
    void close() {
        // Close dumper first to finalize any pending data
        closeDumper();

        // ... existing close logic ...
    }

    /**
     * Check and refresh dump status
     * Call this periodically or when property changes are expected
     */
    void refreshDumpStatus() {
        bool shouldDump = AudioDumpManager::GetInstance().IsStreamOutDumpEnabled();

        if (shouldDump && !mDumper) {
            // Dump was just enabled
            initDumper();
        } else if (!shouldDump && mDumper) {
            // Dump was just disabled
            closeDumper();
        }
    }

private:
    /**
     * Initialize the dumper
     */
    void initDumper() {
        // Check if dump is enabled via system property
        if (AudioDumpManager::GetInstance().IsStreamOutDumpEnabled()) {
            mDumper = AudioDumpManager::GetInstance().CreateStreamDumper(
                AudioStreamType::STREAM_OUT);

            if (mDumper) {
                ALOGI("StreamOut dump enabled, dumper created");
            } else {
                ALOGW("StreamOut dump enabled but failed to create dumper");
            }
        }
    }

    /**
     * Close the dumper
     */
    void closeDumper() {
        if (mDumper) {
            mDumper->ForceClose();
            mDumper.reset();
            ALOGI("StreamOut dumper closed");
        }
    }

    // Member variables
    std::unique_ptr<StreamDumper> mDumper;

    // ... other member variables for your StreamOut implementation ...
};

/**
 * Alternative integration using a wrapper pattern
 *
 * If you cannot modify your existing StreamOut class,
 * you can use a wrapper pattern:
 */
class StreamOutDumpWrapper {
public:
    StreamOutDumpWrapper() {
        if (AudioDumpManager::GetInstance().IsStreamOutDumpEnabled()) {
            mDumper = AudioDumpManager::GetInstance().CreateStreamDumper(
                AudioStreamType::STREAM_OUT);
        }
    }

    ~StreamOutDumpWrapper() {
        if (mDumper) {
            mDumper->ForceClose();
        }
    }

    /**
     * Call this after each successful write
     */
    void onDataWritten(const void* buffer, size_t size) {
        if (mDumper && mDumper->IsValid()) {
            mDumper->WriteData(buffer, size);
        }
    }

private:
    std::unique_ptr<StreamDumper> mDumper;
};

/**
 * Usage Example in existing code:
 *
 * // In your existing StreamOut class:
 *
 * class YourExistingStreamOut {
 * private:
 *     std::unique_ptr<StreamOutDumpWrapper> mDumpWrapper;
 *
 * public:
 *     YourExistingStreamOut() {
 *         // Create wrapper for dump functionality
 *         mDumpWrapper = std::make_unique<StreamOutDumpWrapper>();
 *     }
 *
 *     ssize_t write(const void* buffer, size_t bytes) {
 *         // Your existing write code
 *         ssize_t written = actualWrite(buffer, bytes);
 *
 *         // Add dump after successful write
 *         if (written > 0 && mDumpWrapper) {
 *             mDumpWrapper->onDataWritten(buffer, written);
 *         }
 *
 *         return written;
 *     }
 * };
 */

} // namespace audio
} // namespace android
