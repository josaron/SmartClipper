# SmartClipper - YouTube Shorts Generator

Transform long-form YouTube videos into engaging 45-75 second shorts with AI-powered voiceover and intelligent subject tracking.

## Features

- **Smart Cropping**: Automatically tracks faces/subjects using MediaPipe and crops to 9:16 (720x1280)
- **AI Voiceover**: Natural TTS using Piper with multiple voice options
- **Script-Based Editing**: Uses timestamps from your Gemini-generated script to select footage
- **Quick Export**: Generates download-ready MP4 files

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────┐
│  Vercel         │     │  Render                             │
│  (Frontend)     │     │  (Backend)                          │
│                 │     │                                     │
│  Next.js 14     │────▶│  FastAPI + Python                   │
│  Tailwind CSS   │     │  ├── yt-dlp (download)              │
│  shadcn/ui      │     │  ├── Piper TTS (voiceover)          │
│                 │     │  ├── FFmpeg (video processing)      │
│                 │     │  └── MediaPipe (subject detection)  │
└─────────────────┘     └─────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- FFmpeg
- Docker (recommended for backend)

### Local Development

#### Backend

```bash
cd backend

# Option 1: Docker (recommended)
docker build -t smartclipper-api .
docker run -p 8000:8000 smartclipper-api

# Option 2: Local Python
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
# Download Piper voice models manually to /app/voices/
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Input Format

The app expects a pipe-delimited script input (one segment per line):

```
Script text here|MM:SS|Description of footage
Another line of script|MM:SS|Another description
```

Example:
```
Did you know a 51-foot fire-breathing dragon used to live on the Las Vegas Strip?|23:23|Close up of Murphy the Dragon
This is Murphy. He was the star of the Excalibur Hotel.|24:02|Murphy emerging from the cave
```

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your repository
3. Select "Docker" as the environment
4. Set environment variables:
   - `CORS_ORIGINS`: Your Vercel frontend URL

The included `render.yaml` will configure the service automatically.

### Frontend (Vercel)

1. Import project to Vercel
2. Set the root directory to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs/voices` | List available TTS voices |
| POST | `/jobs` | Create a new processing job |
| GET | `/jobs/{id}/status` | Get job progress |
| GET | `/jobs/{id}/preview` | Get preview thumbnails + audio |
| GET | `/jobs/{id}/download` | Download final MP4 |
| DELETE | `/jobs/{id}` | Delete job and files |

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Lucide icons

### Backend
- FastAPI (Python)
- yt-dlp (YouTube download)
- Piper TTS (text-to-speech)
- FFmpeg (video processing)
- MediaPipe (face/pose detection)
- OpenCV (image processing)

## Workflow

1. Use Gemini to analyze a YouTube video and generate a script with timestamps
2. Paste the YouTube URL and script into SmartClipper
3. Select your preferred voice
4. Wait for processing (2-5 minutes)
5. Preview and download your short

## Limitations

- No persistent storage (files cleared on server restart)
- Processing time depends on video length
- Render free tier has limited resources (recommend Starter plan)
- MediaPipe may not detect subjects in all videos (fallback: center crop)

## License

MIT
