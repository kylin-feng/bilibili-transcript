#!/usr/bin/env python3
"""按固定间隔抽帧并拼成 3x2 看图页（用于读取盘点视频画面标题卡上的项目名）。

用法：
    python extract_frames.py <视频文件> [--interval 3] [--tag v1] [--max-frames 999]

输出（当前目录）：
    <tag>_f_001.png ...   带烧录时间戳的单帧
    <tag>_sheet_NN.png    每张拼6帧（3列2行，行优先顺序）

说明：帧上左上角烧录了黄色时间戳，配合 *_timed.txt 可把画面条目对回到口播文本。
Windows 版 ffmpeg 不支持 glob pattern，本脚本用顺序编号规避。
"""
import argparse
import subprocess
import sys

FONT = "C\\:/Windows/Fonts/consola.ttf"


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--interval", type=float, default=3, help="抽帧间隔秒数，默认3")
    ap.add_argument("--tag", default="v", help="输出文件前缀")
    ap.add_argument("--max-frames", type=int, default=999)
    ap.add_argument("--duration", type=float, default=None,
                    help="视频总时长秒数；不传则用 ffprobe 自动获取")
    args = ap.parse_args()

    if args.duration is None:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", args.video],
            capture_output=True, text=True, check=True)
        args.duration = float(p.stdout.strip())

    t, i = 0.5, 0
    while t < args.duration and i < args.max_frames:
        i += 1
        vf = (f"drawtext=text='{t:.0f}s':x=8:y=8:fontsize=42:fontcolor=yellow:"
              f"box=1:boxcolor=black@0.75:fontfile='{FONT}'")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", args.video,
             "-frames:v", "1", "-vf", vf, f"{args.tag}_f_{i:03d}.png"])
        t += args.interval
    print(f"extracted {i} frames")

    if i:
        sheets = (i + 5) // 6
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1",
             "-i", f"{args.tag}_f_%03d.png",
             "-vf", "scale=640:-2,tile=3x2", "-frames:v", str(sheets),
             f"{args.tag}_sheet_%02d.png"])
        print(f"tiled into {sheets} sheets ({args.tag}_sheet_01.png ...)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg 调用失败: {e}")
