"""
Ohverlay Factory - Central Configuration
All factory settings, API keys, and infrastructure config.
"""

import os

# ─── Core ───
FACTORY_VERSION = "1.0.0"
FACTORY_HOST = os.environ.get("FACTORY_HOST", "0.0.0.0")
FACTORY_PORT = int(os.environ.get("FACTORY_PORT", "8400"))
FACTORY_URL = os.environ.get("FACTORY_URL", "https://ohverlay.com")
DEBUG = os.environ.get("FACTORY_DEBUG", "false").lower() == "true"

# ─── Database ───
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ohverlay:ohverlay@localhost:5432/ohverlay_factory"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# ─── AI Agents ───
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")

# AI agent models (all free tier)
AGENT_LLM_MODEL = "llama-3.3-70b-versatile"          # Groq free
AGENT_VISION_MODEL = "llama-3.2-11b-vision-preview"   # Groq free
AGENT_CREATIVE_MODEL = "command-r"                     # Cohere free

# ─── n8n Automation ───
N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
N8N_WEBHOOK_KEY = os.environ.get("N8N_WEBHOOK_KEY", "")

# ─── Overlay Delivery ───
OVERLAYS_DIR = os.environ.get("OVERLAYS_DIR", "/data/overlays")
MAX_DAILY_OVERLAYS = 3           # New overlays pushed per day
OVERLAY_CATEGORIES = [
    "ambient",       # Fish, jellyfish, aurora, particles
    "productivity",  # Sticky notes, timers, focus tools
    "information",   # News tickers, weather, crypto
    "wellness",      # Break reminders, eye care, breathing
    "creative",      # Art, animations, visualizations
    "ads",           # Sponsored overlays (non-intrusive)
]

# ─── Update System ───
INSTALLER_BUCKET = os.environ.get("INSTALLER_BUCKET", "/data/releases")
CURRENT_APP_VERSION = "4.0.0"

# ─── Rate Limits ───
API_RATE_LIMIT = "60/minute"
FREE_TIER_DAILY_CALLS = 1000
PRO_TIER_DAILY_CALLS = 50000
