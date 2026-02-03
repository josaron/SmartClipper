"use client";

import { useMemo } from "react";
import { Textarea } from "@/components/ui/textarea";
import { parseScriptInput, estimateDuration } from "@/lib/parser";
import { CheckCircle2, AlertCircle, Clock } from "lucide-react";

interface ScriptInputProps {
  value: string;
  onChange: (value: string) => void;
}

const EXAMPLE_INPUT = `Did you know a 51-foot fire-breathing dragon used to live on the Las Vegas Strip?|23:23|Close up of Murphy the Dragon
This is Murphy. He was the star of the Excalibur Hotel, emerging from a cave every hour to battle Merlin.|24:02|Murphy emerging from the cave
Built by Disney veterans, Murphy was a hydraulic beast who spent his days submerged in the castle moat.|23:37|View of the mechanical skeleton/hydraulics
But the desert wasn't kind. Between constant breakdowns and the "family-friendly" era ending, the show was axed in 2003.|27:44|Footage of the dragon breaking down
For 20 years, Murphy didn't leave. He was simply locked behind a wall in his dark, underwater cave.|28:01|Shot of the sealed cave entrance
In 2024, his lair was finally sealed for good. Most think he was scrapped, but some say he's still in there...|28:22|Shot of the modern castle front
...waiting for the day the magic returns to Vegas. Subscribe for more lost history!|31:01|Wide shot of the Excalibur towers`;

export function ScriptInput({ value, onChange }: ScriptInputProps) {
  // Parse and validate in real-time
  const parseResult = useMemo(() => {
    if (!value.trim()) return null;
    return parseScriptInput(value);
  }, [value]);

  const segmentCount = parseResult?.segments.length ?? 0;
  const invalidCount = parseResult?.invalidLines.length ?? 0;
  const estimatedSeconds = parseResult ? estimateDuration(parseResult.segments) : 0;

  // Determine validation state
  const hasInput = value.trim().length > 0;
  const isValid = hasInput && segmentCount > 0;
  const hasWarnings = invalidCount > 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium leading-none">
          Script & Timestamps
        </label>
        <button
          type="button"
          onClick={() => onChange(EXAMPLE_INPUT)}
          className="text-xs text-primary hover:underline"
        >
          Load example
        </button>
      </div>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste your script here in pipe-delimited format:

Script text here|MM:SS|Description of footage
Another line of script|MM:SS|Another description"
        className={`min-h-[200px] font-mono text-sm ${
          hasInput && !isValid ? "border-destructive focus-visible:ring-destructive" : ""
        }`}
      />

      {/* Validation feedback */}
      <div className="flex items-center justify-between text-xs">
        <p className="text-muted-foreground">
          Format: <code className="bg-muted px-1 rounded">Script text|Timestamp|Description</code> (one segment per line)
        </p>

        {/* Status indicator */}
        {hasInput && (
          <div className="flex items-center gap-3">
            {isValid ? (
              <>
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {segmentCount} segment{segmentCount !== 1 ? "s" : ""}
                </span>
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Clock className="w-3.5 h-3.5" />
                  ~{estimatedSeconds}s
                </span>
              </>
            ) : (
              <span className="flex items-center gap-1 text-destructive">
                <AlertCircle className="w-3.5 h-3.5" />
                No valid segments
              </span>
            )}
          </div>
        )}
      </div>

      {/* Warning for partially invalid input */}
      {hasWarnings && segmentCount > 0 && (
        <p className="text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5" />
          {invalidCount} line{invalidCount !== 1 ? "s" : ""} couldn&apos;t be parsed and will be skipped
        </p>
      )}

      {/* Help text when no valid segments */}
      {hasInput && !isValid && (
        <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
          <p className="font-medium mb-1">No valid script segments found</p>
          <p className="text-xs">
            Each line should follow the format: <code>Script text|MM:SS|Description</code>
            <br />
            Or: <code>MM:SS Script text [MM:SS] (Description)</code>
          </p>
        </div>
      )}
    </div>
  );
}
