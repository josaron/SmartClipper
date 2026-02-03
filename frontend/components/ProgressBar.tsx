"use client";

import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

interface Step {
  id: string;
  label: string;
  status: "pending" | "in_progress" | "completed";
}

interface ProgressBarProps {
  progress: number;
  status: string;
  message: string;
}

const STEPS: { id: string; label: string; statuses: string[] }[] = [
  { id: "download", label: "Downloading video", statuses: ["downloading"] },
  { id: "audio", label: "Generating voiceover", statuses: ["generating_audio"] },
  { id: "video", label: "Processing video", statuses: ["processing_video"] },
  { id: "finalize", label: "Finalizing", statuses: ["finalizing"] },
];

function getStepStatus(
  step: { id: string; label: string; statuses: string[] },
  currentStatus: string
): "pending" | "in_progress" | "completed" {
  const statusIndex = STEPS.findIndex((s) => s.statuses.includes(currentStatus));
  const stepIndex = STEPS.indexOf(step);

  if (currentStatus === "completed") return "completed";
  if (stepIndex < statusIndex) return "completed";
  if (stepIndex === statusIndex) return "in_progress";
  return "pending";
}

export function ProgressBar({ progress, status, message }: ProgressBarProps) {
  return (
    <div className="space-y-6">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{message}</span>
          <span className="font-medium">{progress}%</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {STEPS.map((step) => {
          const stepStatus = getStepStatus(step, status);
          return (
            <div
              key={step.id}
              className="flex items-center gap-3 text-sm"
            >
              {stepStatus === "completed" ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : stepStatus === "in_progress" ? (
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              ) : (
                <Circle className="w-5 h-5 text-muted-foreground" />
              )}
              <span
                className={
                  stepStatus === "pending"
                    ? "text-muted-foreground"
                    : stepStatus === "in_progress"
                    ? "text-primary font-medium"
                    : "text-foreground"
                }
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
