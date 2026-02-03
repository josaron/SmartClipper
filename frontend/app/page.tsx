"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScriptInput } from "@/components/ScriptInput";
import { VoiceSelector } from "@/components/VoiceSelector";
import { createJob, getVoices, type Voice } from "@/lib/api";
import { parseScriptInput } from "@/lib/parser";
import { Loader2, Video, Sparkles, Clock, Upload, FileVideo, X } from "lucide-react";

const MAX_FILE_SIZE_MB = 100;
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024;

export default function HomePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [scriptInput, setScriptInput] = useState("");
  const [voice, setVoice] = useState("en_US-lessac-medium");
  const [voices, setVoices] = useState<Voice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Validate script input in real-time
  const parseResult = useMemo(() => {
    if (!scriptInput.trim()) return null;
    return parseScriptInput(scriptInput);
  }, [scriptInput]);

  const hasValidSegments = (parseResult?.segments.length ?? 0) > 0;
  const canSubmit = videoFile && hasValidSegments && !isLoading;

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("video/")) {
      setError("Please select a video file (MP4, MOV, etc.)");
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE_MB}MB`);
      return;
    }

    setError(null);
    setVideoFile(file);
  };

  // Handle file drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("video/")) {
      setError("Please select a video file (MP4, MOV, etc.)");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE_MB}MB`);
      return;
    }

    setError(null);
    setVideoFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const clearFile = () => {
    setVideoFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

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
    setUploadProgress(0);

    try {
      // Validate inputs
      if (!videoFile) {
        throw new Error("Please select a video file");
      }
      if (!scriptInput.trim()) {
        throw new Error("Please enter the script with timestamps");
      }
      if (!hasValidSegments) {
        throw new Error("No valid script segments found. Check the format.");
      }

      // Create job with file upload
      const response = await createJob(
        {
          video: videoFile,
          script_input: scriptInput,
          voice,
        },
        (progress) => setUploadProgress(progress)
      );

      // Navigate to job status page
      router.push(`/job/${response.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">
          Create Shorts in Minutes
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
            Upload your video and add the script you created with Gemini
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Video Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">
                Source Video
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!videoFile ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-gray-50 transition-colors"
                >
                  <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
                  <p className="text-sm font-medium text-gray-700">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    MP4, MOV up to {MAX_FILE_SIZE_MB}MB
                  </p>
                </div>
              ) : (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <FileVideo className="w-8 h-8 text-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{videoFile.name}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(videoFile.size)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={clearFile}
                      className="p-1 hover:bg-gray-200 rounded"
                      disabled={isLoading}
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                  
                  {/* Upload progress */}
                  {isLoading && uploadProgress > 0 && (
                    <div className="mt-3">
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Uploading... {uploadProgress}%
                      </p>
                    </div>
                  )}
                </div>
              )}
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
