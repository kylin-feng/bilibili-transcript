# bilibili-transcript

B 站视频文案提取 skill：给一个 bilibili.com 视频链接，自动产出完整口播文案（带时间戳原稿 + 清理版全文），并支持盘点类视频的项目名/ GitHub 链接考据。

不依赖 B 站登录——字幕接口需要 Cookie，本工具走「音频下载 → faster-whisper 本地 GPU 转写」路线。

## 能做什么

- **文案提取**：av/BV 链接 → 标题/UP主/简介存档 → wav 音频 → `large-v3-turbo` 中文转写（RTX 4060 Ti 上约 30 倍速实时）→ `[mm:ss]` 时间戳稿 + 连排正文稿
- **清理成稿**：对照视频简介修正专有名词同音错误，剔除片尾音乐幻觉句，输出可读交付稿
- **链接考据**（盘点/资讯类视频）：每 3 秒抽帧拼图，读画面标题卡上的项目名 → GitHub/HuggingFace API 验证 → 生成条目-仓库对照表

## 依赖

| 工具 | 用途 |
|---|---|
| Python ≥ 3.10 + `faster-whisper` | 转写 |
| `yt-dlp` | 音频下载 |
| `ffmpeg` / `ffprobe` | 音频抽取、抽帧拼图 |
| GPU（可选） | CUDA float16 加速；无 GPU 自动回退 CPU int8 |

Windows + CUDA 首次使用若报 `cublas64_12.dll is not found`：

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

（`scripts/transcribe.py` 已内置把 pip 版 NVIDIA 运行库目录前置到 PATH 的逻辑。）

## 用法

```bash
# 1. 抓视频信息（生成 descriptions.txt）
python scripts/fetch_info.py "https://www.bilibili.com/video/av117461785514310"

# 2. 下载音频
yt-dlp --no-update -x --audio-format wav -o "v1_%(id)s.%(ext)s" "https://www.bilibili.com/video/av117461785514310"

# 3. 转写（生成 v1_BVxxxx_timed.txt / v1_BVxxxx_plain.txt）
python scripts/transcribe.py v1_BVxxxx.wav

# 4.（可选，盘点类视频）抽帧拼图考据画面上的项目名
python scripts/extract_frames.py v1_video.mp4 --interval 3 --tag v1
```

完整工作流与转写清理规范见 [SKILL.md](SKILL.md)。

## 作为 agent skill 安装

把本目录（含 `SKILL.md` 和 `scripts/`）放进你的 skills 目录即可，例如：

```
~/.agents/skills/bilibili-transcript/
```

## License

MIT
