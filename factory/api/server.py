"""
Ohverlay Factory API Server
============================
FastAPI backend powering ohverlay.com

Endpoints:
  /api/v1/overlays          - Browse & download overlay catalog
  /api/v1/overlays/daily    - Today's featured overlays
  /api/v1/overlays/{id}     - Get specific overlay HTML/config
  /api/v1/updates/manifest  - Desktop app update manifest
  /api/v1/updates/download  - Download latest installer/portable ZIP
  /api/v1/blue/chat         - Blue AI chat (server-side, for web users)
  /api/v1/blue/vision       - Blue Vision analysis
  /api/v1/news              - Real-time news feed
  /api/v1/weather           - Weather data
  /api/v1/tickers           - Crypto/stock tickers
  /api/v1/health            - Factory health check
  /api/v1/n8n/webhook       - n8n automation webhook receiver
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import time
import os
import json

from factory.factory_config import (
    FACTORY_VERSION, FACTORY_URL, CURRENT_APP_VERSION,
    OVERLAY_CATEGORIES, DEBUG,
)

# ─── App Setup ───

app = FastAPI(
    title="Ohverlay Factory",
    description="The central brain powering ohverlay.com - overlays, AI, content delivery",
    version=FACTORY_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ohverlay.com", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ───

class OverlayInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str
    version: str
    thumbnail_url: Optional[str] = None
    download_url: str
    is_free: bool = True
    is_daily: bool = False
    created_at: str = ""
    tags: List[str] = []


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    context: Optional[str] = None
    include_vision: bool = False


class ChatResponse(BaseModel):
    reply: str
    memory_updated: bool = False
    suggestions: List[str] = []


class UpdateManifest(BaseModel):
    version: str
    channel: str
    installer_url: str
    portable_url: str
    notes: str
    min_version: str = "1.0.0"
    released_at: str = ""


# ─── Overlay Catalog (in-memory for now, PostgreSQL later) ───

_overlay_catalog: List[dict] = []
_daily_overlays: List[dict] = []


def _load_overlay_catalog():
    """Load overlays from the overlays directory."""
    global _overlay_catalog
    overlays_dir = os.path.join(os.path.dirname(__file__), "..", "overlays")
    catalog_file = os.path.join(overlays_dir, "catalog.json")

    if os.path.exists(catalog_file):
        with open(catalog_file, "r") as f:
            _overlay_catalog = json.load(f)
    else:
        # Default catalog with bundled overlays
        _overlay_catalog = [
            {
                "id": "betta-fish",
                "name": "Betta Fish Companion",
                "description": "Beautiful betta fish swimming on your desktop with realistic AI behavior",
                "category": "ambient",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/betta-fish",
                "is_free": True,
                "is_daily": False,
                "tags": ["fish", "pet", "ambient", "ai"],
            },
            {
                "id": "jellyfish-cyan",
                "name": "Cyan Jellyfish",
                "description": "Ethereal glowing jellyfish floating across your screen",
                "category": "ambient",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/jellyfish-cyan",
                "is_free": True,
                "is_daily": False,
                "tags": ["jellyfish", "glow", "ambient"],
            },
            {
                "id": "manta-ray",
                "name": "Wireframe Manta Ray",
                "description": "Graceful wireframe manta ray gliding with neon glow",
                "category": "ambient",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/manta-ray",
                "is_free": True,
                "is_daily": False,
                "tags": ["manta", "wireframe", "neon"],
            },
            {
                "id": "aurora",
                "name": "Aurora Borealis",
                "description": "Northern lights dancing across your desktop",
                "category": "ambient",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/aurora",
                "is_free": True,
                "is_daily": False,
                "tags": ["aurora", "lights", "ambient"],
            },
            {
                "id": "fairy-dandelion",
                "name": "Fairy & Dandelion",
                "description": "Wireframe fairy with floating dandelion seeds",
                "category": "creative",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/fairy-dandelion",
                "is_free": True,
                "is_daily": False,
                "tags": ["fairy", "wireframe", "magical"],
            },
            {
                "id": "sticky-note",
                "name": "Smart Sticky Note",
                "description": "Draggable sticky note with countdown timer and deadline tracking",
                "category": "productivity",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/sticky-note",
                "is_free": True,
                "is_daily": False,
                "tags": ["note", "timer", "productivity"],
            },
            {
                "id": "blue-chatbox",
                "name": "Blue AI Assistant",
                "description": "AI chatbox overlay powered by free LLMs with memory and vision",
                "category": "productivity",
                "version": "4.0.0",
                "download_url": f"{FACTORY_URL}/overlays/blue-chatbox",
                "is_free": True,
                "is_daily": False,
                "tags": ["ai", "chat", "blue", "assistant"],
            },
        ]


# Load on startup
_load_overlay_catalog()


# ─── Health ───

@app.get("/api/v1/health")
async def health():
    return {
        "status": "alive",
        "factory_version": FACTORY_VERSION,
        "app_version": CURRENT_APP_VERSION,
        "overlays_count": len(_overlay_catalog),
        "timestamp": int(time.time()),
    }


# ─── Overlay Catalog ───

@app.get("/api/v1/overlays", response_model=List[OverlayInfo])
async def list_overlays(
    category: Optional[str] = Query(None, description="Filter by category"),
    free_only: bool = Query(False, description="Only free overlays"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
):
    results = _overlay_catalog

    if category:
        results = [o for o in results if o.get("category") == category]
    if free_only:
        results = [o for o in results if o.get("is_free", True)]
    if tag:
        results = [o for o in results if tag in o.get("tags", [])]

    return results


@app.get("/api/v1/overlays/daily")
async def daily_overlays():
    """Get today's featured overlays (AI-curated daily drops)."""
    daily = [o for o in _overlay_catalog if o.get("is_daily")]
    if not daily:
        # Fallback: pick random from catalog
        import random
        daily = random.sample(_overlay_catalog, min(3, len(_overlay_catalog)))
    return {"date": time.strftime("%Y-%m-%d"), "overlays": daily}


@app.get("/api/v1/overlays/{overlay_id}")
async def get_overlay(overlay_id: str):
    """Get a specific overlay by ID."""
    for o in _overlay_catalog:
        if o.get("id") == overlay_id:
            return o
    raise HTTPException(status_code=404, detail="Overlay not found")


@app.get("/api/v1/overlays/categories")
async def list_categories():
    return {"categories": OVERLAY_CATEGORIES}


# ─── Update System ───

@app.get("/api/v1/updates/manifest", response_model=UpdateManifest)
@app.get("/updates/manifest.json")  # Legacy path for existing desktop apps
async def update_manifest():
    """Return the current update manifest for desktop app auto-updates."""
    return UpdateManifest(
        version=CURRENT_APP_VERSION,
        channel="stable",
        installer_url=f"{FACTORY_URL}/downloads/Ohverlay-v{CURRENT_APP_VERSION}-Setup.exe",
        portable_url=f"{FACTORY_URL}/downloads/Ohverlay-v{CURRENT_APP_VERSION}-Portable.zip",
        notes=f"Ohverlay v{CURRENT_APP_VERSION} - Blue AI, Vision, Daily Overlays",
        released_at=time.strftime("%Y-%m-%d"),
    )


# ─── Blue AI Chat (Server-side for web users) ───

@app.post("/api/v1/blue/chat", response_model=ChatResponse)
async def blue_chat(req: ChatRequest):
    """Blue AI chat endpoint for ohverlay.com web version."""
    # In production, this calls Groq/Cohere with memory context
    # For now, return a placeholder showing the architecture works
    return ChatResponse(
        reply=f"Hey! I'm Blue, your AI assistant. I heard: '{req.message[:100]}'. "
              f"I'm running on the Ohverlay Factory!",
        memory_updated=True,
        suggestions=["Tell me about yourself", "What's the weather?", "Show me today's overlays"],
    )


# ─── Real-time Data ───

@app.get("/api/v1/news")
async def news_feed(
    topic: str = Query("technology", description="News topic"),
    limit: int = Query(5, description="Number of articles"),
):
    """Real-time news feed powered by factory content curator agent."""
    # Proxied through factory to add caching, curation, and filtering
    return {
        "topic": topic,
        "articles": [],
        "cached": False,
        "message": "Connect content curator agent for live news",
    }


@app.get("/api/v1/weather")
async def weather(city: str = Query("Manila", description="City name")):
    """Weather data proxied through factory for caching."""
    return {
        "city": city,
        "data": None,
        "message": "Connect weather module for live data",
    }


@app.get("/api/v1/tickers")
async def tickers(
    coins: str = Query("bitcoin,ethereum", description="Comma-separated coin IDs"),
):
    """Crypto ticker data proxied through factory."""
    return {
        "coins": coins.split(","),
        "prices": {},
        "message": "Connect ticker module for live prices",
    }


# ─── n8n Webhook Receiver ───

@app.post("/api/v1/n8n/webhook")
async def n8n_webhook(request: Request):
    """
    Receives webhooks from n8n automation workflows.
    n8n can trigger: overlay deployments, content updates, notifications.
    """
    body = await request.json()
    event_type = body.get("event", "unknown")

    if event_type == "deploy_overlay":
        # n8n triggers overlay deployment
        return {"status": "queued", "event": event_type}
    elif event_type == "content_update":
        # n8n pushes new content (news, quotes)
        return {"status": "received", "event": event_type}
    elif event_type == "notification":
        # n8n sends notification to users
        return {"status": "dispatched", "event": event_type}

    return {"status": "unknown_event", "event": event_type}


# ─── Startup ───

@app.on_event("startup")
async def startup():
    print(f"Ohverlay Factory v{FACTORY_VERSION} starting...")
    print(f"Serving {len(_overlay_catalog)} overlays")
    print(f"App version: {CURRENT_APP_VERSION}")
    print(f"Factory URL: {FACTORY_URL}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8400)
