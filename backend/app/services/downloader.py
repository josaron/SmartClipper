import os
import subprocess
import re
from typing import Optional


class YouTubeDownloader:
    """Service for downloading YouTube videos using yt-dlp."""
    
    def __init__(self, output_dir: str = "/app/temp"):
        self.output_dir = output_dir
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
        
        # yt-dlp command to download at 720p max
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", output_path,
            "--no-playlist",
            "--no-warnings",
            url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
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
