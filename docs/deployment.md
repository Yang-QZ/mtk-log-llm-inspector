# Audio Dump Automation System - 部署指南

本文档详细说明Audio Dump自动化监控系统的部署步骤。

## 前置条件

### Android设备端

- Android 8.0 (API 26) 或更高版本
- Root权限（访问/data/vendor目录）
- 已集成MTK Audio HAL

### Windows PC端

- Windows 10/11
- Python 3.7 或更高版本
- Android SDK Platform Tools (ADB)
- USB数据线或WiFi连接

## 第一部分：Android HAL端部署

### 步骤1：获取源代码

将`android/hal/`目录下的文件复制到您的Audio HAL源码目录：

```bash
# 假设您的HAL目录是 /path/to/vendor/mediatek/hal/audio
cp -r android/hal/* /path/to/vendor/mediatek/hal/audio/dump/
```

需要复制的文件：
- `AudioDumpManager.h`
- `AudioDumpManager.cpp`
- `StreamDumper.h`
- `StreamDumper.cpp`
- `Android.bp`

### 步骤2：修改HAL编译配置

在您的Audio HAL的`Android.bp`中添加依赖：

```blueprint
cc_library_shared {
    name: "audio.primary.mt6xxx",

    // ... 现有配置 ...

    static_libs: [
        "libaudiodump_static",
        // ... 其他静态库 ...
    ],

    // 或者使用共享库：
    shared_libs: [
        "libaudiodump",
        // ... 其他共享库 ...
    ],
}
```

### 步骤3：集成到StreamOut

参考`StreamOut_integration.cpp`，在您的StreamOut实现中添加：

```cpp
#include <AudioDumpManager.h>
#include <StreamDumper.h>

class YourStreamOut {
private:
    std::unique_ptr<android::audio::StreamDumper> mDumper;

public:
    YourStreamOut() {
        // 构造函数中创建dumper
        auto& manager = android::audio::AudioDumpManager::GetInstance();
        if (manager.IsStreamOutDumpEnabled()) {
            mDumper = manager.CreateStreamDumper(
                android::audio::AudioStreamType::STREAM_OUT);
        }
    }

    ssize_t write(const void* buffer, size_t bytes) {
        // 现有的写入逻辑
        ssize_t written = doHardwareWrite(buffer, bytes);

        // 添加dump
        if (written > 0 && mDumper) {
            mDumper->WriteData(buffer, static_cast<size_t>(written));
        }

        return written;
    }

    ~YourStreamOut() {
        if (mDumper) {
            mDumper->ForceClose();
        }
    }
};
```

### 步骤4：集成到StreamIn

参考`StreamIn_integration.cpp`，在您的StreamIn实现中添加类似的代码。

### 步骤5：编译和推送

```bash
# 编译整个Audio HAL
cd /path/to/android/source
source build/envsetup.sh
lunch your_target-userdebug
mmm vendor/mediatek/hal/audio

# 推送到设备
adb root
adb remount
adb push out/target/product/xxx/vendor/lib64/hw/audio.primary.mt6xxx.so /vendor/lib64/hw/
adb push out/target/product/xxx/vendor/lib64/libaudiodump.so /vendor/lib64/

# 重启Audio服务
adb shell "kill $(pidof audioserver)"
```

### 步骤6：创建dump目录

```bash
adb root
adb shell "mkdir -p /data/vendor/audio_dump"
adb shell "chmod 777 /data/vendor/audio_dump"
adb shell "chown audioserver:audio /data/vendor/audio_dump"
```

### 步骤7：验证安装

```bash
# 启用dump
adb shell "setprop vendor.streamout.pcm.dump 1"

# 播放一些音频

# 检查是否有dump文件
adb shell "ls -la /data/vendor/audio_dump/"

# 检查logcat
adb logcat | grep "AUDIO_DUMP_READY"
```

## 第二部分：Windows监控端部署

### 步骤1：安装Python

1. 访问 https://www.python.org/downloads/
2. 下载Python 3.7或更高版本
3. 运行安装程序
4. **重要**：勾选 "Add Python to PATH"
5. 完成安装

验证安装：
```batch
python --version
```

### 步骤2：安装ADB

1. 访问 https://developer.android.com/studio/releases/platform-tools
2. 下载Platform Tools for Windows
3. 解压到例如 `C:\platform-tools`
4. 添加到系统PATH：
   - 右键"此电脑" → 属性 → 高级系统设置
   - 环境变量 → 系统变量 → Path → 编辑
   - 新建 → 输入 `C:\platform-tools`
   - 确定

验证安装：
```batch
adb version
```

### 步骤3：复制监控程序

将`windows/`目录复制到您的工作目录：

```batch
mkdir C:\AudioDumpMonitor
copy windows\* C:\AudioDumpMonitor\
```

目录结构应该是：
```
C:\AudioDumpMonitor\
├── audio_dump_monitor.py
├── config.json
├── start_monitor.bat
├── requirements.txt
└── README.md
```

### 步骤4：配置（可选）

编辑`config.json`根据需要修改配置：

```json
{
    "device_dump_path": "/data/vendor/audio_dump/",
    "local_save_path": "D:\\AudioDumps",
    "use_logcat": true,
    "poll_interval": 10,
    "pull_workers": 2
}
```

### 步骤5：连接设备

使用USB连接：
```batch
adb devices
```

使用WiFi连接（需要先用USB设置）：
```batch
# 先用USB连接
adb tcpip 5555

# 然后断开USB，使用WiFi
adb connect 192.168.1.xxx:5555
```

### 步骤6：启动监控

双击`start_monitor.bat`或命令行运行：

```batch
cd C:\AudioDumpMonitor
python audio_dump_monitor.py
```

### 步骤7：验证运行

1. 在设备上播放音频
2. 检查监控程序输出是否有文件拉取信息
3. 检查本地`audio_dumps`目录是否有文件

## 完整测试流程

### 1. 启用设备端dump

```bash
adb root
adb shell "setprop vendor.streamout.pcm.dump 1"
adb shell "setprop vendor.streamin.pcm.dump 1"
```

### 2. 启动Windows监控

```batch
start_monitor.bat
```

### 3. 触发音频

- 播放一首歌曲（测试streamout）
- 录制语音（测试streamin）

### 4. 观察结果

监控程序应该显示：
```
2024-01-06 10:30:15 [INFO] Queued from logcat: audio_streamout_20240106_103015_0_1.pcm
2024-01-06 10:30:16 [INFO] Worker 0: Pulled audio_streamout_20240106_103015_0_1.pcm
```

### 5. 验证文件

```batch
dir audio_dumps
```

### 6. 禁用dump（完成后）

```bash
adb shell "setprop vendor.streamout.pcm.dump 0"
adb shell "setprop vendor.streamin.pcm.dump 0"
```

## 开机自启动配置（可选）

### Windows自启动

1. 按 `Win+R`，输入 `shell:startup`
2. 在打开的目录中创建快捷方式指向 `start_monitor.bat`

### Android自启动（需要修改init.rc）

在您的`init.xxx.rc`中添加：

```
on property:vendor.streamout.pcm.dump=1
    mkdir /data/vendor/audio_dump 0777 audioserver audio

on property:vendor.streamin.pcm.dump=1
    mkdir /data/vendor/audio_dump 0777 audioserver audio
```

## 卸载

### Windows端

删除`C:\AudioDumpMonitor`目录即可。

### Android端

如果需要完全移除dump功能：

1. 从Audio HAL代码中移除集成代码
2. 从Android.bp中移除libaudiodump依赖
3. 重新编译并推送HAL

```bash
adb shell "rm -rf /data/vendor/audio_dump"
adb shell "setprop vendor.streamout.pcm.dump 0"
adb shell "setprop vendor.streamin.pcm.dump 0"
```
