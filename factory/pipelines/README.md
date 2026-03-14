# Ohverlay Factory Pipelines

## n8n Workflow Pipelines

These are the automated workflows that run inside the factory's n8n instance.

### Pipeline 1: Daily Overlay Drop
```
Schedule (6 AM Manila)
  → AI generates video prompt
  → Send to AI video API (Kling/Runway/Sora)
  → Wait for video completion
  → FFmpeg converts to WebM alpha (wireframe/glow/ghost)
  → OVL compiler packages as overlay HTML
  → Upload to factory overlay catalog
  → Push notification to desktop apps
  → Post preview to ohverlay.com/daily
```

### Pipeline 2: Video-to-Overlay on Demand
```
User uploads video (web or API)
  → Validate file (format, size, duration)
  → Queue conversion job
  → FFmpeg processes (user-selected mode)
  → Generate overlay HTML
  → Store in user's overlay library
  → Return download link
```

### Pipeline 3: OVL Compilation Pipeline
```
User submits .ovl file (web editor or API)
  → OVL parser validates syntax
  → OVL compiler generates HTML
  → Preview rendered (headless browser screenshot)
  → Store in overlay catalog
  → Return preview + download
```

### Pipeline 4: Content Curation
```
Schedule (every 4 hours)
  → Fetch news from RSS feeds
  → Fetch weather data
  → Fetch crypto prices
  → AI summarizes headlines
  → Generate wellness tips
  → Package as daily content JSON
  → Cache in Redis
  → Available via /api/v1/news, /weather, /tickers
```

### Pipeline 5: AI Video Generation
```
Internal or scheduled trigger
  → Generate creative prompt (themes, seasons, trending)
  → Call AI video generation API:
    - Kling AI (free tier available)
    - Runway Gen-3
    - Pika Labs
    - Stable Video Diffusion (self-hosted)
  → Download generated video
  → Auto-convert through Pipeline 2
  → Tag and categorize
  → Add to daily drop queue
```

## API Endpoints for Pipelines

```
POST /api/v1/pipeline/video-upload     Upload video for conversion
POST /api/v1/pipeline/ovl-compile      Submit OVL source for compilation
GET  /api/v1/pipeline/status/{job_id}  Check pipeline job status
GET  /api/v1/pipeline/daily-queue      View upcoming daily drops
```

## Environment Setup

The pipelines run inside the n8n container (port 5678).
Configure API keys in the factory `.env` file.

AI Video APIs to explore:
- Kling AI: https://klingai.com (free tier)
- Runway: https://runwayml.com
- Pika: https://pika.art
- Stable Video: Self-hosted via ComfyUI
