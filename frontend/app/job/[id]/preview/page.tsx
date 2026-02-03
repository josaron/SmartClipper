"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PreviewPlayer } from "@/components/PreviewPlayer";
import { getJobPreview, getDownloadUrl, type JobPreview } from "@/lib/api";
import { ArrowLeft, Download, CheckCircle2 } from "lucide-react";

export default function PreviewPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [preview, setPreview] = useState<JobPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    async function loadPreview() {
      try {
        const data = await getJobPreview(jobId);
        setPreview(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load preview");
      }
    }

    loadPreview();
  }, [jobId]);

  const handleDownload = () => {
    setIsDownloading(true);
    const downloadUrl = getDownloadUrl(jobId);
    
    // Create a temporary link to trigger download
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `smartclipper_${jobId}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Reset button after a short delay
    setTimeout(() => setIsDownloading(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Button
        variant="ghost"
        onClick={() => router.push("/")}
        className="gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Create Another
      </Button>

      {/* Success Banner */}
      <div className="flex items-center gap-3 p-4 rounded-lg bg-green-50 border border-green-200 text-green-800">
        <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
        <div>
          <p className="font-medium">Your short is ready!</p>
          <p className="text-sm text-green-700">
            Preview below and download when ready.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
          <CardDescription>
            Review your short before downloading
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="p-4 rounded-md bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          ) : preview ? (
            <PreviewPlayer
              thumbnails={preview.thumbnails}
              audioUrl={preview.audio_url}
              duration={preview.duration}
            />
          ) : (
            <div className="flex items-center justify-center py-8">
              <div className="animate-pulse text-muted-foreground">
                Loading preview...
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Download Section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="flex-1 text-center sm:text-left">
              <p className="font-medium">Download MP4</p>
              <p className="text-sm text-muted-foreground">
                720x1280 (9:16) • H.264 • AAC Audio
              </p>
            </div>
            <Button
              size="lg"
              onClick={handleDownload}
              disabled={isDownloading || !preview}
              className="w-full sm:w-auto gap-2"
            >
              <Download className="w-4 h-4" />
              {isDownloading ? "Downloading..." : "Download Video"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tips */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <h3 className="font-medium mb-2">Tips for uploading</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• YouTube Shorts: Upload directly, it will auto-detect the format</li>
            <li>• TikTok: Upload as-is, add captions in their editor</li>
            <li>• Instagram Reels: Works perfectly with 9:16 aspect ratio</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
