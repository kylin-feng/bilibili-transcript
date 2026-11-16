#!/usr/bin/env python3
"""faster-whisper 批量转写（GPU 优先，Windows CUDA 运行库自动修复）。

用法：
    python transcribe.py <音频或视频文件> [更多文件...]

每个输入生成两个文件：<stem>_timed.txt（[mm:ss] 逐段）和 <stem>_plain.txt（连排正文）。
- 模型 large-v3-turbo（首次运行自动下载约1.6GB，走 hf-mirror）
- zh + beam_size=5 + VAD；initial_prompt 会显著改善中文标点与领域词汇
"""
import glob
import os
import sys
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# Windows 下 ctranslate2 需要 cuBLAS/cuDNN dll；pip 装的 nvidia-* 包不自动进 PATH
try:
    import nvidia
    for _sub in ("cublas/bin", "cudnn/bin", "nvrtc/bin"):
        for _d in glob.glob(os.path.join(nvidia.__path__[0], _sub)):
            os.environ["PATH"] = _d + os.pathsep + os.environ["PATH"]
except ImportError:
    pass

from faster_whisper import WhisperModel  # noqa: E402

# 按内容领域改写这句话可进一步提升专有名词识别率
PROMPT = ("以下是关于AI、大模型、开源项目、编程和科技新闻的普通话讲解，"
          "其中夹杂英文产品名、公司名和项目名。请使用简体中文标点。")


def fmt(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print("loading model large-v3-turbo ...", flush=True)
    t0 = time.time()
    try:
        model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    except Exception as e:
        print(f"CUDA 不可用（{e}），回退 CPU int8", flush=True)
        model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    print(f"model ready in {time.time()-t0:.0f}s", flush=True)

    for path in sys.argv[1:]:
        stem = os.path.splitext(path)[0]
        t1 = time.time()
        print(f"transcribing {path} ...", flush=True)
        segments, _info = model.transcribe(
            path, language="zh", beam_size=5, vad_filter=True,
            initial_prompt=PROMPT,
        )
        ts_lines, plain = [], []
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            ts_lines.append(f"[{fmt(seg.start)}] {text}")
            plain.append(text)
        with open(f"{stem}_timed.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(ts_lines))
        with open(f"{stem}_plain.txt", "w", encoding="utf-8") as f:
            f.write("".join(plain))
        print(f"{stem}: {len(plain)} segments, {time.time()-t1:.0f}s", flush=True)

    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
