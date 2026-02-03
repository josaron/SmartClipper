import os
import asyncio
import shutil
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.job import (
    Job, JobCreate, JobProgress, JobPreview, JobStatus,
    ScriptSegment, AVAILABLE_VOICES
)
from app.utils.parser import parse_script_input
from app.services.downloader import YouTubeDownloader
from app.services.tts import PiperTTS
from app.services.video import VideoProcessor
from app.config import TEMP_DIR, OUTPUT_DIR

router = APIRouter()

# In-memory job storage (for MVP - use Redis/DB for production)
jobs: Dict[str, Job] = {}


def update_job_progress(job: Job, status: JobStatus, progress: int, message: str):
    """Update job progress."""
    job.status = status
    job.progress = progress
    job.message = message


async def process_job(job_id: str):
    """Background task to process a video generation job."""
    job = jobs.get(job_id)
    if not job:
        return
    
    try:
        downloader = YouTubeDownloader(output_dir=TEMP_DIR)
        tts = PiperTTS(output_dir=TEMP_DIR)
        video_processor = VideoProcessor(temp_dir=TEMP_DIR)
        
        job_dir = os.path.join(TEMP_DIR, job_id)
        output_dir = os.path.join(OUTPUT_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Download video (0-20%)
        update_job_progress(job, JobStatus.DOWNLOADING, 5, "Downloading video...")
        source_video = downloader.download(job.youtube_url, job_id)
        update_job_progress(job, JobStatus.DOWNLOADING, 20, "Video downloaded")
        
        # Step 2: Generate TTS audio for each segment (20-40%)
        update_job_progress(job, JobStatus.GENERATING_AUDIO, 25, "Generating voiceover...")
        
        audio_paths = []
        for i, segment in enumerate(job.segments):
            audio_path = os.path.join(job_dir, f"audio_{i}.wav")
            duration = tts.generate_audio(segment.text, job.voice, audio_path)
            segment.audio_duration = duration
            segment.audio_path = audio_path
            audio_paths.append(audio_path)
            
            progress = 25 + int((i + 1) / len(job.segments) * 15)
            update_job_progress(job, JobStatus.GENERATING_AUDIO, progress, 
                              f"Generated audio {i+1}/{len(job.segments)}")
        
        # Concatenate all audio
        full_audio_path = os.path.join(output_dir, "audio.wav")
        tts.concatenate_audio(audio_paths, full_audio_path)
        job.audio_path = full_audio_path
        update_job_progress(job, JobStatus.GENERATING_AUDIO, 40, "Audio complete")
        
        # Step 3: Process video clips (40-80%)
        update_job_progress(job, JobStatus.PROCESSING_VIDEO, 45, "Processing video clips...")
        
        clip_paths = []
        for i, segment in enumerate(job.segments):
            clip_path = video_processor.process_clip(
                source_video,
                segment.timestamp,
                segment.audio_duration,
                job_id,
                i
            )
            segment.clip_path = clip_path
            clip_paths.append(clip_path)
            
            progress = 45 + int((i + 1) / len(job.segments) * 35)
            update_job_progress(job, JobStatus.PROCESSING_VIDEO, progress,
                              f"Processed clip {i+1}/{len(job.segments)}")
        
        # Step 4: Concatenate clips and merge with audio (80-95%)
        update_job_progress(job, JobStatus.FINALIZING, 85, "Assembling final video...")
        
        concatenated_video = os.path.join(job_dir, "concatenated.mp4")
        video_processor.concatenate_clips(clip_paths, concatenated_video)
        
        final_video = os.path.join(output_dir, "output.mp4")
        video_processor.merge_audio_video(concatenated_video, full_audio_path, final_video)
        job.video_path = final_video
        
        # Step 5: Generate thumbnails (95-100%)
        update_job_progress(job, JobStatus.FINALIZING, 95, "Generating preview...")
        
        thumbnails = []
        for i, segment in enumerate(job.segments):
            if segment.clip_path and os.path.exists(segment.clip_path):
                thumb_path = os.path.join(output_dir, f"thumb_{i}.jpg")
                video_processor.generate_thumbnail(segment.clip_path, thumb_path, 0.5)
                thumbnails.append(f"/static/{job_id}/thumb_{i}.jpg")
        job.thumbnails = thumbnails
        
        # Clean up temp files
        shutil.rmtree(job_dir, ignore_errors=True)
        
        # Mark complete
        from datetime import datetime
        job.completed_at = datetime.utcnow()
        update_job_progress(job, JobStatus.COMPLETED, 100, "Complete!")
        
        video_processor.close()
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.message = f"Processing failed: {str(e)}"


@router.get("/voices")
async def get_voices():
    """Get available TTS voices."""
    return {"voices": AVAILABLE_VOICES}


@router.post("", response_model=dict)
async def create_job(request: JobCreate, background_tasks: BackgroundTasks):
    """
    Create a new video generation job.
    
    The job will be processed in the background. Use the returned job ID
    to poll for status updates.
    """
    # Parse script input
    segments = parse_script_input(request.script_input)
    if not segments:
        raise HTTPException(status_code=400, detail="No valid script segments found")
    
    # Validate voice
    valid_voices = [v["id"] for v in AVAILABLE_VOICES]
    if request.voice not in valid_voices:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid voice. Available: {valid_voices}"
        )
    
    # Create job
    job = Job(
        youtube_url=request.youtube_url,
        voice=request.voice,
        segments=segments,
        message="Job created, starting processing..."
    )
    
    jobs[job.id] = job
    
    # Start background processing
    background_tasks.add_task(process_job, job.id)
    
    return {"job_id": job.id, "status": job.status.value}


@router.get("/{job_id}/status", response_model=JobProgress)
async def get_job_status(job_id: str):
    """Get the current status and progress of a job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.get_progress()


@router.get("/{job_id}/preview", response_model=JobPreview)
async def get_job_preview(job_id: str):
    """Get preview data for a completed job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Job not complete. Current status: {job.status.value}"
        )
    
    return job.get_preview()


@router.get("/{job_id}/download")
async def download_video(job_id: str):
    """Download the final video file."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not complete. Current status: {job.status.value}"
        )
    
    if not job.video_path or not os.path.exists(job.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        job.video_path,
        media_type="video/mp4",
        filename=f"smartclipper_{job_id}.mp4"
    )


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up files
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    job_temp_dir = os.path.join(TEMP_DIR, job_id)
    shutil.rmtree(job_output_dir, ignore_errors=True)
    shutil.rmtree(job_temp_dir, ignore_errors=True)
    
    del jobs[job_id]
    
    return {"message": "Job deleted"}
