"""
Overlay Creator Agent - Ohverlay Factory
==========================================
Resident AI agent that generates new HTML overlay animations.

Uses Groq (Llama 3.3 70B free) to:
- Generate new canvas-based overlay HTML files
- Create variations of existing overlays (color themes, sizes)
- Design seasonal/holiday overlays automatically
- Produce daily "overlay drops" for users

Triggered by:
- n8n scheduled workflows (daily at 6 AM)
- Manual API call from factory admin
- User requests via Blue chatbot
"""

import os
import json
import time
from typing import Optional
from factory.factory_config import GROQ_API_KEY, AGENT_LLM_MODEL

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class OverlayCreatorAgent:
    """AI agent that generates new overlay HTML files."""

    SYSTEM_PROMPT = """You are the Overlay Creator, a resident AI agent at the Ohverlay Factory.
You create beautiful, lightweight HTML5 Canvas overlay animations for desktop screens.

RULES for overlay generation:
1. Single HTML file, no external dependencies
2. Use HTML5 Canvas 2D API only (no WebGL, no libraries)
3. Transparent background (body background: transparent)
4. Smooth 60fps animations using requestAnimationFrame
5. Wireframe/glowing aesthetic (neon lines, particles, gradients)
6. File must be under 500 lines
7. Include proper cleanup and performance optimization
8. Must look good on dark AND light backgrounds
9. Use CSS mix-blend-mode: screen for glow effects
10. Include a title comment at the top with overlay name and description

STYLE GUIDE:
- Wireframe creatures: glowing outlines, no fills, particle trails
- Ambient effects: aurora, particles, waves, fractals
- Productivity tools: clean glass UI, semi-transparent, draggable
- Information displays: minimal, readable, non-intrusive

Return ONLY the complete HTML code. No explanations."""

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key=None, output_dir=None):
        self.api_key = api_key or GROQ_API_KEY
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "overlays", "generated"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def create_overlay(self, description, category="ambient", name=None):
        """
        Generate a new overlay from a text description.

        Args:
            description: What the overlay should look like/do
            category: ambient, productivity, wellness, creative, information
            name: Optional filename (auto-generated if not provided)

        Returns:
            dict with {id, name, path, html, category} or None on failure
        """
        if not HAS_REQUESTS or not self.api_key:
            return None

        prompt = (
            f"Create an HTML5 Canvas overlay animation:\n"
            f"Category: {category}\n"
            f"Description: {description}\n\n"
            f"Generate the complete HTML file."
        )

        try:
            resp = requests.post(
                self.GROQ_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": AGENT_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.8,
                },
                timeout=60,
            )

            if resp.status_code != 200:
                return None

            data = resp.json()
            html = data["choices"][0]["message"]["content"].strip()

            # Extract HTML from markdown code blocks if present
            if "```html" in html:
                html = html.split("```html", 1)[1].split("```", 1)[0].strip()
            elif "```" in html:
                html = html.split("```", 1)[1].split("```", 1)[0].strip()

            # Generate name if not provided
            if not name:
                safe_desc = description[:30].lower().replace(" ", "-")
                safe_desc = "".join(c for c in safe_desc if c.isalnum() or c == "-")
                name = f"{safe_desc}-{int(time.time()) % 100000}"

            overlay_id = name
            filename = f"{name}.html"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            return {
                "id": overlay_id,
                "name": name,
                "path": filepath,
                "html": html,
                "category": category,
                "description": description,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }

        except Exception:
            return None

    def create_daily_overlays(self, count=3):
        """
        Generate daily overlay drops.
        Called by n8n workflow every morning.
        """
        daily_themes = [
            ("Glowing wireframe dolphin jumping through waves", "ambient"),
            ("Floating holographic crystals rotating slowly", "ambient"),
            ("Neon rain drops with ripple effects", "ambient"),
            ("Wireframe butterfly garden with particles", "creative"),
            ("Glowing DNA helix strand spinning", "creative"),
            ("Constellation map with twinkling stars", "ambient"),
            ("Wireframe whale swimming through clouds", "ambient"),
            ("Neon circuit board patterns pulsing", "creative"),
            ("Floating paper lanterns with warm glow", "ambient"),
            ("Abstract geometric mandala rotating", "creative"),
            ("Wireframe phoenix with fire particles", "creative"),
            ("Ocean waves with bioluminescent plankton", "ambient"),
            ("Floating zen garden with raked sand", "wellness"),
            ("Holographic koi fish in a pond", "ambient"),
            ("Neon cherry blossom petals falling", "ambient"),
        ]

        import random
        selected = random.sample(daily_themes, min(count, len(daily_themes)))
        results = []

        for description, category in selected:
            result = self.create_overlay(description, category)
            if result:
                result["is_daily"] = True
                results.append(result)

        return results
