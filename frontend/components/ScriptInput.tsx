"use client";

import { Textarea } from "@/components/ui/textarea";

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
        className="min-h-[200px] font-mono text-sm"
      />
      <p className="text-xs text-muted-foreground">
        Format: <code className="bg-muted px-1 rounded">Script text|Timestamp|Description</code> (one segment per line)
      </p>
    </div>
  );
}
