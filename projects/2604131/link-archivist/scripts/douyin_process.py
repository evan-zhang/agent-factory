#!/usr/bin/env python3
"""
抖音视频分析一键脚本
用法: python3 douyin_process.py <抖音分享链接> [输出目录]

流程（优先 API 方案）：
  1. API方案：玄关开放平台API → 直接返回ASR文本（推荐）
  2. MC方案：mcporter解析 → curl下载视频 → ffmpeg提取音频 → 生成报告（降级）
"""

import sys
import os
import re
import json
import subprocess
import shutil
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# API方案配置（玄关开放平台抖音音频导出）
DOUYIN_API_BASE = "https://hk-al-xg-node.mediportal.com.cn"
DOUYIN_API_TOKEN = "47a0e299aaea700d6133a9ee3ab17018a56c616ada15ba1f484faec70801169b"


def process_with_api(share_link):
    """
    玄关开放平台API方案：直接调用抖音音频导出API，获取ASR文本。
    推荐优先使用，无需mcporter/ffmpeg。
    """
    print("[1/1] 调用玄关开放平台API提取音频+ASR...")

    payload = json.dumps({"url": share_link}).encode()
    req = urllib.request.Request(
        f"{DOUYIN_API_BASE}/api/open/audio/export-with-asr",
        data=payload,
        headers={
            "Authorization": f"Bearer {DOUYIN_API_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=200) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if result.get("status") != "200":
        raise RuntimeError(f"API返回错误: {result.get('msg', 'unknown')}")

    data = result.get("data", {})
    return {
        "aweme_id": data.get("aweme_id", ""),
        "is_original": data.get("is_original", False),
        "music_title": data.get("music_title", ""),
        "asr_text": data.get("asr_text", ""),
        "share_link": share_link,
    }

import sys
import os
import re
import json
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path


def run(cmd, timeout=120, check=True):
    """执行命令，返回 stdout"""
    print(f"  > {cmd[:120]}...")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"命令失败 (rc={result.returncode}): {result.stderr[:500]}")
    return result.stdout.strip()


def parse_with_mcp(share_link):
    """用 mcporter 调用 Douyin MCP Server 解析链接"""
    print("[1/4] 解析抖音链接...")
    
    safe_link = share_link.replace('"', '\\"')
    
    output = run(
        f'mcporter call \'douyin.parse_douyin_video_info(share_link: "{safe_link}")\'',
        timeout=60
    )
    
    # 用正则提取关键信息
    title_match = re.search(r'标题[:：\s]*(.+)', output)
    id_match = re.search(r'ID[:：\s]*(\d+)', output)
    url_match = re.search(r'(https://aweme\.snssdk\.com/[^\s]+)', output)
    
    title = title_match.group(1).strip() if title_match else ""
    video_id = id_match.group(1).strip() if id_match else ""
    download_url = url_match.group(1).strip() if url_match else ""
    
    if not download_url:
        raise RuntimeError(f"无法获取下载链接。MCP 输出:\n{output}")
    
    print(f"  标题: {title}")
    print(f"  ID: {video_id}")
    print(f"  下载链接: {download_url[:80]}...")
    
    return {"title": title, "video_id": video_id, "download_url": download_url}


def parse_with_python(share_link):
    """备选方案：用 Python requests 直接解析"""
    import requests
    
    print("[1/4] 用 Python 直接解析抖音链接...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                       "Mobile/15E148 Safari/604.1",
        "Referer": "https://www.douyin.com/",
    }
    
    # 跟随重定向获取真实URL
    resp = requests.get(share_link, headers=headers, timeout=30, 
                        allow_redirects=True, verify=False)
    real_url = resp.url
    
    # 提取视频ID
    vid_match = re.search(r'/video/(\d+)', real_url)
    video_id = vid_match.group(1) if vid_match else ""
    
    if not video_id:
        raise RuntimeError(f"无法从 URL 提取视频ID: {real_url}")
    
    # 构造无水印下载链接
    download_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=720p&line=0"
    
    # 从页面提取标题
    title_match = re.search(r'<title[^>]*>(.*?)</title>', resp.text)
    title = title_match.group(1) if title_match else f"抖音视频_{video_id}"
    
    print(f"  标题: {title}")
    print(f"  ID: {video_id}")
    
    return {"title": title, "video_id": video_id, "download_url": download_url}


def download_video(url, output_path):
    """下载视频"""
    print(f"[2/4] 下载视频...")
    
    run(
        f'curl -L -o "{output_path}" '
        f'-H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" '
        f'-H "Referer: https://www.douyin.com/" '
        f'"{url}" --max-time 300 --noproxy \'*\' -s',
        timeout=320
    )
    
    size = os.path.getsize(output_path)
    if size < 10000:
        raise RuntimeError(f"下载文件过小 ({size} bytes)，可能下载失败")
    
    print(f"  下载完成: {size / 1024 / 1024:.1f} MB")
    return size


def extract_audio(video_path, audio_path):
    """用 ffmpeg 提取音频"""
    print(f"[3/4] 提取音频...")
    
    run(
        f'ffmpeg -i "{video_path}" -vn -acodec libmp3lame -ab 128k '
        f'"{audio_path}" -y -loglevel warning',
        timeout=120
    )
    
    size = os.path.getsize(audio_path)
    if size < 1000:
        raise RuntimeError(f"音频文件过小 ({size} bytes)，提取失败")
    
    # 获取时长
    duration_out = run(
        f'ffprobe -i "{audio_path}" -show_entries format=duration '
        f'-v quiet -of csv="p=0"',
        timeout=10, check=False
    )
    duration = float(duration_out) if duration_out else 0
    
    mins, secs = divmod(int(duration), 60)
    print(f"  音频: {size / 1024:.0f} KB, 时长 {mins}:{secs:02d}")
    return duration


def generate_report(info, output_dir, audio_duration, transcript=""):
    """生成分析报告"""
    print(f"[4/4] 生成报告...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    duration_str = f"{int(audio_duration) // 60}:{int(audio_duration) % 60:02d}" if audio_duration else "未知"
    
    report = f"""# 抖音视频分析报告

## 基本信息
- **标题**：{info['title']}
- **视频ID**：{info['video_id']}
- **来源链接**：{info.get('share_link', '')}
- **视频时长**：{duration_str}
- **分析时间**：{now}

## 文件
- 视频：{output_dir}/video.mp4
- 音频：{output_dir}/audio.mp3
"""

    if transcript:
        report += f"""
## 语音转写

{transcript}
"""
    else:
        report += """
## 语音转写

（转写服务暂不可用，仅提供视频元数据）
"""

    report += f"""
## 内容摘要

**标题**：{info['title']}

> 基于视频元数据生成。如需详细内容分析，请在转写可用后重新运行。

---
*由 douyin-video-analysis skill 自动生成*
"""
    
    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"  报告已保存: {report_path}")
    return report_path


def main():
    use_api = "--api" in sys.argv
    if len(sys.argv) < 2 or (len(sys.argv) < 3 and not use_api):
        print("用法: python3 douyin_process.py <抖音分享链接> [输出目录] [--api]")
        print("  --api: 使用玄关开放平台API方案（推荐，默认方案）")
        print("  不加--api: 使用mcporter+ffmpeg方案（降级方案）")
        print("示例: python3 douyin_process.py https://v.douyin.com/XXXXX/ /tmp/douyin_out")
        sys.exit(1)

    share_link = sys.argv[1] if len(sys.argv) >= 2 else sys.argv[2]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 and sys.argv[2] != "--api" else f"/tmp/douyin_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"{'='*50}")
    print(f"抖音视频分析")
    print(f"链接: {share_link}")
    print(f"输出: {output_dir}")
    print(f"方案: {'玄关API' if use_api else 'mcporter+ffmpeg降级'}")
    print(f"{'='*50}\n")

    os.makedirs(output_dir, exist_ok=True)

    # API方案（推荐）
    if use_api:
        try:
            info = process_with_api(share_link)
            print(f"  视频ID: {info['aweme_id']}")
            print(f"  ASR长度: {len(info['asr_text'])} 字")
            print(f"  ASR预览: {info['asr_text'][:80]}...")
            result = {
                "success": True,
                "method": "api",
                "aweme_id": info["aweme_id"],
                "is_original": info["is_original"],
                "music_title": info["music_title"],
                "asr_text": info["asr_text"],
                "share_link": share_link,
                "output_dir": output_dir,
            }
            print(f"\n__JSON_RESULT__{json.dumps(result, ensure_ascii=False)}")
            return
        except Exception as e:
            print(f"  API方案失败: {e}")
            print(f"  降级为mcporter+ffmpeg方案...")

    # 降级方案：mcporter+ffmpeg
    # Step 1: 解析链接（优先 MCP，失败用 Python）
    info = None
    try:
        info = parse_with_mcp(share_link)
    except Exception as e:
        print(f"  MCP 解析失败: {e}")
        print(f"  尝试 Python 备选方案...")
        try:
            info = parse_with_python(share_link)
        except Exception as e2:
            print(f"  Python 解析也失败: {e2}")
            sys.exit(1)

    info["share_link"] = share_link

    # Step 2: 下载视频
    video_path = os.path.join(output_dir, "video.mp4")
    download_video(info["download_url"], video_path)

    # Step 3: 提取音频
    audio_path = os.path.join(output_dir, "audio.mp3")
    audio_duration = extract_audio(video_path, audio_path)

    # Step 4: 生成报告
    report_path = generate_report(info, output_dir, audio_duration)

    print(f"\n{'='*50}")
    print(f"✅ 分析完成!")
    print(f"输出目录: {output_dir}/")
    print(f"  video.mp4  - 视频文件")
    print(f"  audio.mp3  - 音频文件")
    print(f"  report.md  - 分析报告")
    print(f"{'='*50}")

    # 返回 JSON 结果供 Agent 使用
    result = {
        "success": True,
        "method": "mcporter",
        "title": info["title"],
        "video_id": info["video_id"],
        "output_dir": output_dir,
        "video_file": video_path,
        "audio_file": audio_path,
        "report_file": report_path,
        "audio_duration": audio_duration,
    }
    print(f"\n__JSON_RESULT__{json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
