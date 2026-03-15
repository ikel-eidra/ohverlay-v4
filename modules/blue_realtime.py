"""
Blue Real-Time Information Module - Ohverlay v4.0
Provides live news, weather, and trading ticker data for Blue AI assistant.

Uses free APIs that don't require authentication where possible,
and Groq/Cohere LLM for intelligent summarization.
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class BlueRealtime:
    """Real-time information provider for Blue AI assistant."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = {
            'news': 900,       # 15 minutes
            'weather': 1800,   # 30 minutes
            'ticker': 60,      # 1 minute
        }
        self.user_prefs = {
            'news_topics': ['technology', 'world'],
            'weather_location': None,
            'tickers': [],
            'news_language': 'en',
        }
        self._load_prefs()

    def _load_prefs(self):
        """Load user preferences from disk."""
        prefs_path = Path.home() / '.ohverlay' / 'blue_prefs.json'
        try:
            if prefs_path.exists():
                with open(prefs_path) as f:
                    saved = json.load(f)
                    self.user_prefs.update(saved)
        except Exception:
            pass

    def save_prefs(self):
        """Save user preferences to disk."""
        prefs_path = Path.home() / '.ohverlay' / 'blue_prefs.json'
        try:
            prefs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(prefs_path, 'w') as f:
                json.dump(self.user_prefs, f, indent=2)
        except Exception:
            pass

    def _is_cached(self, key):
        """Check if cached data is still fresh."""
        if key not in self.cache:
            return False
        entry = self.cache[key]
        ttl = self.cache_ttl.get(key.split(':')[0], 300)
        return (time.time() - entry['timestamp']) < ttl

    def _get_cached(self, key):
        """Get cached data."""
        return self.cache.get(key, {}).get('data')

    def _set_cached(self, key, data):
        """Set cached data."""
        self.cache[key] = {'data': data, 'timestamp': time.time()}

    # ─── News ───

    def get_news(self, topic=None, limit=5):
        """Get latest news headlines using free RSS-to-JSON API."""
        if not requests:
            return [{'title': 'News unavailable (requests not installed)', 'source': ''}]

        topic = topic or (self.user_prefs['news_topics'][0] if self.user_prefs['news_topics'] else 'world')
        cache_key = f'news:{topic}'

        if self._is_cached(cache_key):
            return self._get_cached(cache_key)[:limit]

        # Free news sources (no API key needed)
        feeds = {
            'world': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'technology': 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
            'business': 'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
            'science': 'https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
            'health': 'https://rss.nytimes.com/services/xml/rss/nyt/Health.xml',
            'sports': 'https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml',
            'philippines': 'https://www.philstar.com/rss/nation',
        }

        # Use rss2json.com free API to convert RSS to JSON
        feed_url = feeds.get(topic, feeds['world'])
        api_url = f'https://api.rss2json.com/v1/api.json?rss_url={feed_url}&count={limit}'

        try:
            resp = requests.get(api_url, timeout=10)
            data = resp.json()

            if data.get('status') == 'ok':
                articles = []
                for item in data.get('items', [])[:limit]:
                    articles.append({
                        'title': item.get('title', ''),
                        'source': item.get('author', '') or data.get('feed', {}).get('title', ''),
                        'link': item.get('link', ''),
                        'published': item.get('pubDate', ''),
                        'description': item.get('description', '')[:200],
                    })
                self._set_cached(cache_key, articles)
                return articles
        except Exception as e:
            return [{'title': f'News fetch error: {str(e)[:60]}', 'source': ''}]

        return [{'title': 'No news available', 'source': ''}]

    # ─── Weather ───

    def get_weather(self, location=None):
        """Get current weather using free wttr.in API (no key needed)."""
        if not requests:
            return {'error': 'requests not installed'}

        location = location or self.user_prefs.get('weather_location') or 'Manila'
        cache_key = f'weather:{location}'

        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        try:
            resp = requests.get(
                f'https://wttr.in/{location}?format=j1',
                timeout=10,
                headers={'User-Agent': 'Ohverlay/4.0'}
            )
            data = resp.json()

            current = data.get('current_condition', [{}])[0]
            weather = {
                'location': location,
                'temp_c': current.get('temp_C', '?'),
                'temp_f': current.get('temp_F', '?'),
                'feels_like_c': current.get('FeelsLikeC', '?'),
                'condition': current.get('weatherDesc', [{}])[0].get('value', 'Unknown'),
                'humidity': current.get('humidity', '?'),
                'wind_kmph': current.get('windspeedKmph', '?'),
                'wind_dir': current.get('winddir16Point', ''),
                'uv_index': current.get('uvIndex', '?'),
                'visibility': current.get('visibility', '?'),
            }

            # Forecast
            forecasts = data.get('weather', [])
            weather['forecast'] = []
            for day in forecasts[:3]:
                weather['forecast'].append({
                    'date': day.get('date', ''),
                    'max_c': day.get('maxtempC', '?'),
                    'min_c': day.get('mintempC', '?'),
                    'condition': day.get('hourly', [{}])[4].get('weatherDesc', [{}])[0].get('value', '') if day.get('hourly') else '',
                })

            self._set_cached(cache_key, weather)
            return weather

        except Exception as e:
            return {'error': str(e)[:100], 'location': location}

    # ─── Trading Tickers ───

    def get_ticker(self, symbol='BTC'):
        """Get crypto/stock price using free CoinGecko API (no key for crypto)."""
        if not requests:
            return {'error': 'requests not installed'}

        cache_key = f'ticker:{symbol}'

        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        # Map common symbols to CoinGecko IDs
        crypto_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'ADA': 'cardano', 'DOT': 'polkadot', 'DOGE': 'dogecoin',
            'XRP': 'ripple', 'AVAX': 'avalanche-2', 'MATIC': 'matic-network',
            'LINK': 'chainlink', 'UNI': 'uniswap', 'ATOM': 'cosmos',
            'BNB': 'binancecoin', 'SHIB': 'shiba-inu',
        }

        coin_id = crypto_map.get(symbol.upper())
        if coin_id:
            try:
                resp = requests.get(
                    f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,php&include_24hr_change=true&include_24hr_vol=true',
                    timeout=10
                )
                data = resp.json().get(coin_id, {})

                ticker = {
                    'symbol': symbol.upper(),
                    'type': 'crypto',
                    'price_usd': data.get('usd', 0),
                    'price_php': data.get('php', 0),
                    'change_24h': round(data.get('usd_24h_change', 0), 2),
                    'volume_24h': data.get('usd_24h_vol', 0),
                }
                self._set_cached(cache_key, ticker)
                return ticker

            except Exception as e:
                return {'symbol': symbol, 'error': str(e)[:60]}

        return {'symbol': symbol, 'error': 'Symbol not found. Supported: ' + ', '.join(crypto_map.keys())}

    def get_multiple_tickers(self, symbols=None):
        """Get prices for multiple symbols."""
        symbols = symbols or self.user_prefs.get('tickers', ['BTC', 'ETH'])
        results = []
        for sym in symbols[:10]:  # Limit to 10
            results.append(self.get_ticker(sym))
        return results

    # ─── Preferences ───

    def set_news_topics(self, topics):
        """Set preferred news topics."""
        valid = ['world', 'technology', 'business', 'science', 'health', 'sports', 'philippines']
        self.user_prefs['news_topics'] = [t for t in topics if t in valid]
        self.save_prefs()

    def set_weather_location(self, location):
        """Set weather location."""
        self.user_prefs['weather_location'] = location
        self.save_prefs()

    def set_tickers(self, symbols):
        """Set tracked trading symbols."""
        self.user_prefs['tickers'] = [s.upper() for s in symbols[:10]]
        self.save_prefs()

    # ─── Context for Blue ───

    def build_realtime_context(self):
        """Build a real-time context string for Blue's system prompt."""
        parts = []
        now = datetime.now()
        parts.append(f'Current date/time: {now.strftime("%A, %B %d, %Y %I:%M %p")}')

        # Weather (if location is set)
        if self.user_prefs.get('weather_location'):
            weather = self.get_weather()
            if 'error' not in weather:
                parts.append(f'Weather in {weather["location"]}: {weather["temp_c"]}°C, {weather["condition"]}, Humidity: {weather["humidity"]}%')

        # Tickers (if any tracked)
        if self.user_prefs.get('tickers'):
            tickers = self.get_multiple_tickers()
            ticker_strs = []
            for t in tickers:
                if 'error' not in t:
                    direction = '+' if t.get('change_24h', 0) >= 0 else ''
                    ticker_strs.append(f'{t["symbol"]}: ${t["price_usd"]:,.2f} ({direction}{t["change_24h"]}%)')
            if ticker_strs:
                parts.append('Tickers: ' + ' | '.join(ticker_strs))

        return '\n'.join(parts)

    def format_news_summary(self, topic=None, limit=3):
        """Format news as a readable summary for display."""
        articles = self.get_news(topic, limit)
        lines = []
        for i, a in enumerate(articles, 1):
            lines.append(f'{i}. {a["title"]}')
            if a.get('source'):
                lines.append(f'   — {a["source"]}')
        return '\n'.join(lines) if lines else 'No news available.'

    def format_weather_summary(self, location=None):
        """Format weather as a readable summary."""
        w = self.get_weather(location)
        if 'error' in w:
            return f'Weather error: {w["error"]}'

        lines = [
            f'Weather in {w["location"]}:',
            f'  {w["condition"]}, {w["temp_c"]}°C (feels like {w["feels_like_c"]}°C)',
            f'  Humidity: {w["humidity"]}% | Wind: {w["wind_kmph"]} km/h {w["wind_dir"]}',
            f'  UV Index: {w["uv_index"]} | Visibility: {w["visibility"]} km',
        ]
        if w.get('forecast'):
            lines.append('  Forecast:')
            for f in w['forecast']:
                lines.append(f'    {f["date"]}: {f["min_c"]}–{f["max_c"]}°C, {f["condition"]}')
        return '\n'.join(lines)

    def format_ticker_summary(self, symbols=None):
        """Format tickers as a readable summary."""
        tickers = self.get_multiple_tickers(symbols)
        lines = []
        for t in tickers:
            if 'error' in t:
                lines.append(f'{t["symbol"]}: {t["error"]}')
            else:
                direction = '+' if t.get('change_24h', 0) >= 0 else ''
                lines.append(f'{t["symbol"]}: ${t["price_usd"]:,.2f} (₱{t["price_php"]:,.2f}) {direction}{t["change_24h"]}% 24h')
        return '\n'.join(lines) if lines else 'No tickers configured.'
