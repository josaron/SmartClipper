"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/ProgressBar";
import { getJobStatus, type JobProgress } from "@/lib/api";
import { AlertCircle, ArrowLeft } from "lucide-react";

export default function JobStatusPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    try {
      const status = await getJobStatus(jobId);
      setJobProgress(status);

      // Navigate to preview when complete
      if (status.status === "completed") {
        router.push(`/job/${jobId}/preview`);
        return false; // Stop polling
      }

      // Stop polling on failure
      if (status.status === "failed") {
        setError(status.error || "Processing failed");
        return false;
      }

      return true; // Continue polling
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch status");
      return false;
    }
  }, [jobId, router]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    async function startPolling() {
      // Initial fetch
      const shouldContinue = await pollStatus();

      if (shouldContinue) {
        // Poll every 3 seconds
        intervalId = setInterval(async () => {
          const continuePolling = await pollStatus();
          if (!continuePolling) {
            clearInterval(intervalId);
          }
        }, 3000);
      }
    }

    startPolling();

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [pollStatus]);

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <Button
        variant="ghost"
        onClick={() => router.push("/")}
        className="gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Home
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Processing Your Short</CardTitle>
          <CardDescription>
            Job ID: <code className="text-xs bg-muted px-1 rounded">{jobId}</code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 rounded-md bg-destructive/10 text-destructive">
                <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Processing Failed</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </div>
              <Button onClick={() => router.push("/")} className="w-full">
                Try Again
              </Button>
            </div>
          ) : jobProgress ? (
            <ProgressBar
              progress={jobProgress.progress}
              status={jobProgress.status}
              message={jobProgress.message}
            />
          ) : (
            <div className="flex items-center justify-center py-8">
              <div className="animate-pulse text-muted-foreground">
                Loading...
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info card */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">
            Processing typically takes 2-5 minutes depending on video length.
            You can leave this page open or bookmark it to check back later.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
