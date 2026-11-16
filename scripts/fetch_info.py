#!/usr/bin/env python3
"""抓取B站视频信息：标题/UP主/简介/cid/时长，存为 descriptions.txt。

用法：
    python fetch_info.py <视频URL或av/BV号> [更多链接...]

可接受的形式：完整URL、纯av号（如 117461785514310）、纯BV号（如 BV1UAn36aEX3）。
"""
import json
import re
import sys
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


def to_aid(token):
    """把 URL / av号 / BV号 统一成 aid 查询参数。"""
    token = token.strip()
    m = re.search(r"av(\d+)", token, re.I)
    if m:
        return f"aid={m.group(1)}"
    m = re.search(r"(BV[0-9A-Za-z]{10})", token)
    if m:
        return f"bvid={m.group(1)}"
    if token.isdigit():
        return f"aid={token}"
    raise SystemExit(f"无法识别的视频标识: {token}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = []
    for token in sys.argv[1:]:
        v = get(f"https://api.bilibili.com/x/web-interface/view?{to_aid(token)}")["data"]
        block = (
            f"标题：{v['title']}\n"
            f"UP主：{v['owner']['name']}\n"
            f"链接：https://www.bilibili.com/video/{v['bvid']}\n"
            f"bvid：{v['bvid']}\ncid：{v['cid']}\n时长：{v['duration']}s\n"
            f"发布时间戳：{v['pubdate']}\n\n简介：\n{v['desc']}"
        )
        out.append(block)
        print(f"{v['bvid']} | {v['title']} | {v['duration']}s | UP:{v['owner']['name']}")
    with open("descriptions.txt", "w", encoding="utf-8") as f:
        f.write(("\n" + "=" * 60 + "\n").join(out))
    print(f"已保存 {len(out)} 条到 descriptions.txt")


if __name__ == "__main__":
    main()
