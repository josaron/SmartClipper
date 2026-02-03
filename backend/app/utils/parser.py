import re
from typing import List
from app.models.job import ScriptSegment


def parse_timestamp(timestamp: str) -> int:
    """
    Parse a timestamp string to seconds.
    Supports formats: "MM:SS", "HH:MM:SS", "[MM:SS]", "[HH:MM:SS]"
    """
    # Remove brackets if present
    timestamp = timestamp.strip().strip("[]")
    
    parts = timestamp.split(":")
    if len(parts) == 2:
        # MM:SS format
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # HH:MM:SS format
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def format_timestamp_for_ffmpeg(seconds: int) -> str:
    """Format seconds to HH:MM:SS for FFmpeg."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_script_input(script_input: str) -> List[ScriptSegment]:
    """
    Parse pipe-delimited script input into ScriptSegment objects.
    
    Expected format (one per line):
    Script text here|MM:SS|Description of footage
    
    Also handles:
    Script text here|[MM:SS]|Description of footage
    """
    segments = []
    lines = script_input.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split("|")
        if len(parts) < 2:
            # Try to be lenient - maybe just text and timestamp
            continue
        
        text = parts[0].strip()
        timestamp_raw = parts[1].strip()
        description = parts[2].strip() if len(parts) > 2 else ""
        
        # Extract timestamp from formats like "[23:23]" or "23:23"
        timestamp_match = re.search(r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?', timestamp_raw)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
        else:
            timestamp = timestamp_raw
        
        if text and timestamp:
            segments.append(ScriptSegment(
                text=text,
                timestamp=timestamp,
                description=description
            ))
    
    return segments
