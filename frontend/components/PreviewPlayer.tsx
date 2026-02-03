"use client";

import Image from "next/image";
import { Volume2 } from "lucide-react";

interface PreviewPlayerProps {
  thumbnails: string[];
  audioUrl: string;
  duration: number;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function PreviewPlayer({ thumbnails, audioUrl, duration }: PreviewPlayerProps) {
  return (
    <div className="space-y-6">
      {/* Thumbnail Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Preview Frames</h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {thumbnails.map((thumb, index) => (
            <div
              key={index}
              className="relative aspect-[9/16] rounded-md overflow-hidden bg-muted"
            >
              <Image
                src={thumb}
                alt={`Frame ${index + 1}`}
                fill
                className="object-cover"
                unoptimized // For external URLs
              />
              <div className="absolute bottom-1 left-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                {index + 1}
              </div>
            </div>
          ))}
        </div>
        {thumbnails.length === 0 && (
          <div className="aspect-[9/16] max-w-[180px] rounded-md bg-muted flex items-center justify-center text-muted-foreground text-sm">
            No preview available
          </div>
        )}
      </div>

      {/* Audio Player */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Volume2 className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Voiceover Audio</h3>
          <span className="text-xs text-muted-foreground">
            ({formatDuration(duration)})
          </span>
        </div>
        {audioUrl ? (
          <audio controls className="w-full" preload="metadata">
            <source src={audioUrl} type="audio/wav" />
            Your browser does not support the audio element.
          </audio>
        ) : (
          <div className="h-12 rounded-md bg-muted flex items-center justify-center text-muted-foreground text-sm">
            Audio not available
          </div>
        )}
      </div>
    </div>
  );
}
