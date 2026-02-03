const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Voice {
  id: string;
  name: string;
  language: string;
}

export interface JobProgress {
  status: string;
  progress: number;
  message: string;
  error?: string;
}

export interface JobPreview {
  thumbnails: string[];
  audio_url: string;
  duration: number;
}

export interface CreateJobRequest {
  youtube_url: string;
  script_input: string;
  voice: string;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
}

// Fetch available voices
export async function getVoices(): Promise<Voice[]> {
  const response = await fetch(`${API_URL}/jobs/voices`);
  if (!response.ok) {
    throw new Error("Failed to fetch voices");
  }
  const data = await response.json();
  return data.voices;
}

// Create a new job
export async function createJob(request: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create job");
  }

  return response.json();
}

// Get job status
export async function getJobStatus(jobId: string): Promise<JobProgress> {
  const response = await fetch(`${API_URL}/jobs/${jobId}/status`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return response.json();
}

// Get job preview
export async function getJobPreview(jobId: string): Promise<JobPreview> {
  const response = await fetch(`${API_URL}/jobs/${jobId}/preview`);
  if (!response.ok) {
    throw new Error("Failed to fetch job preview");
  }
  const data = await response.json();
  
  // Prefix URLs with API base
  return {
    ...data,
    thumbnails: data.thumbnails.map((t: string) => `${API_URL}${t}`),
    audio_url: data.audio_url ? `${API_URL}${data.audio_url}` : "",
  };
}

// Get download URL
export function getDownloadUrl(jobId: string): string {
  return `${API_URL}/jobs/${jobId}/download`;
}
