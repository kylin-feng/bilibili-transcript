---
name: bilibili-transcript
description: 提取B站视频的完整口播文案（转写稿），并考据视频里提到的项目名和GitHub链接。当用户给出 bilibili.com / B站 视频链接（av 或 BV 号），要求提取文案、字幕、转写、扒稿、拆解口播内容，或要求整理视频里提到的项目/工具/开源仓库清单时，务必使用本技能。自动抓取标题简介、下载音频、faster-whisper 本地 GPU 转写（无需登录B站）、生成带时间戳原稿+清理版全文，还能抽帧识别画面标题卡上的项目名用于链接考据。
---

# Skill: bilibili-transcript（B站视频文案提取）

把 B 站视频的口播文案完整扒出来，输出「带时间戳原稿 + 清理版全文 + 简介存档」；盘点类视频还可以抽帧认出画面上的项目名，去 GitHub 考据出仓库链接。

本技能的核心价值：B 站的 CC/AI 字幕接口需要登录态（浏览器 Cookie 经常拿不到），所以走「音频下载 → 本地 whisper 转写」这条不依赖登录的路线，全程可在用户电脑上离线完成（除下载外）。

## 工作流程

### 第 1 步：解析链接并抓取视频信息

从用户给的 URL 里提取 av 号（`bilibili.com/video/av117461785514310`）或 BV 号。用脚本抓取标题、简介、cid、时长：

```bash
python <skill目录>/scripts/fetch_info.py "https://www.bilibili.com/video/avXXXX" [更多链接...]
```

输出：终端打印信息 + 当前目录生成 `descriptions.txt`（含标题/UP主/链接/简介原文）。**简介务必保留**——它是后续清理转写稿和考据项目名的第一手对照材料（UP主常在简介里列出项目官方名和 GitHub 链接）。

### 第 2 步：（可选，先试无妨）尝试官方字幕

```bash
python -c "import json,urllib.request as u; r=u.Request('https://api.bilibili.com/x/player/v2?aid=AV号&cid=CID号',headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'}); print(json.loads(u.urlopen(r).read())['data']['subtitle']['subtitles'])"
```

若返回 `[]`（未登录的常态），直接进入第 3 步，不要在此恋战。若拿到了 `subtitle_url`，拼上 `https:` 前缀下载 JSON 即为字幕，转写步骤可跳过。

### 第 3 步：下载音频

```bash
yt-dlp --no-update -x --audio-format wav -o "v1_%(id)s.%(ext)s" "视频URL"
```

文件名前缀用 v1/v2/v3… 区分多条视频（`%(id)s` 会展开成 BV 号）。

### 第 4 步：本地转写（faster-whisper + GPU）

```bash
python <skill目录>/scripts/transcribe.py v1_BVxxxx.wav [更多wav...]
```

脚本会用 `large-v3-turbo` 模型、CUDA float16、VAD 过滤、中文 initial_prompt（提示词里写明内容领域可显著提升专有名词识别）。每条音频生成：
- `v1_BVxxxx_timed.txt`：`[mm:ss] 文本` 逐段时间戳原稿
- `v1_BVxxxx_plain.txt`：无时间戳连排版

RTX 4060 Ti 上约 30 倍速实时（10 分钟视频 20 秒转完）。首次运行会下载 1.6GB 模型。

### 第 5 步：清理成稿

对照第 1 步的简介，修正 `_plain.txt` 后输出交付稿（`文案汇总.md`）。清理规则见下方「转写清理规范」，这是决定交付质量的一步，不要跳过。

### 第 6 步：（盘点/资讯类视频）项目链接考据

新闻盘点类视频口播常只说「研究员开源了XX模型」不点名。做法：**抽帧读画面标题卡**——这类视频每个条目出现时画面上方都有「研究员开源XX模型「项目名」」的标题卡。

```bash
python <skill目录>/scripts/extract_frames.py video.mp4 --interval 3 --tag v1
```

生成 `v1_sheet_NN.png`（每张 3×2 共 6 帧，帧上烧录了时间戳）。用视觉模型逐张读出标题卡上的项目名，再结合 `_timed.txt` 的时间戳对应到口播条目。识别出的名字用 GitHub 搜索 API 验证：

```bash
curl -s "https://api.github.com/search/repositories?q=NAME+in:name&per_page=5" -H "Accept: application/vnd.github+json" -H "User-Agent: repo-lookup"
```

验证要点：仓库描述与口播内容吻合、创建/更新时间在视频发布前后。名字太通用（如 PURE、Falcon、Idol）时要加领域词（`PURE 3D reconstruction`）。

## 转写清理规范

1. **专有名词以视频简介为第一准绳**：简介列了官方名（如 claude-mem、Hy-SimulMT），转写稿里的同音错误（Cloud MEM、中音双向）一律照简介改。
2. **常见同音/近音错误模式**（zh→中文术语）：
   - 建库/建的库 ← 「见得酷」「艰苦」「键的库」；颗星 ← 「可星」「克型」「克星」「可行」
   - Claude Code ← 「Cloud Code」「Codecode」；递归式 ← 「地规式」；汇报 ← 「回报」
   - 值夜班 ← 「职业班」；运维 ← 「未营」；重写 ← 「冲写」；挂谷猜想 ← 「挂骨猜想」；量子场论 ← 「量子常论」
3. **片尾音乐幻觉**：whisper 对纯音乐段会编出「请不吝点赞 订阅 转发 打赏支持明镜与点点栏目」这类句子，结尾重复句同理——识别到就删，并在交付稿注明。
4. **拿不准的不硬改**：听不清的人名、口头梗（如反复出现的「大肥鱼」）保留原样并标注存疑；数字（星数、参数量）如关键需提示用户复核。
5. **交付格式**：每条视频给「标题 / UP主 / 链接 / 时长」元信息 + 分段正文（长视频按话题分段，盘点类一个条目一段），结尾附与简介的名称对照表。

## 环境要求与常见坑

- 依赖：`yt-dlp`、`ffmpeg`（均在 PATH）、Python ≥3.10 且装有 `faster-whisper`。
- **Windows + CUDA 报 `cublas64_12.dll is not found`**：装 `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`（国内加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`），transcribe.py 已内置把 `site-packages/nvidia/*/bin` 前置到 PATH 的逻辑；若用户的 `os.add_dll_dir` 不可用属正常，仅 PATH 方式即可。
- **HuggingFace 直连超时**：`export HF_ENDPOINT=https://hf-mirror.com`（脚本已内置 fallback）；模型只需下载一次。
- **pip 装错环境**：Windows 上常有多套 Python（系统 Python、各种 venv），先确认 `faster-whisper` 装在哪套，就用那套的绝对路径跑 transcribe.py。
- **GitHub API 限流**：搜索接口未登录 10 次/分钟，批量考据时每次查询间 sleep 7s，或走本地代理换 IP。
- **ffmpeg 拼图**：Windows 版 ffmpeg 不支持 `-pattern_type glob`，抽帧脚本已用顺序编号规避。
- B 站下载偶尔 406/403：重试即可；确实失败时提示用户换链接或稍后再试。
