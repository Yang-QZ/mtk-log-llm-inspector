# Audio Dump Automation System - 故障排查指南

本文档列出常见问题及其解决方案。

## Android HAL端问题

### 问题1：Dump文件未生成

**症状**：设置了属性但/data/vendor/audio_dump/目录为空

**排查步骤**：

1. 检查属性是否设置成功：
```bash
adb shell "getprop vendor.streamout.pcm.dump"
# 应该返回 "1"
```

2. 检查目录权限：
```bash
adb shell "ls -la /data/vendor/ | grep audio_dump"
# 应该看到 drwxrwxrwx
```

3. 检查logcat错误：
```bash
adb logcat | grep -E "AudioDump|StreamDumper"
```

4. 检查HAL是否正确加载：
```bash
adb shell "lsof | grep libaudiodump"
```

**解决方案**：

- 如果属性未生效，重启audioserver：
```bash
adb shell "kill $(pidof audioserver)"
```

- 如果权限问题：
```bash
adb shell "mkdir -p /data/vendor/audio_dump"
adb shell "chmod 777 /data/vendor/audio_dump"
adb shell "chown audioserver:audio /data/vendor/audio_dump"
```

### 问题2：Dump文件一直是.tmp后缀

**症状**：文件以.tmp结尾，从未被重命名为.pcm

**可能原因**：
- 音频流未正常关闭
- StreamDumper析构函数未被调用

**解决方案**：

1. 确保在StreamOut/StreamIn的close()方法中调用ForceClose()：
```cpp
void YourStreamOut::close() {
    if (mDumper) {
        mDumper->ForceClose();
        mDumper.reset();
    }
    // ... 其他关闭逻辑
}
```

2. 手动停止音频流测试：
```bash
# 停止播放/录音后检查
adb shell "ls /data/vendor/audio_dump/*.pcm"
```

### 问题3：Logcat中没有AUDIO_DUMP_READY消息

**排查步骤**：

1. 确认logcat过滤正确：
```bash
adb logcat -s AudioDumpManager:I
```

2. 检查ALOGI是否被编译：
```cpp
// 确保LOG_TAG定义在#include之前
#define LOG_TAG "AudioDumpManager"
#include <log/log.h>
```

3. 检查编译选项是否禁用了日志

### 问题4：磁盘空间不足

**症状**：Dump突然停止，logcat显示写入失败

**解决方案**：

1. 检查可用空间：
```bash
adb shell "df -h /data"
```

2. 清理旧文件：
```bash
adb shell "rm /data/vendor/audio_dump/*.pcm"
adb shell "rm /data/vendor/audio_dump/*.tmp"
```

3. 减小单文件大小（修改StreamDumper.h中的MAX_FILE_SIZE）

## Windows监控端问题

### 问题1：提示"No adb device connected"

**可能原因**：
- 设备未连接
- USB调试未开启
- 驱动问题

**解决方案**：

1. 检查物理连接
2. 开启USB调试：设置 → 开发者选项 → USB调试
3. 安装设备驱动
4. 尝试更换USB端口或数据线
5. 在设备上确认授权

### 问题2：Logcat监听无响应

**症状**：文件只能通过队列轮询获取，logcat监听无效

**排查步骤**：

1. 手动测试logcat：
```batch
adb logcat -s AudioDumpManager:I
```

2. 检查Python进程：
```batch
tasklist | findstr python
```

**解决方案**：

1. 确保只有一个监控实例运行
2. 尝试禁用logcat使用纯轮询模式：
```json
{
    "use_logcat": false,
    "poll_interval": 5
}
```

### 问题3：文件拉取失败

**症状**：日志显示"Pull attempt failed"

**可能原因**：
- 文件不存在（已被删除）
- 权限问题
- ADB连接不稳定

**解决方案**：

1. 检查设备端文件：
```bash
adb shell "ls -la /data/vendor/audio_dump/"
```

2. 手动测试拉取：
```bash
adb pull /data/vendor/audio_dump/test_file.pcm .
```

3. 增加重试次数：
```json
{
    "max_retries": 5,
    "retry_delay": 3
}
```

4. 检查USB连接质量

### 问题4：重复文件通知

**症状**：同一个文件多次出现在日志中

**可能原因**：
- Set去重机制失效
- 线程竞争条件

**解决方案**：

1. 检查processed_files集合是否正常工作
2. 重启监控程序
3. 如果问题持续，检查是否有多个监控实例

### 问题5：统计信息不准确

**症状**：显示的文件数或字节数不正确

**解决方案**：

1. 确保Statistics类的锁正常工作
2. 检查文件实际大小：
```batch
dir audio_dumps
```

## 性能问题

### 问题1：Dump导致音频卡顿

**可能原因**：
- Buffer太小
- Flush太频繁
- 磁盘IO慢

**解决方案**：

1. 增大buffer大小（修改StreamDumper.h）：
```cpp
static constexpr size_t BUFFER_SIZE = 512 * 1024;  // 512KB
```

2. 增大flush阈值：
```cpp
static constexpr size_t FLUSH_THRESHOLD = 20 * 1024 * 1024;  // 20MB
```

3. 检查是否使用高速存储

### 问题2：文件传输很慢

**解决方案**：

1. 使用USB 3.0端口和数据线
2. 增加worker线程数：
```json
{
    "pull_workers": 4
}
```

3. 使用WiFi ADB（某些情况下更快）

### 问题3：监控程序占用CPU过高

**解决方案**：

1. 增大轮询间隔：
```json
{
    "poll_interval": 30
}
```

2. 减少worker数量
3. 检查是否有死循环日志

## 日志和调试

### 启用详细日志

**Android端**：
```bash
adb shell "setprop log.tag.AudioDumpManager V"
adb shell "setprop log.tag.StreamDumper V"
```

**Windows端**：
修改config.json：
```json
{
    "log_level": "DEBUG"
}
```

### 查看完整日志

**Android端**：
```bash
adb logcat -v time | grep -E "AudioDump|StreamDumper" > android_dump.log
```

**Windows端**：
查看`audio_dump_monitor.log`文件

### 检查.queue文件

```bash
adb shell "cat /data/vendor/audio_dump/.queue"
```

### 清理测试环境

```bash
# Android端
adb shell "rm -rf /data/vendor/audio_dump/*"
adb shell "setprop vendor.streamout.pcm.dump 0"
adb shell "setprop vendor.streamin.pcm.dump 0"

# Windows端
del audio_dumps\*
del audio_dump_monitor.log
```

## 联系支持

如果以上方案无法解决问题，请收集以下信息后联系支持：

1. Android版本和设备型号
2. HAL版本信息
3. 相关logcat日志
4. Windows端日志文件
5. 问题复现步骤
