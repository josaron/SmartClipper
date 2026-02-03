"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScriptInput } from "@/components/ScriptInput";
import { VoiceSelector } from "@/components/VoiceSelector";
import { createJob, getVoices, type Voice } from "@/lib/api";
import { parseScriptInput } from "@/lib/parser";
import { Loader2, Video, Sparkles, Clock } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [scriptInput, setScriptInput] = useState("");
  const [voice, setVoice] = useState("en_US-lessac-medium");
  const [voices, setVoices] = useState<Voice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validate script input in real-time
  const parseResult = useMemo(() => {
    if (!scriptInput.trim()) return null;
    return parseScriptInput(scriptInput);
  }, [scriptInput]);

  const hasValidSegments = (parseResult?.segments.length ?? 0) > 0;
  const canSubmit = youtubeUrl.trim() && hasValidSegments && !isLoading;

  // Fetch available voices on mount
  useEffect(() => {
    async function loadVoices() {
      try {
        const voiceList = await getVoices();
        setVoices(voiceList);
        if (voiceList.length > 0) {
          setVoice(voiceList[0].id);
        }
      } catch (err) {
        // Use default voices if API is unavailable
        setVoices([
          { id: "en_US-lessac-medium", name: "Lessac (US Male)", language: "en-US" },
          { id: "en_US-amy-medium", name: "Amy (US Female)", language: "en-US" },
          { id: "en_GB-alan-medium", name: "Alan (UK Male)", language: "en-GB" },
        ]);
      }
    }
    loadVoices();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Validate inputs
      if (!youtubeUrl.trim()) {
        throw new Error("Please enter a YouTube URL");
      }
      if (!scriptInput.trim()) {
        throw new Error("Please enter the script with timestamps");
      }
      if (!hasValidSegments) {
        throw new Error("No valid script segments found. Check the format.");
      }

      // Create job
      const response = await createJob({
        youtube_url: youtubeUrl,
        script_input: scriptInput,
        voice,
      });

      // Navigate to job status page
      router.push(`/job/${response.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">
          Create YouTube Shorts in Minutes
        </h1>
        <p className="text-lg text-muted-foreground">
          Transform long-form videos into engaging 45-75 second shorts with AI voiceover
        </p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="p-4 rounded-lg bg-white shadow-sm">
          <Video className="w-6 h-6 mx-auto mb-2 text-primary" />
          <p className="text-sm font-medium">Smart Cropping</p>
          <p className="text-xs text-muted-foreground">Auto-tracks subjects</p>
        </div>
        <div className="p-4 rounded-lg bg-white shadow-sm">
          <Sparkles className="w-6 h-6 mx-auto mb-2 text-primary" />
          <p className="text-sm font-medium">AI Voiceover</p>
          <p className="text-xs text-muted-foreground">Natural TTS audio</p>
        </div>
        <div className="p-4 rounded-lg bg-white shadow-sm">
          <Clock className="w-6 h-6 mx-auto mb-2 text-primary" />
          <p className="text-sm font-medium">Quick Export</p>
          <p className="text-xs text-muted-foreground">720x1280 MP4</p>
        </div>
      </div>

      {/* Main Form */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Short</CardTitle>
          <CardDescription>
            Enter your YouTube video URL and the script you created with Gemini
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* YouTube URL */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">
                YouTube URL
              </label>
              <Input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                required
              />
            </div>

            {/* Script Input */}
            <ScriptInput value={scriptInput} onChange={setScriptInput} />

            {/* Voice Selector */}
            <VoiceSelector
              voices={voices}
              value={voice}
              onChange={setVoice}
              disabled={isLoading}
            />

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={!canSubmit}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating job...
                </>
              ) : (
                "Generate Short"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
