# Audio Dump Monitor - Windows Client

Windows端音频Dump自动监控工具，用于从Android设备自动拉取音频dump文件。

## 功能特性

- 🔄 **实时监控**: 通过logcat实时监听`AUDIO_DUMP_READY`通知
- 📋 **队列轮询**: 每10秒轮询`.queue`文件作为备份机制
- ⚡ **并发拉取**: 2个并发线程从设备拉取文件
- 📊 **统计报告**: 每60秒输出统计信息
- 🔒 **防重复**: 使用Set记录已处理文件，避免重复拉取
- ♻️ **重试机制**: 拉取失败时自动重试
- 📝 **日志系统**: 同时输出到控制台和文件

## 系统要求

- Windows 10/11
- Python 3.7 或更高版本
- ADB (Android Debug Bridge)
- 通过USB连接的Android设备

## 安装步骤

### 1. 安装Python

从 [Python官网](https://www.python.org/downloads/) 下载并安装Python 3.7+

安装时请勾选 "Add Python to PATH"

### 2. 安装ADB

下载 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)

解压后将目录添加到系统PATH环境变量

### 3. 准备工作

```batch
# 确认Python已安装
python --version

# 确认ADB已安装
adb version

# 确认设备已连接
adb devices
```

## 使用方法

### 快速开始

双击 `start_monitor.bat` 启动监控程序

### 命令行启动

```batch
# 使用默认配置
python audio_dump_monitor.py

# 使用自定义配置文件
python audio_dump_monitor.py --config my_config.json

# 指定输出目录
python audio_dump_monitor.py --output D:\AudioDumps
```

### 停止监控

按 `Ctrl+C` 停止监控程序

## 配置说明

编辑 `config.json` 文件修改配置：

```json
{
    "device_dump_path": "/data/vendor/audio_dump/",
    "device_queue_file": "/data/vendor/audio_dump/.queue",
    "local_save_path": "./audio_dumps",
    "use_logcat": true,
    "poll_interval": 10,
    "pull_workers": 2,
    "stats_interval": 60,
    "adb_timeout": 30,
    "max_retries": 3,
    "retry_delay": 2,
    "log_file": "audio_dump_monitor.log",
    "log_level": "INFO"
}
```

### 配置项说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `device_dump_path` | 设备端dump文件目录 | `/data/vendor/audio_dump/` |
| `device_queue_file` | 设备端队列文件路径 | `/data/vendor/audio_dump/.queue` |
| `local_save_path` | 本地保存目录 | `./audio_dumps` |
| `use_logcat` | 是否使用logcat监听 | `true` |
| `poll_interval` | 队列轮询间隔（秒） | `10` |
| `pull_workers` | 并发拉取线程数 | `2` |
| `stats_interval` | 统计报告间隔（秒） | `60` |
| `adb_timeout` | ADB命令超时（秒） | `30` |
| `max_retries` | 最大重试次数 | `3` |
| `retry_delay` | 重试延迟（秒） | `2` |
| `log_file` | 日志文件名 | `audio_dump_monitor.log` |
| `log_level` | 日志级别 | `INFO` |

## 工作流程

1. **启动时**：检查Python和ADB，确认设备连接
2. **监控中**：
   - logcat监听线程实时接收`AUDIO_DUMP_READY`消息
   - 队列轮询线程每10秒读取`.queue`文件
   - 发现新文件时加入任务队列
   - 拉取线程从队列取出文件并拉取
   - 拉取成功后删除设备端文件
3. **统计报告**：每60秒输出统计信息
4. **停止时**：输出最终统计信息

## 日志文件

日志保存在 `audio_dump_monitor.log` 文件中，包含：

- 时间戳
- 日志级别
- 线程名称
- 详细消息

## 常见问题

### Q: 提示"No adb device connected"

A: 请检查：
1. 设备是否通过USB连接
2. USB调试是否开启
3. 是否已授权该电脑

### Q: 文件拉取很慢

A: 可以尝试：
1. 使用USB 3.0接口
2. 更换质量更好的数据线
3. 增加`pull_workers`数量

### Q: 日志中出现权限错误

A: 设备需要root权限访问`/data/vendor/`目录：
```batch
adb root
adb shell "chmod 777 /data/vendor/audio_dump"
```

## 输出文件

拉取的文件保存在 `audio_dumps` 目录（或配置的`local_save_path`），文件命名格式：

```
audio_streamout_20240106_103000_0_1.pcm
audio_streamin_20240106_103005_1_1.pcm
```

格式说明：`audio_{类型}_{时间戳}_{计数器}_{文件索引}.pcm`
