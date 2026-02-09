"""
News/Info module - LLM-enhanced.
Fetches RSS headlines and uses the LLM Brain to curate and summarize
the most relevant news into concise fish-bubble messages.
Falls back to raw headlines when LLM is unavailable.
"""

import time
import threading
from utils.logger import logger

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    logger.warning("feedparser not installed. News module RSS disabled.")

try:
    import requests as req_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class NewsModule:
    """Fetches, curates, and delivers news through the LLM Brain."""

    DEFAULT_FEEDS = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ]

    def __init__(self, config=None, llm_brain=None):
        self.enabled = False  # Opt-in per PRD
        self.llm_brain = llm_brain
        self.feeds = list(self.DEFAULT_FEEDS)
        self.check_interval = 30 * 60  # seconds
        self.last_check = 0
        self.raw_headlines = []
        self.delivered = set()
        self._fetching = False

        if config:
            self._load_config(config)

    def set_llm_brain(self, llm_brain):
        """Attach LLM brain for intelligent news curation."""
        self.llm_brain = llm_brain

    def _load_config(self, config):
        ncfg = config.get("news") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(ncfg, dict):
            return
        feeds = ncfg.get("rss_feeds", [])
        if feeds:
            self.feeds = feeds
        self.check_interval = ncfg.get("check_interval_minutes", 30) * 60

    def check(self):
        """Check for news. Returns list of (message, category) tuples."""
        if not self.enabled:
            return []

        now = time.time()
        if now - self.last_check < self.check_interval:
            return []

        self.last_check = now

        # Fetch feeds in background
        if not self._fetching and (HAS_FEEDPARSER or HAS_REQUESTS):
            self._fetching = True
            thread = threading.Thread(target=self._fetch_feeds, daemon=True)
            thread.start()

        if not self.raw_headlines:
            return []

        # Get undelivered headlines
        undelivered = [h for h in self.raw_headlines if h not in self.delivered]
        if not undelivered:
            return []

        # Try LLM curation: pick the best headline and summarize it
        if self.llm_brain and self.llm_brain.is_available:
            try:
                curated = self.llm_brain.curate_news(undelivered[:10])
                if curated:
                    # Mark all input headlines as "considered"
                    for h in undelivered[:10]:
                        self.delivered.add(h)
                    return [(curated, "news")]
            except Exception as e:
                logger.debug(f"LLM news curation failed: {e}")

        # Fallback: deliver one raw headline at a time
        headline = undelivered[0]
        self.delivered.add(headline)

        # Truncate for bubble display
        if len(headline) > 75:
            headline = headline[:72] + "..."

        return [(headline, "news")]

    def _fetch_feeds(self):
        """Fetch RSS feeds in background thread."""
        try:
            new_headlines = []

            if HAS_FEEDPARSER:
                for feed_url in self.feeds:
                    try:
                        feed = feedparser.parse(feed_url)
                        for entry in feed.entries[:8]:
                            title = entry.get("title", "").strip()
                            if title:
                                new_headlines.append(title)
                    except Exception as e:
                        logger.warning(f"Error fetching feed {feed_url}: {e}")

            self.raw_headlines = new_headlines
            logger.debug(f"Fetched {len(new_headlines)} headlines from {len(self.feeds)} feeds")
        finally:
            self._fetching = False
