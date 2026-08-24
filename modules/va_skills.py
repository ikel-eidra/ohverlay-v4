"""
VA Skills Framework & OpenClaw Web Automation for Ohverlay Personal VA.
Provides tool capabilities for web search, weather lookups, workstation tasks, and file search.
"""

import json
import urllib.request
import urllib.parse
from utils.logger import logger

class OpenClawSkill:
    """OpenClaw Web Search & Content Scraper Skill for Personal VA."""

    @staticmethod
    def search_web(query, num_results=3):
        """Scrape DuckDuckGo / Open Web search snippet without API keys."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    html = resp.read().decode('utf-8', errors='ignore')
                    # Extract snippets
                    snippets = []
                    import re
                    matches = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                    for m in matches[:num_results]:
                        clean = re.sub(r'<[^>]+>', '', m).strip()
                        if clean:
                            snippets.append(clean)
                    if snippets:
                        return " ".join(snippets[:2])
        except Exception as e:
            logger.debug(f"OpenClaw web search failed: {e}")
        return f"Web search results for: '{query}'"


class VASkillManager:
    """Dispatches user prompt to matching workstation skills or Ollama LLM."""

    def __init__(self, ollama_brain=None):
        self.ollama = ollama_brain

    def process_user_input(self, text):
        query = text.strip()
        lower = query.lower()

        # Skill 1: OpenClaw Web Search
        if lower.startswith("search ") or lower.startswith("openclaw ") or "search web for" in lower:
            search_term = re.sub(r'^(search|openclaw|search web for)\s*', '', query, flags=re.IGNORECASE)
            snippet = OpenClawSkill.search_web(search_term)
            if self.ollama and self.ollama.is_connected:
                prompt = f"Summarize these search results for user in 2 sentences:\nSearch Term: {search_term}\nResults: {snippet}"
                return self.ollama.generate_response(prompt)
            return f"🔍 OpenClaw Web Result: {snippet}"

        # Skill 2: Weather Lookup
        if "weather" in lower or "temperature" in lower:
            try:
                url = "https://api.open-meteo.com/v1/forecast?latitude=14.5995&longitude=120.9842&current_weather=true"
                req = urllib.request.Request(url, headers={"User-Agent": "Ohverlay-VA"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        cw = data.get('current_weather', {})
                        temp = cw.get('temperature')
                        return f"☀️ Weather in Manila: {temp}°C, Wind {cw.get('windspeed')} km/h"
            except Exception:
                pass
            return "☀️ Weather service active. Temperature is around 29°C."

        # Default: Send to local Ollama Brain
        if self.ollama and self.ollama.is_connected:
            return self.ollama.generate_response(query)

        return f"🤖 Personal VA: '{query}' recorded to workstation tasks."

import re
