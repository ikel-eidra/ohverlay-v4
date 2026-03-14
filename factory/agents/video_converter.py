"""
Video-to-Overlay Converter Agent - Ohverlay Factory
=====================================================
Server-side video processing using FFmpeg.

Converts any video into an Ohverlay-style transparent overlay:
  1. Wireframe  - Edge detection (Sobel/Canny), neon glow
  2. Glow       - Luminance key (dark = transparent, bright = glow)
  3. Ghost      - Semi-transparent apparition with color tint
  4. Silhouette - Solid color cutout of bright regions
  5. Chroma Key - Green screen removal

Pipeline:
  Input video → FFmpeg processing → WebM (VP9 alpha) or overlay HTML

FFmpeg filters used:
  - edgedetect (wireframe/edge extraction)
  - colorkey (chroma key / green screen)
  - lumakey (luminance transparency)
  - colorchannelmixer (tinting)
  - gblur (glow effect)
  - blend (compositing)

Requires: FFmpeg with libvpx-vp9 support
"""

import os
import subprocess
import shutil
import json
import time
from typing import Optional
from pathlib import Path


class VideoConverterAgent:
    """Server-side video-to-overlay converter using FFmpeg."""

    MODES = ["wireframe", "glow", "ghost", "silhouette", "chroma"]

    # Ohverlay glow colors (hex → FFmpeg color format)
    COLORS = {
        "cyan":    "0x00D4FF",
        "magenta": "0xFF00FF",
        "green":   "0x00FF96",
        "orange":  "0xFF6600",
        "white":   "0xFFFFFF",
        "pink":    "0xFF3366",
    }

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "overlays", "converted"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")

    @property
    def available(self):
        return self.ffmpeg is not None

    def get_video_info(self, input_path):
        """Get video metadata using ffprobe."""
        if not self.ffprobe or not os.path.exists(input_path):
            return None

        try:
            result = subprocess.run(
                [
                    self.ffprobe, "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    input_path,
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        return {
                            "width": int(stream.get("width", 0)),
                            "height": int(stream.get("height", 0)),
                            "duration": float(data.get("format", {}).get("duration", 0)),
                            "fps": eval(stream.get("r_frame_rate", "30/1")),
                            "codec": stream.get("codec_name", ""),
                        }
        except Exception:
            pass
        return None

    def convert(
        self,
        input_path,
        mode="wireframe",
        color="cyan",
        opacity=0.7,
        threshold=0.3,
        glow=0.6,
        scale=1.0,
        max_duration=None,
        output_format="webm",
        output_name=None,
    ):
        """
        Convert a video file into an Ohverlay-style transparent overlay.

        Args:
            input_path: Source video file
            mode: wireframe, glow, ghost, silhouette, chroma
            color: cyan, magenta, green, orange, white, pink
            opacity: 0.0 - 1.0
            threshold: Edge/luma threshold 0.0 - 1.0
            glow: Glow intensity 0.0 - 1.0
            scale: Output scale factor
            max_duration: Limit output duration (seconds)
            output_format: webm (alpha) or mp4 (no alpha, for preview)
            output_name: Custom output filename

        Returns:
            dict with {path, mode, duration, size} or None on failure
        """
        if not self.available:
            return {"error": "FFmpeg not found"}

        if not os.path.exists(input_path):
            return {"error": f"Input file not found: {input_path}"}

        if mode not in self.MODES:
            mode = "wireframe"

        color_hex = self.COLORS.get(color, self.COLORS["cyan"])

        # Build output path
        if not output_name:
            base = Path(input_path).stem
            output_name = f"{base}-{mode}-ohverlay"

        ext = "webm" if output_format == "webm" else "mp4"
        output_path = os.path.join(self.output_dir, f"{output_name}.{ext}")

        # Build FFmpeg filter chain
        filters = self._build_filter(mode, color_hex, opacity, threshold, glow, scale)

        # Build command
        cmd = [self.ffmpeg, "-y", "-i", input_path]

        if max_duration:
            cmd.extend(["-t", str(max_duration)])

        cmd.extend(["-vf", filters])

        if output_format == "webm":
            # WebM VP9 with alpha channel
            cmd.extend([
                "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p",
                "-auto-alt-ref", "0",
                "-b:v", "2M",
                "-an",  # No audio for overlays
            ])
        else:
            # MP4 for preview (no alpha)
            cmd.extend([
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", "23",
                "-an",
            ])

        cmd.append(output_path)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
            )

            if result.returncode != 0:
                return {"error": f"FFmpeg failed: {result.stderr[:500]}"}

            # Get output info
            size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            info = self.get_video_info(output_path)

            return {
                "path": output_path,
                "mode": mode,
                "color": color,
                "format": output_format,
                "duration": info["duration"] if info else 0,
                "width": info["width"] if info else 0,
                "height": info["height"] if info else 0,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
            }

        except subprocess.TimeoutExpired:
            return {"error": "Conversion timed out (10 min limit)"}
        except Exception as e:
            return {"error": str(e)}

    def _build_filter(self, mode, color_hex, opacity, threshold, glow, scale):
        """Build the FFmpeg filter chain for the given mode."""
        filters = []

        # Scale if needed
        if scale != 1.0:
            filters.append(f"scale=iw*{scale}:ih*{scale}")

        if mode == "wireframe":
            # Edge detection → colorize → glow
            t = max(0.05, min(0.95, threshold))
            filters.append(f"edgedetect=low={t*0.4}:high={t}:mode=colormix")
            # Make dark areas transparent using lumakey
            filters.append("lumakey=threshold=0.08:tolerance=0.05:softness=0.1")
            # Tint with glow color
            r = int(color_hex[2:4], 16) / 255
            g_val = int(color_hex[4:6], 16) / 255
            b = int(color_hex[6:8], 16) / 255
            filters.append(
                f"colorchannelmixer={r}:0:0:0:0:{g_val}:0:0:0:0:{b}:0"
            )
            # Glow via blur+blend
            if glow > 0.1:
                blur_size = max(1, int(glow * 12)) | 1  # Must be odd
                filters.append(
                    f"split[a][b];[b]gblur=sigma={blur_size}[blur];"
                    f"[a][blur]blend=all_mode=screen:all_opacity={glow*0.5}"
                )

        elif mode == "glow":
            # Luminance key: dark = transparent
            luma_thresh = max(0.05, threshold * 0.4)
            filters.append(
                f"lumakey=threshold={luma_thresh}:tolerance=0.1:softness=0.15"
            )
            r = int(color_hex[2:4], 16) / 255
            g_val = int(color_hex[4:6], 16) / 255
            b = int(color_hex[6:8], 16) / 255
            filters.append(
                f"colorchannelmixer={r}:0:0:0:0:{g_val}:0:0:0:0:{b}:0"
            )
            if glow > 0.1:
                blur_size = max(1, int(glow * 15)) | 1
                filters.append(
                    f"split[a][b];[b]gblur=sigma={blur_size}[blur];"
                    f"[a][blur]blend=all_mode=screen:all_opacity={glow*0.4}"
                )

        elif mode == "ghost":
            # Semi-transparent with color tint
            r = int(color_hex[2:4], 16) / 255
            g_val = int(color_hex[4:6], 16) / 255
            b = int(color_hex[6:8], 16) / 255
            filters.append(
                f"colorchannelmixer="
                f"{0.3+r*0.7}:0:0:0:"
                f"0:{0.3+g_val*0.7}:0:0:"
                f"0:0:{0.3+b*0.7}:0"
            )
            filters.append(f"format=rgba,colorchannelmixer=aa={opacity * 0.6}")
            if glow > 0.1:
                blur_size = max(1, int(glow * 18)) | 1
                filters.append(
                    f"split[a][b];[b]gblur=sigma={blur_size}[blur];"
                    f"[a][blur]blend=all_mode=screen:all_opacity={glow*0.25}"
                )

        elif mode == "silhouette":
            # Threshold → solid color
            luma_thresh = max(0.05, threshold * 0.4)
            filters.append(
                f"lumakey=threshold={luma_thresh}:tolerance=0.08:softness=0.05"
            )
            r = int(color_hex[2:4], 16) / 255
            g_val = int(color_hex[4:6], 16) / 255
            b = int(color_hex[6:8], 16) / 255
            filters.append(
                f"colorchannelmixer={r}:0:0:0:0:{g_val}:0:0:0:0:{b}:0"
            )

        elif mode == "chroma":
            # Green screen removal
            filters.append(
                f"chromakey=0x00B140:similarity={threshold*0.5}:blend=0.1"
            )
            r = int(color_hex[2:4], 16) / 255
            g_val = int(color_hex[4:6], 16) / 255
            b = int(color_hex[6:8], 16) / 255
            filters.append(
                f"colorchannelmixer="
                f"{0.4+r*0.6}:0:0:0:"
                f"0:{0.4+g_val*0.6}:0:0:"
                f"0:0:{0.4+b*0.6}:0"
            )

        # Global opacity
        if opacity < 1.0 and mode != "ghost":
            filters.append(f"format=rgba,colorchannelmixer=aa={opacity}")

        return ",".join(filters) if filters else "null"

    def generate_overlay_html(self, webm_path, overlay_name=None):
        """
        Generate a self-contained overlay HTML file that plays the converted WebM.
        The WebM is embedded as base64 data URI.
        """
        import base64

        if not os.path.exists(webm_path):
            return None

        # For large files, don't embed (link instead)
        file_size = os.path.getsize(webm_path)
        embed = file_size < 10 * 1024 * 1024  # Embed if under 10MB

        if embed:
            with open(webm_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            video_src = f"data:video/webm;base64,{b64}"
        else:
            video_src = os.path.basename(webm_path)

        name = overlay_name or Path(webm_path).stem

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Ohverlay - {name}</title>
<style>
  * {{ margin: 0; padding: 0; }}
  body {{ background: transparent; overflow: hidden; }}
  video {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 100vw;
    max-height: 100vh;
    mix-blend-mode: screen;
    pointer-events: none;
  }}
</style>
</head>
<body>
<video autoplay loop muted playsinline>
  <source src="{video_src}" type="video/webm">
</video>
</body>
</html>"""

        html_path = os.path.join(self.output_dir, f"{name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return html_path

    def batch_convert(self, input_path, colors=None, modes=None):
        """
        Generate multiple overlay variations from a single video.
        Useful for factory daily drops.
        """
        if colors is None:
            colors = ["cyan", "magenta", "green"]
        if modes is None:
            modes = ["wireframe", "glow", "ghost"]

        results = []
        for mode in modes:
            for color in colors:
                result = self.convert(
                    input_path,
                    mode=mode,
                    color=color,
                    max_duration=30,  # Cap at 30 seconds for overlays
                )
                if result and "error" not in result:
                    results.append(result)

        return results
