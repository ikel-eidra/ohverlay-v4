"""
Ohverlay Factory - The Central Brain
=====================================
ohverlay.com backend infrastructure that powers the entire ecosystem.

Architecture:
  factory/
    api/              - REST API server (FastAPI)
      server.py       - Main API endpoints
      overlay_store.py - Overlay catalog & delivery
      auth.py         - User authentication (simple API keys)
    agents/           - Resident AI agents
      overlay_creator.py  - AI that generates new overlays
      content_curator.py  - Curates daily content (news, quotes, tips)
    overlays/         - Overlay templates & daily drops
    docker-compose.yml - Full stack: API + n8n + PostgreSQL + Redis
    Dockerfile        - Factory API container
    factory_config.py - Central configuration

The Factory serves:
  ONLINE users  → real-time news, Blue AI, daily overlays, ads, updates
  OFFLINE users → basic bundled overlays, cached content, local Blue
  Desktop app   → update manifests, overlay catalog, telemetry
  n8n workflows → automation for content creation, notifications, deploys
"""
