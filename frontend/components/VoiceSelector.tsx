"use client";

import { Select } from "@/components/ui/select";
import type { Voice } from "@/lib/api";

interface VoiceSelectorProps {
  voices: Voice[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function VoiceSelector({ voices, value, onChange, disabled }: VoiceSelectorProps) {
  const options = voices.map((voice) => ({
    value: voice.id,
    label: `${voice.name} (${voice.language})`,
  }));

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium leading-none">
        Voice
      </label>
      <Select
        options={options}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
      <p className="text-xs text-muted-foreground">
        Select the voice for the TTS voiceover
      </p>
    </div>
  );
}
