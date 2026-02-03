from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    GENERATING_AUDIO = "generating_audio"
    PROCESSING_VIDEO = "processing_video"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScriptSegment(BaseModel):
    """A single segment of the script with its associated footage timestamp."""
    text: str
    timestamp: str  # Format: "MM:SS" or "HH:MM:SS"
    description: str
    
    # Computed during processing
    audio_duration: Optional[float] = None
    audio_path: Optional[str] = None
    clip_path: Optional[str] = None


class JobCreateForm(BaseModel):
    """Form data for creating a new job (used with file upload)."""
    script_input: str = Field(..., description="Pipe-delimited script input")
    voice: str = Field(default="en_US-lessac-medium", description="Piper voice model name")


class JobProgress(BaseModel):
    """Current progress of a job."""
    status: JobStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    message: str = ""
    error: Optional[str] = None


class JobPreview(BaseModel):
    """Preview data for a completed job."""
    thumbnails: List[str] = Field(default_factory=list, description="URLs to thumbnail images")
    audio_url: str = Field(default="", description="URL to the full TTS audio")
    duration: float = Field(default=0.0, description="Total duration in seconds")


class Job(BaseModel):
    """Complete job data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_video_path: str = Field(..., description="Path to the uploaded source video")
    voice: str
    segments: List[ScriptSegment] = Field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Output paths
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    thumbnails: List[str] = Field(default_factory=list)
    
    def get_progress(self) -> JobProgress:
        return JobProgress(
            status=self.status,
            progress=self.progress,
            message=self.message,
            error=self.error
        )
    
    def get_preview(self) -> JobPreview:
        return JobPreview(
            thumbnails=self.thumbnails,
            audio_url=f"/static/{self.id}/audio.wav" if self.audio_path else "",
            duration=sum(s.audio_duration or 0 for s in self.segments)
        )


# Available voices
AVAILABLE_VOICES = [
    {"id": "en_US-lessac-medium", "name": "Lessac (US Male)", "language": "en-US"},
    {"id": "en_US-amy-medium", "name": "Amy (US Female)", "language": "en-US"},
    {"id": "en_GB-alan-medium", "name": "Alan (UK Male)", "language": "en-GB"},
]
