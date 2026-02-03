#!/usr/bin/env python3
"""Quick test script to verify the parser fix."""

import sys
sys.path.insert(0, '.')

from app.utils.parser import parse_script_input

# Test input from user's screenshot
test_input = """the "family-friendly" era ending, the show was axed in 2003.
[27:44] (Footage of the dragon breaking down or the show ending)
00:30   For 20 years, Murphy didn't leave. He was simply locked behind a wall in his dark, underwater cave.   [28:01] (Shot of the sealed cave entrance)
00:38   In 2024, his lair was finally sealed for good. Most think he was scrapped, but some say he's still in there...   [28:22] (Shot of the modern, "sterile" castle front)
00:46   ...waiting for the day the magic returns to Vegas. Subscribe for more lost history!   [31:01] (Wide shot of the Excalibur towers)"""

print("=" * 60)
print("Testing parser with user's input format")
print("=" * 60)
print("\nInput:")
print(test_input)
print("\n" + "=" * 60)
print("Parsed segments:")
print("=" * 60)

segments = parse_script_input(test_input)

if not segments:
    print("\n❌ FAILED: No valid script segments found!")
else:
    print(f"\n✅ SUCCESS: Found {len(segments)} segment(s)\n")
    for i, seg in enumerate(segments, 1):
        print(f"Segment {i}:")
        print(f"  Text: {seg.text[:60]}...")
        print(f"  Timestamp: {seg.timestamp}")
        print(f"  Description: {seg.description}")
        print()

# Also test pipe-delimited format still works
print("=" * 60)
print("Testing original pipe-delimited format")
print("=" * 60)

pipe_input = """Did you know a 51-foot fire-breathing dragon used to live on the Las Vegas Strip?|23:23|Close up of Murphy the Dragon
This is Murphy. He was the star of the Excalibur Hotel...|24:02|Murphy emerging from the cave"""

segments2 = parse_script_input(pipe_input)
if segments2:
    print(f"\n✅ Pipe format still works: Found {len(segments2)} segment(s)")
else:
    print("\n❌ Pipe format broken!")
