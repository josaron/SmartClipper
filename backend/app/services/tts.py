import os
import subprocess
import wave
from typing import List, Tuple


class PiperTTS:
    """Service for generating TTS audio using Piper."""
    
    VOICE_MODELS = {
        "en_US-lessac-medium": "/app/voices/en_US-lessac-medium.onnx",
        "en_US-amy-medium": "/app/voices/en_US-amy-medium.onnx",
        "en_GB-alan-medium": "/app/voices/en_GB-alan-medium.onnx",
    }
    
    def __init__(self, output_dir: str = "/app/temp"):
        self.output_dir = output_dir
    
    def generate_audio(self, text: str, voice: str, output_path: str) -> float:
        """
        Generate TTS audio for a text segment.
        
        Args:
            text: Text to convert to speech
            voice: Voice model name
            output_path: Path for output WAV file
            
        Returns:
            Duration of the generated audio in seconds
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        model_path = self.VOICE_MODELS.get(voice)
        if not model_path:
            raise ValueError(f"Unknown voice: {voice}. Available: {list(self.VOICE_MODELS.keys())}")
        
        # Use piper to generate audio
        cmd = [
            "piper",
            "--model", model_path,
            "--output_file", output_path
        ]
        
        try:
            # Pipe the text to piper
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"Piper TTS failed: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise Exception("TTS completed but audio file not found")
            
            # Get duration
            return self.get_audio_duration(output_path)
            
        except subprocess.TimeoutExpired:
            raise Exception("TTS generation timed out")
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get the duration of an audio file in seconds."""
        with wave.open(audio_path, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            return frames / float(rate)
    
    def generate_segments(
        self, 
        segments: List[Tuple[str, str]],  # List of (text, output_path)
        voice: str
    ) -> List[float]:
        """
        Generate TTS audio for multiple segments.
        
        Args:
            segments: List of (text, output_path) tuples
            voice: Voice model name
            
        Returns:
            List of durations for each segment
        """
        durations = []
        for text, output_path in segments:
            duration = self.generate_audio(text, voice, output_path)
            durations.append(duration)
        return durations
    
    def concatenate_audio(self, audio_paths: List[str], output_path: str) -> float:
        """
        Concatenate multiple audio files into one.
        
        Args:
            audio_paths: List of paths to audio files
            output_path: Path for the combined output
            
        Returns:
            Total duration of concatenated audio
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a file list for FFmpeg
        list_path = output_path + ".txt"
        with open(list_path, 'w') as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")
        
        # Use FFmpeg to concatenate
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
            
            # Clean up list file
            os.remove(list_path)
            
            return self.get_audio_duration(output_path)
            
        except subprocess.TimeoutExpired:
            raise Exception("Audio concatenation timed out")
