import os
import subprocess
import re
import json
from typing import Optional

# #region agent log
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str = ""):
    """Write debug log entry to NDJSON file."""
    import time
    log_path = "/Users/josephaharon/Documents/workspace/SmartClipper/.cursor/debug.log"
    entry = {
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "sessionId": "debug-session",
        "hypothesisId": hypothesis_id
    }
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
# #endregion


class YouTubeDownloader:
    """Service for downloading YouTube videos using yt-dlp."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        # #region agent log
        _debug_log("downloader.py:init", "YouTubeDownloader initialized", {"output_dir": output_dir}, "LOCAL")
        # #endregion
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download(self, url: str, job_id: str) -> str:
        """
        Download a YouTube video at 720p max quality.
        
        Args:
            url: YouTube video URL
            job_id: Unique job identifier for the output filename
            
        Returns:
            Path to the downloaded video file
        """
        output_path = os.path.join(self.output_dir, job_id, "source.mp4")
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # #region agent log
        # Log yt-dlp version (Hypothesis B)
        version_result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        _debug_log("downloader.py:download:version", "yt-dlp version check", {"version": version_result.stdout.strip(), "stderr": version_result.stderr.strip()}, "B")
        # #endregion

        # #region agent log
        # Log URL and video ID being processed (Hypothesis D)
        video_id = self.extract_video_id(url)
        _debug_log("downloader.py:download:url", "URL being processed", {"url": url, "video_id": video_id, "job_id": job_id}, "D")
        # #endregion

        # Normalize URL to standard format (avoid short URLs and tracking params)
        if video_id:
            normalized_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            normalized_url = url

        # #region agent log
        _debug_log("downloader.py:download:normalized", "URL normalization", {"original": url, "normalized": normalized_url, "video_id": video_id}, "H")
        # #endregion

        # Check for YouTube cookies (optional - helps bypass bot detection on cloud IPs)
        cookies_file = None
        youtube_cookies = os.getenv("YOUTUBE_COOKIES")
        if youtube_cookies:
            cookies_file = os.path.join(self.output_dir, "cookies.txt")
            with open(cookies_file, "w") as f:
                f.write(youtube_cookies)

        # yt-dlp command to download at 720p max
        # Try multiple player clients to bypass YouTube bot detection on cloud IPs
        # Order: mweb (mobile web), ios, android - these often work better from datacenter IPs
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", output_path,
            "--no-playlist",
            "--no-warnings",
            "--extractor-args", "youtube:player_client=mweb,ios,android",
            "--extractor-args", "youtube:player_skip=webpage",
            "--retries", "5",
            "--force-ipv4",
            "--sleep-requests", "1",
            "--geo-bypass",
        ]
        
        # Add cookies if available
        if cookies_file:
            cmd.extend(["--cookies", cookies_file])
        
        cmd.append(normalized_url)

        # #region agent log
        _debug_log("downloader.py:download:cmd", "yt-dlp command", {"cmd": cmd, "has_cookies": cookies_file is not None}, "F,G,K,L")
        # #endregion
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # #region agent log
            _debug_log("downloader.py:download:result", "yt-dlp execution result", {
                "returncode": result.returncode,
                "stdout": result.stdout[:2000] if result.stdout else "",
                "stderr": result.stderr[:2000] if result.stderr else ""
            }, "A,C,D,E")
            # #endregion
            
            if result.returncode != 0:
                # #region agent log
                _debug_log("downloader.py:download:failure", "yt-dlp failed", {
                    "returncode": result.returncode,
                    "full_stderr": result.stderr,
                    "contains_bot_detection": "Sign in to confirm" in result.stderr or "bot" in result.stderr.lower(),
                    "contains_age_restriction": "age" in result.stderr.lower(),
                    "contains_login_required": "login" in result.stderr.lower() or "sign in" in result.stderr.lower()
                }, "A,C,D")
                # #endregion
                raise Exception(f"yt-dlp failed: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise Exception("Video download completed but file not found")
            
            return output_path
            
        except subprocess.TimeoutExpired:
            raise Exception("Video download timed out after 5 minutes")
    
    def get_video_duration(self, video_path: str) -> float:
        """Get the duration of a video in seconds using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        return float(result.stdout.strip())
    
    def get_video_dimensions(self, video_path: str) -> tuple[int, int]:
        """Get the width and height of a video."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        dimensions = result.stdout.strip().split("x")
        return int(dimensions[0]), int(dimensions[1])
