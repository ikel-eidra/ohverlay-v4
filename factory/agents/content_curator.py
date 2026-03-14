"""
Content Curator Agent - Ohverlay Factory
==========================================
Resident AI agent that curates daily content for overlays.

Responsibilities:
- Fetch and filter news from multiple sources
- Generate daily wellness tips and quotes
- Curate trending topics for the news ticker overlay
- Create personalized content based on user preferences
- Feed content to n8n for automated distribution

Uses free APIs:
- rss2json.com (news RSS feeds)
- wttr.in (weather)
- CoinGecko (crypto prices)
- Groq Llama (content summarization)
"""

import os
import time
import json
from typing import List, Optional

from factory.factory_config import GROQ_API_KEY, AGENT_LLM_MODEL

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class ContentCuratorAgent:
    """AI agent that curates and creates content for overlays."""

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Free RSS feeds via rss2json
    NEWS_SOURCES = {
        "technology": "https://feeds.feedburner.com/TechCrunch/",
        "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "science": "https://www.sciencedaily.com/rss/all.xml",
        "philippines": "https://www.philstar.com/rss/nation",
        "gaming": "https://kotaku.com/rss",
        "crypto": "https://cointelegraph.com/rss",
    }

    WELLNESS_CATEGORIES = [
        "hydration", "eye_care", "posture", "stretching",
        "breathing", "mindfulness", "gratitude",
    ]

    def __init__(self, api_key=None, cache_dir=None):
        self.api_key = api_key or GROQ_API_KEY
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "..", "overlays", "content_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self._news_cache = {}
        self._cache_ttl = 900  # 15 minutes

    def fetch_news(self, topic="technology", limit=5):
        """Fetch news articles from RSS feeds."""
        if not HAS_REQUESTS:
            return []

        # Check cache
        cache_key = f"news_{topic}"
        if cache_key in self._news_cache:
            cached = self._news_cache[cache_key]
            if time.time() - cached["time"] < self._cache_ttl:
                return cached["data"][:limit]

        feed_url = self.NEWS_SOURCES.get(topic)
        if not feed_url:
            return []

        try:
            rss_api = f"https://api.rss2json.com/v1/api.json?rss_url={feed_url}"
            resp = requests.get(rss_api, timeout=10)
            if resp.status_code != 200:
                return []

            data = resp.json()
            articles = []
            for item in data.get("items", [])[:limit]:
                articles.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "published": item.get("pubDate", ""),
                    "source": data.get("feed", {}).get("title", topic),
                })

            self._news_cache[cache_key] = {"time": time.time(), "data": articles}
            return articles

        except Exception:
            return []

    def fetch_weather(self, city="Manila"):
        """Fetch weather from wttr.in (free, no API key)."""
        if not HAS_REQUESTS:
            return None

        try:
            resp = requests.get(
                f"https://wttr.in/{city}?format=j1",
                headers={"User-Agent": "OhverlayFactory/1.0"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            return {
                "city": city,
                "temp_c": current.get("temp_C", "?"),
                "feels_like_c": current.get("FeelsLikeC", "?"),
                "humidity": current.get("humidity", "?"),
                "description": current.get("weatherDesc", [{}])[0].get("value", ""),
                "wind_kmh": current.get("windspeedKmph", "?"),
            }
        except Exception:
            return None

    def fetch_crypto_prices(self, coins=None):
        """Fetch crypto prices from CoinGecko (free, no API key)."""
        if not HAS_REQUESTS:
            return {}

        if coins is None:
            coins = ["bitcoin", "ethereum", "solana"]

        try:
            ids = ",".join(coins)
            resp = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price"
                f"?ids={ids}&vs_currencies=usd,php&include_24hr_change=true",
                timeout=10,
            )
            if resp.status_code != 200:
                return {}

            return resp.json()
        except Exception:
            return {}

    def generate_wellness_tip(self, category="hydration"):
        """Generate a wellness tip using AI."""
        if not HAS_REQUESTS or not self.api_key:
            # Fallback static tips
            return self._static_tip(category)

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
                        {
                            "role": "system",
                            "content": (
                                "You are a wellness advisor for desktop workers. "
                                "Generate a single, warm, encouraging wellness tip. "
                                "Keep it under 80 characters. No quotes or prefixes."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Generate a {category} tip for someone at their desk.",
                        },
                    ],
                    "max_tokens": 60,
                    "temperature": 0.9,
                },
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()[:80]
        except Exception:
            pass

        return self._static_tip(category)

    def _static_tip(self, category):
        """Fallback wellness tips when API is unavailable."""
        tips = {
            "hydration": "Your body needs water - take a sip right now!",
            "eye_care": "Look at something 20 feet away for 20 seconds.",
            "posture": "Shoulders back, chin level. You've got this!",
            "stretching": "Roll your shoulders and stretch your neck gently.",
            "breathing": "Take 3 deep breaths. In through nose, out through mouth.",
            "mindfulness": "Pause. Notice 3 things you can see right now.",
            "gratitude": "Think of one thing you're grateful for today.",
        }
        return tips.get(category, "Take care of yourself today.")

    def curate_daily_content(self):
        """
        Generate the daily content package for all overlays.
        Called by n8n workflow every morning.

        Returns a content package dict ready for distribution.
        """
        package = {
            "date": time.strftime("%Y-%m-%d"),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "news": {},
            "weather": self.fetch_weather("Manila"),
            "crypto": self.fetch_crypto_prices(),
            "wellness_tips": [],
            "quote_of_day": "",
        }

        # Fetch news from multiple topics
        for topic in ["technology", "world", "philippines"]:
            articles = self.fetch_news(topic, limit=3)
            if articles:
                package["news"][topic] = articles

        # Generate wellness tips for the day
        import random
        categories = random.sample(self.WELLNESS_CATEGORIES, 3)
        for cat in categories:
            tip = self.generate_wellness_tip(cat)
            package["wellness_tips"].append({"category": cat, "tip": tip})

        # Save to cache
        cache_path = os.path.join(self.cache_dir, f"daily_{package['date']}.json")
        with open(cache_path, "w") as f:
            json.dump(package, f, indent=2)

        return package
