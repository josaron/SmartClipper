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
  video: File;
  script_input: string;
  voice: string;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
}

export type UploadProgressCallback = (progress: number) => void;

// Fetch available voices
export async function getVoices(): Promise<Voice[]> {
  const response = await fetch(`${API_URL}/jobs/voices`);
  if (!response.ok) {
    throw new Error("Failed to fetch voices");
  }
  const data = await response.json();
  return data.voices;
}

// Create a new job with file upload
export async function createJob(
  request: CreateJobRequest,
  onProgress?: UploadProgressCallback
): Promise<CreateJobResponse> {
  const formData = new FormData();
  formData.append("video", request.video);
  formData.append("script_input", request.script_input);
  formData.append("voice", request.voice);

  // Use XMLHttpRequest for upload progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new Error("Invalid response from server"));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || "Failed to create job"));
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Upload cancelled"));
    });

    xhr.open("POST", `${API_URL}/jobs`);
    xhr.send(formData);
  });
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
