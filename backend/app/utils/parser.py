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


def _parse_alternative_format(line: str) -> tuple:
    """
    Parse alternative format: MM:SS Script text... [MM:SS] (Description)
    
    The bracketed timestamp [MM:SS] is the YouTube video timestamp.
    The parenthesized text (Description) is the visual description.
    The leading MM:SS is voiceover timing (ignored for now).
    
    Returns: (text, timestamp, description) or (None, None, None) if no match
    """
    # Pattern: optional leading timestamp, text, bracketed timestamp, optional description
    # Example: 00:30   For 20 years, Murphy didn't leave...   [28:01] (Shot of the sealed cave entrance)
    
    # Look for bracketed timestamp [MM:SS] or [HH:MM:SS]
    bracket_match = re.search(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', line)
    if not bracket_match:
        return None, None, None
    
    timestamp = bracket_match.group(1)
    
    # Extract description from parentheses after the bracketed timestamp
    desc_match = re.search(r'\[[\d:]+\]\s*\(([^)]+)\)', line)
    description = desc_match.group(1).strip() if desc_match else ""
    
    # Extract text: everything before the bracketed timestamp, minus any leading timestamp
    text_portion = line[:bracket_match.start()].strip()
    
    # Remove leading timestamp (e.g., "00:30   " at start)
    text_portion = re.sub(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+', '', text_portion)
    
    # Clean up the text
    text = text_portion.strip()
    
    if text and timestamp:
        return text, timestamp, description
    
    return None, None, None


def parse_script_input(script_input: str) -> List[ScriptSegment]:
    """
    Parse script input into ScriptSegment objects.
    
    Supports two formats:
    
    1. Pipe-delimited (preferred):
       Script text here|MM:SS|Description of footage
       Script text here|[MM:SS]|Description of footage
    
    2. Alternative format (Gemini-style):
       MM:SS   Script text here   [MM:SS] (Description of footage)
       Where the bracketed [MM:SS] is the YouTube video timestamp.
    """
    segments = []
    lines = script_input.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try pipe-delimited format first
        parts = line.split("|")
        if len(parts) >= 2:
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
                continue
        
        # Try alternative format: MM:SS Text... [MM:SS] (Description)
        text, timestamp, description = _parse_alternative_format(line)
        if text and timestamp:
            segments.append(ScriptSegment(
                text=text,
                timestamp=timestamp,
                description=description
            ))
    
    return segments
