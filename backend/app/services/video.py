import os
import subprocess
from typing import List, Tuple
from app.services.cropper import SubjectDetector
from app.utils.parser import parse_timestamp, format_timestamp_for_ffmpeg


class VideoProcessor:
    """Service for video processing using FFmpeg."""
    
    OUTPUT_WIDTH = 720
    OUTPUT_HEIGHT = 1280
    CLIP_DURATION = 15  # Max seconds to extract per clip
    
    def __init__(self, temp_dir: str = "/app/temp"):
        self.temp_dir = temp_dir
        self.subject_detector = SubjectDetector()
    
    def extract_clip(
        self,
        source_path: str,
        timestamp: str,
        output_path: str,
        duration: float = None
    ) -> str:
        """
        Extract a clip from the source video starting at timestamp.
        
        Args:
            source_path: Path to source video
            timestamp: Start timestamp (MM:SS or HH:MM:SS)
            output_path: Path for output clip
            duration: Duration in seconds (default: CLIP_DURATION)
            
        Returns:
            Path to extracted clip
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        start_seconds = parse_timestamp(timestamp)
        start_ffmpeg = format_timestamp_for_ffmpeg(start_seconds)
        clip_duration = duration or self.CLIP_DURATION
        
        # Extract clip without re-encoding for speed
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", start_ffmpeg,
            "-i", source_path,
            "-t", str(clip_duration),
            "-c", "copy",
            "-an",  # Remove audio
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise Exception(f"FFmpeg clip extraction failed: {result.stderr}")
        
        return output_path
    
    def get_clip_duration(self, clip_path: str) -> float:
        """Get duration of a clip in seconds."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            clip_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        return float(result.stdout.strip())
    
    def get_video_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get width and height of video."""
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
        
        parts = result.stdout.strip().split("x")
        return int(parts[0]), int(parts[1])
    
    def crop_and_resize(
        self,
        input_path: str,
        output_path: str,
        crop_region: Tuple[int, int, int, int]
    ) -> str:
        """
        Crop video to region and resize to output dimensions.
        
        Args:
            input_path: Source clip path
            output_path: Output path
            crop_region: (x, y, width, height) crop region
            
        Returns:
            Path to cropped clip
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        x, y, w, h = crop_region
        
        # Crop and scale in one pass
        filter_str = f"crop={w}:{h}:{x}:{y},scale={self.OUTPUT_WIDTH}:{self.OUTPUT_HEIGHT}"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise Exception(f"FFmpeg crop failed: {result.stderr}")
        
        return output_path
    
    def time_stretch(
        self,
        input_path: str,
        output_path: str,
        target_duration: float
    ) -> str:
        """
        Stretch or compress video to match target duration.
        
        Args:
            input_path: Source clip path
            output_path: Output path
            target_duration: Desired duration in seconds
            
        Returns:
            Path to time-stretched clip
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        current_duration = self.get_clip_duration(input_path)
        if current_duration <= 0:
            raise Exception("Invalid clip duration")
        
        # Calculate speed ratio
        speed_ratio = current_duration / target_duration
        
        # Limit extreme stretching/compression (0.5x to 2x)
        speed_ratio = max(0.5, min(2.0, speed_ratio))
        
        # setpts filter: lower value = faster, higher = slower
        pts_multiplier = 1 / speed_ratio
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vf", f"setpts={pts_multiplier}*PTS",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise Exception(f"FFmpeg time stretch failed: {result.stderr}")
        
        return output_path
    
    def process_clip(
        self,
        source_path: str,
        timestamp: str,
        target_duration: float,
        job_id: str,
        clip_index: int
    ) -> str:
        """
        Full pipeline for processing a single clip:
        1. Extract from source
        2. Detect subject
        3. Crop to 9:16
        4. Time-stretch to match audio
        
        Returns:
            Path to final processed clip
        """
        job_dir = os.path.join(self.temp_dir, job_id, "clips")
        os.makedirs(job_dir, exist_ok=True)
        
        # Step 1: Extract raw clip (15 seconds)
        raw_clip = os.path.join(job_dir, f"raw_{clip_index}.mp4")
        self.extract_clip(source_path, timestamp, raw_clip)
        
        # Step 2: Detect subject center
        width, height = self.get_video_dimensions(raw_clip)
        subject_center = self.subject_detector.analyze_clip(raw_clip)
        
        # Step 3: Calculate crop region
        crop_region = self.subject_detector.calculate_crop_region(
            width, height, subject_center,
            self.OUTPUT_WIDTH, self.OUTPUT_HEIGHT
        )
        
        # Step 4: Crop and resize
        cropped_clip = os.path.join(job_dir, f"cropped_{clip_index}.mp4")
        self.crop_and_resize(raw_clip, cropped_clip, crop_region)
        
        # Step 5: Time-stretch to match audio duration
        final_clip = os.path.join(job_dir, f"final_{clip_index}.mp4")
        self.time_stretch(cropped_clip, final_clip, target_duration)
        
        # Clean up intermediate files
        if os.path.exists(raw_clip):
            os.remove(raw_clip)
        if os.path.exists(cropped_clip):
            os.remove(cropped_clip)
        
        return final_clip
    
    def concatenate_clips(
        self,
        clip_paths: List[str],
        output_path: str
    ) -> str:
        """
        Concatenate multiple clips into one video.
        
        Args:
            clip_paths: List of paths to clips
            output_path: Output video path
            
        Returns:
            Path to concatenated video
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create file list for concat demuxer
        list_path = output_path + ".txt"
        with open(list_path, 'w') as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
        
        # Clean up list file
        os.remove(list_path)
        
        return output_path
    
    def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> str:
        """
        Merge video with audio track.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Output path
            
        Returns:
            Path to final video with audio
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"FFmpeg merge failed: {result.stderr}")
        
        return output_path
    
    def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        timestamp: float = 0.5
    ) -> str:
        """
        Generate a thumbnail from a video at a specific timestamp.
        
        Args:
            video_path: Path to video
            output_path: Output image path
            timestamp: Time in seconds for thumbnail
            
        Returns:
            Path to thumbnail image
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"FFmpeg thumbnail failed: {result.stderr}")
        
        return output_path
    
    def close(self):
        """Release resources."""
        self.subject_detector.close()
