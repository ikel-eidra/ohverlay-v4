-- ============================================================
-- OHVERLAY FACTORY - Database Schema
-- PostgreSQL initialization script
-- ============================================================

-- Users table (desktop app + web users)
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(64) UNIQUE NOT NULL,
    email           VARCHAR(255),
    display_name    VARCHAR(100),
    tier            VARCHAR(20) DEFAULT 'free',  -- free, pro, enterprise
    api_key         VARCHAR(128),
    app_version     VARCHAR(20),
    platform        VARCHAR(20),  -- windows, mac, linux, web
    timezone        VARCHAR(50) DEFAULT 'Asia/Manila',
    preferences     JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    last_seen       TIMESTAMP DEFAULT NOW()
);

-- Overlay catalog
CREATE TABLE IF NOT EXISTS overlays (
    id              SERIAL PRIMARY KEY,
    overlay_id      VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(50) NOT NULL,
    version         VARCHAR(20) DEFAULT '1.0.0',
    html_content    TEXT,
    thumbnail_url   VARCHAR(500),
    is_free         BOOLEAN DEFAULT TRUE,
    is_daily        BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    tags            TEXT[] DEFAULT '{}',
    download_count  INTEGER DEFAULT 0,
    rating          DECIMAL(3,2) DEFAULT 0,
    created_by      VARCHAR(50) DEFAULT 'system',  -- system, ai-agent, user
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Daily overlay drops
CREATE TABLE IF NOT EXISTS daily_drops (
    id              SERIAL PRIMARY KEY,
    drop_date       DATE NOT NULL,
    overlay_id      INTEGER REFERENCES overlays(id),
    position        INTEGER DEFAULT 0,  -- ordering
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_daily_drops_date ON daily_drops(drop_date);

-- Blue AI conversation logs (server-side for web users)
CREATE TABLE IF NOT EXISTS blue_conversations (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(64),
    role            VARCHAR(20) NOT NULL,  -- user, assistant, system
    content         TEXT NOT NULL,
    tokens_used     INTEGER DEFAULT 0,
    model           VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blue_conv_user ON blue_conversations(user_id);

-- Blue memory (user facts, preferences)
CREATE TABLE IF NOT EXISTS blue_memory (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(64) NOT NULL,
    category        VARCHAR(50) NOT NULL,  -- name, location, preference, etc.
    fact            TEXT NOT NULL,
    confidence      DECIMAL(3,2) DEFAULT 1.0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blue_memory_user ON blue_memory(user_id);

-- Content cache (news, weather, tickers)
CREATE TABLE IF NOT EXISTS content_cache (
    id              SERIAL PRIMARY KEY,
    cache_key       VARCHAR(200) UNIQUE NOT NULL,
    content         JSONB NOT NULL,
    ttl_seconds     INTEGER DEFAULT 900,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Analytics / telemetry (anonymous usage stats)
CREATE TABLE IF NOT EXISTS analytics (
    id              SERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,
    user_id         VARCHAR(64),
    data            JSONB DEFAULT '{}',
    app_version     VARCHAR(20),
    platform        VARCHAR(20),
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(created_at);

-- Update releases
CREATE TABLE IF NOT EXISTS releases (
    id              SERIAL PRIMARY KEY,
    version         VARCHAR(20) UNIQUE NOT NULL,
    channel         VARCHAR(20) DEFAULT 'stable',
    installer_url   VARCHAR(500),
    portable_url    VARCHAR(500),
    notes           TEXT,
    min_version     VARCHAR(20) DEFAULT '1.0.0',
    is_active       BOOLEAN DEFAULT TRUE,
    released_at     TIMESTAMP DEFAULT NOW()
);

-- Ohverlay promo overlays (company announcements only, minimal, hanapbuhay lang)
-- NO third-party ads. Only Ohverlay's own: new features, pro tier, tips.
CREATE TABLE IF NOT EXISTS promo_overlays (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    overlay_html    TEXT NOT NULL,
    promo_type      VARCHAR(50) DEFAULT 'feature',  -- feature, pro_upgrade, tip, changelog
    target_tier     VARCHAR(20) DEFAULT 'free',      -- which tier sees it
    impressions     INTEGER DEFAULT 0,
    dismissed       INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    max_impressions INTEGER DEFAULT 3,               -- show max 3x per user, then stop
    start_date      DATE,
    end_date        DATE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- n8n workflow logs
CREATE TABLE IF NOT EXISTS workflow_logs (
    id              SERIAL PRIMARY KEY,
    workflow_name   VARCHAR(200),
    event_type      VARCHAR(50),
    status          VARCHAR(20),  -- success, failed, skipped
    data            JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW()
);
