#!/usr/bin/env python3
"""Extract subtitles from YouTube videos.

Priority: manual subtitles > auto-generated subtitles.
Returns JSON with subtitle text and metadata.
"""
import json
import re
import sys


def extract_video_id(url_or_id: str) -> str | None:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    # Already a video ID (11 chars, alphanumeric + dash/underscore)
    if re.match(r'^[\w-]{11}$', url_or_id):
        return url_or_id

    # Various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})',
        r'youtube\.com/watch\?.*[\?&]v=([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return None


def get_subtitles(video_id: str, languages: list[str] | None = None) -> dict:
    """Try to fetch subtitles for a YouTube video.

    Args:
        video_id: YouTube video ID
        languages: Preferred language codes (default: zh-Hans, zh, en)

    Returns:
        {"ok": True, "text": "...", "source": "manual"|"auto", "language": "zh"}
        or {"ok": False, "error": "...", "has_subtitles": False}
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    if languages is None:
        languages = ["zh-Hans", "zh", "zh-CN", "zh-TW", "en"]

    ytt_api = YouTubeTranscriptApi()

    # Try to find available transcripts
    try:
        transcript_list = ytt_api.list(video_id)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Cannot fetch transcript list: {e}",
            "has_subtitles": False,
        }

    # Find the best available transcript
    # Priority 1: manually created in preferred language
    # Priority 2: auto-generated in preferred language
    # Priority 3: any manually created
    # Priority 4: any auto-generated
    target = None
    source_type = None

    for lang in languages:
        for t in transcript_list:
            if t.language_code == lang or t.language_code.startswith(lang.split("-")[0]):
                if not t.is_generated:
                    target = t
                    source_type = "manual"
                    break
        if target:
            break

    if not target:
        for lang in languages:
            for t in transcript_list:
                if t.language_code == lang or t.language_code.startswith(lang.split("-")[0]):
                    if t.is_generated:
                        target = t
                        source_type = "auto"
                        break
            if target:
                break

    if not target:
        # Try any transcript
        for t in transcript_list:
            if not t.is_generated:
                target = t
                source_type = "manual"
                break

    if not target:
        for t in transcript_list:
            target = t
            source_type = "auto"
            break

    if not target:
        return {
            "ok": False,
            "error": "No subtitles available for this video",
            "has_subtitles": False,
        }

    # Fetch and assemble text
    try:
        transcript = target.fetch()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to fetch transcript: {e}",
            "has_subtitles": False,
        }

    # Combine all snippets into plain text
    lines = []
    for snippet in transcript.snippets:
        lines.append(snippet.text)

    full_text = " ".join(lines)
    # Clean up: remove duplicate spaces
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    return {
        "ok": True,
        "text": full_text,
        "source": source_type,
        "language": target.language_code,
        "snippet_count": len(transcript.snippets),
        "video_id": video_id,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "error": "usage: youtube_subtitle.py <youtube_url_or_id>",
        }, ensure_ascii=False))
        return 1

    url_or_id = sys.argv[1]
    video_id = extract_video_id(url_or_id)

    if not video_id:
        print(json.dumps({
            "ok": False,
            "error": f"Cannot extract video ID from: {url_or_id}",
        }, ensure_ascii=False))
        return 1

    result = get_subtitles(video_id)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
