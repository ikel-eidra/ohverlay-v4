"""
Video-to-Overlay Pipeline - Ohverlay Factory
==============================================
End-to-end pipeline:
  AI prompt → Video generation → FFmpeg conversion → OVL packaging → Deploy

This is the internal engine that n8n workflows call to produce overlays
from video content automatically.
"""

import os
import time
import json
import uuid
from typing import Optional, Dict
from pathlib import Path

# Import factory agents
try:
    from factory.agents.video_converter import VideoConverterAgent
except ImportError:
    VideoConverterAgent = None

try:
    from factory.agents.overlay_creator import OverlayCreatorAgent
except ImportError:
    OverlayCreatorAgent = None

try:
    from ovl.parser import parse_ovl
    from ovl.compiler import compile_ovl
    HAS_OVL = True
except ImportError:
    HAS_OVL = False


class PipelineJob:
    """Represents a single pipeline job."""

    STATUSES = ("queued", "processing", "converting", "compiling", "done", "failed")

    def __init__(self, job_type, input_data=None):
        self.id = str(uuid.uuid4())[:12]
        self.type = job_type
        self.status = "queued"
        self.input_data = input_data or {}
        self.output = {}
        self.error = None
        self.created_at = time.time()
        self.updated_at = time.time()
        self.progress = 0  # 0-100

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "output": self.output,
            "error": self.error,
            "created_at": self.created_at,
        }


class VideoPipeline:
    """
    Main pipeline orchestrator.

    Flows:
    1. video_to_overlay(video_path) → overlay HTML
    2. prompt_to_overlay(text_prompt) → AI video → overlay HTML
    3. ovl_to_overlay(ovl_source) → compiled HTML
    4. daily_drop() → batch generate overlays for today
    """

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "overlays", "pipeline_output"
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.converter = VideoConverterAgent(output_dir=self.output_dir) if VideoConverterAgent else None
        self.creator = OverlayCreatorAgent() if OverlayCreatorAgent else None

        # Job queue (in-memory, Redis in production)
        self.jobs: Dict[str, PipelineJob] = {}

    # ─── Pipeline 1: Video → Overlay ───

    def video_to_overlay(
        self,
        video_path,
        mode="wireframe",
        color="cyan",
        opacity=0.7,
        glow=0.6,
        max_duration=30,
    ) -> PipelineJob:
        """
        Convert a video file to an overlay.

        Steps:
        1. Validate video
        2. FFmpeg convert to WebM with alpha
        3. Generate overlay HTML wrapper
        4. Register in catalog
        """
        job = PipelineJob("video_to_overlay", {
            "video_path": video_path,
            "mode": mode,
            "color": color,
        })
        self.jobs[job.id] = job

        if not self.converter or not self.converter.available:
            job.status = "failed"
            job.error = "FFmpeg not available"
            return job

        if not os.path.exists(video_path):
            job.status = "failed"
            job.error = f"Video not found: {video_path}"
            return job

        # Step 1: Get video info
        job.status = "processing"
        job.progress = 10
        info = self.converter.get_video_info(video_path)

        if not info:
            job.status = "failed"
            job.error = "Could not read video file"
            return job

        # Step 2: FFmpeg conversion
        job.status = "converting"
        job.progress = 30
        result = self.converter.convert(
            video_path,
            mode=mode,
            color=color,
            opacity=opacity,
            glow=glow,
            max_duration=max_duration,
            output_format="webm",
        )

        if not result or "error" in result:
            job.status = "failed"
            job.error = result.get("error", "Conversion failed") if result else "Conversion returned nothing"
            return job

        # Step 3: Generate HTML wrapper
        job.status = "compiling"
        job.progress = 70
        webm_path = result["path"]
        html_path = self.converter.generate_overlay_html(webm_path)

        # Step 4: Done
        job.status = "done"
        job.progress = 100
        job.output = {
            "webm_path": webm_path,
            "html_path": html_path,
            "mode": mode,
            "color": color,
            "duration": result.get("duration", 0),
            "size_mb": result.get("size_mb", 0),
        }

        return job

    # ─── Pipeline 2: Text Prompt → Overlay (AI-generated) ───

    def prompt_to_overlay(self, description, category="ambient") -> PipelineJob:
        """
        Generate an overlay from a text description using AI.
        Uses Groq Llama to generate HTML canvas code directly.

        For video-based generation (future):
        1. AI generates video from prompt (Kling/Runway/Sora)
        2. FFmpeg converts to transparent overlay
        3. Package as HTML
        """
        job = PipelineJob("prompt_to_overlay", {
            "description": description,
            "category": category,
        })
        self.jobs[job.id] = job

        if not self.creator:
            job.status = "failed"
            job.error = "Overlay creator agent not available"
            return job

        # Generate via AI
        job.status = "processing"
        job.progress = 30

        result = self.creator.create_overlay(description, category)

        if not result:
            job.status = "failed"
            job.error = "AI generation failed"
            return job

        job.status = "done"
        job.progress = 100
        job.output = result

        return job

    # ─── Pipeline 3: OVL → Overlay ───

    def ovl_to_overlay(self, ovl_source, output_name=None) -> PipelineJob:
        """
        Compile OVL source code into an overlay HTML file.
        """
        job = PipelineJob("ovl_compile", {"source_length": len(ovl_source)})
        self.jobs[job.id] = job

        if not HAS_OVL:
            job.status = "failed"
            job.error = "OVL compiler not available"
            return job

        job.status = "compiling"
        job.progress = 50

        try:
            nodes = parse_ovl(ovl_source)
            if not nodes:
                job.status = "failed"
                job.error = "No overlay blocks found in OVL source"
                return job

            html = compile_ovl(nodes)
            name = output_name or nodes[0].name.lower().replace(" ", "-") or "overlay"
            out_path = os.path.join(self.output_dir, f"{name}.html")

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)

            job.status = "done"
            job.progress = 100
            job.output = {
                "html_path": out_path,
                "name": nodes[0].name,
                "size_kb": round(len(html) / 1024, 1),
                "creatures": sum(1 for n in nodes[0].children if n.type == "creature"),
                "particles": sum(1 for n in nodes[0].children if n.type == "particles"),
            }

        except Exception as e:
            job.status = "failed"
            job.error = str(e)

        return job

    # ─── Pipeline 4: Daily Drop ───

    def daily_drop(self, count=3) -> list:
        """
        Generate today's daily overlay drops.
        Called by n8n scheduled workflow.

        Mixes AI-generated canvas overlays and (future) video-based overlays.
        """
        jobs = []

        if self.creator:
            results = self.creator.create_daily_overlays(count)
            for result in results:
                job = PipelineJob("daily_drop")
                job.status = "done"
                job.progress = 100
                job.output = result
                self.jobs[job.id] = job
                jobs.append(job)

        return jobs

    # ─── Job Management ───

    def get_job(self, job_id) -> Optional[PipelineJob]:
        return self.jobs.get(job_id)

    def list_jobs(self, status=None, limit=20):
        jobs = sorted(self.jobs.values(), key=lambda j: j.created_at, reverse=True)
        if status:
            jobs = [j for j in jobs if j.status == status]
        return [j.to_dict() for j in jobs[:limit]]
