/**
 * Script parser for frontend validation.
 * Mirrors the backend logic in backend/app/utils/parser.py
 */

export interface ScriptSegment {
  text: string;
  timestamp: string;
  description: string;
}

export interface ParseResult {
  segments: ScriptSegment[];
  invalidLines: number[]; // 0-indexed line numbers that couldn't be parsed
  totalLines: number;
}

/**
 * Parse alternative format: MM:SS Script text... [MM:SS] (Description)
 * The bracketed timestamp [MM:SS] is the YouTube video timestamp.
 */
function parseAlternativeFormat(line: string): ScriptSegment | null {
  // Look for bracketed timestamp [MM:SS] or [HH:MM:SS]
  const bracketMatch = line.match(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/);
  if (!bracketMatch) {
    return null;
  }

  const timestamp = bracketMatch[1];

  // Extract description from parentheses after the bracketed timestamp
  const descMatch = line.match(/\[[\d:]+\]\s*\(([^)]+)\)/);
  const description = descMatch ? descMatch[1].trim() : "";

  // Extract text: everything before the bracketed timestamp, minus any leading timestamp
  let textPortion = line.substring(0, bracketMatch.index).trim();

  // Remove leading timestamp (e.g., "00:30   " at start)
  textPortion = textPortion.replace(/^(\d{1,2}:\d{2}(?::\d{2})?)\s+/, "");

  const text = textPortion.trim();

  if (text && timestamp) {
    return { text, timestamp, description };
  }

  return null;
}

/**
 * Parse script input into ScriptSegment objects.
 *
 * Supports two formats:
 *
 * 1. Pipe-delimited (preferred):
 *    Script text here|MM:SS|Description of footage
 *
 * 2. Alternative format (Gemini-style):
 *    MM:SS   Script text here   [MM:SS] (Description of footage)
 */
export function parseScriptInput(scriptInput: string): ParseResult {
  const segments: ScriptSegment[] = [];
  const invalidLines: number[] = [];
  const lines = scriptInput.trim().split("\n");

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim();
    if (!line) {
      return; // Skip empty lines (don't count as invalid)
    }

    // Try pipe-delimited format first
    const parts = line.split("|");
    if (parts.length >= 2) {
      const text = parts[0].trim();
      const timestampRaw = parts[1].trim();
      const description = parts.length > 2 ? parts[2].trim() : "";

      // Extract timestamp from formats like "[23:23]" or "23:23"
      const timestampMatch = timestampRaw.match(/\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?/);
      if (timestampMatch && text) {
        segments.push({
          text,
          timestamp: timestampMatch[1],
          description,
        });
        return;
      }
    }

    // Try alternative format: MM:SS Text... [MM:SS] (Description)
    const altSegment = parseAlternativeFormat(line);
    if (altSegment) {
      segments.push(altSegment);
      return;
    }

    // Line couldn't be parsed
    invalidLines.push(index);
  });

  return {
    segments,
    invalidLines,
    totalLines: lines.filter((l) => l.trim()).length,
  };
}

/**
 * Calculate estimated duration based on text length.
 * Rough estimate: ~150 words per minute for TTS
 */
export function estimateDuration(segments: ScriptSegment[]): number {
  const totalWords = segments.reduce((sum, seg) => {
    return sum + seg.text.split(/\s+/).length;
  }, 0);
  // 150 words per minute = 2.5 words per second
  return Math.round(totalWords / 2.5);
}
