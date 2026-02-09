"""
News/Info module using RSS feeds.
Fetches headlines from configured RSS feeds and delivers them via bubbles.
"""

import time
import threading
from utils.logger import logger

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    logger.warning("feedparser not installed. News module disabled.")


class NewsModule:
    """Fetches and delivers news headlines from RSS feeds."""

    DEFAULT_FEEDS = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ]

    def __init__(self, config=None):
        self.enabled = False  # Disabled by default per PRD (user opts in)
        self.feeds = list(self.DEFAULT_FEEDS)
        self.check_interval = 30 * 60  # seconds
        self.last_check = 0
        self.headlines = []
        self.delivered = set()
        self._fetching = False

        if config:
            self._load_config(config)

    def _load_config(self, config):
        ncfg = config.get("news") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(ncfg, dict):
            return
        feeds = ncfg.get("rss_feeds", [])
        if feeds:
            self.feeds = feeds
        self.check_interval = ncfg.get("check_interval_minutes", 30) * 60

    def check(self):
        """Check for new headlines. Returns list of (message, category) tuples."""
        if not self.enabled or not HAS_FEEDPARSER:
            return []

        now = time.time()
        if now - self.last_check < self.check_interval:
            return []

        self.last_check = now

        # Fetch in background to avoid blocking
        if not self._fetching:
            self._fetching = True
            thread = threading.Thread(target=self._fetch_feeds, daemon=True)
            thread.start()

        # Deliver one headline at a time
        messages = []
        for headline in self.headlines:
            if headline not in self.delivered:
                messages.append((headline, "news"))
                self.delivered.add(headline)
                break  # One at a time

        return messages

    def _fetch_feeds(self):
        """Fetch RSS feeds in background thread."""
        try:
            new_headlines = []
            for feed_url in self.feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:5]:
                        title = entry.get("title", "").strip()
                        if title:
                            new_headlines.append(title)
                except Exception as e:
                    logger.warning(f"Error fetching feed {feed_url}: {e}")

            self.headlines = new_headlines
            logger.debug(f"Fetched {len(new_headlines)} headlines from {len(self.feeds)} feeds")
        finally:
            self._fetching = False
