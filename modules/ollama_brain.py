"""
Ollama Brain - Local Offline LLM Provider for Ohverlay Personal VA Companion.
Connects to local Ollama server (http://localhost:11434) with zero cloud telemetry.
"""

import json
import urllib.request
import urllib.error
import threading
from utils.logger import logger

class OllamaBrain:
    def __init__(self, host="http://localhost:11434", default_model="llama3.2:1b"):
        self.host = host.rstrip('/')
        self.model = default_model
        self.available_models = []
        self.is_connected = False
        self._check_connection()

    def _check_connection(self):
        """Check if local Ollama server is running and fetch available models."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "Ohverlay-VA"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    models = data.get('models', [])
                    self.available_models = [m.get('name') for m in models if m.get('name')]
                    if self.available_models:
                        if self.model not in self.available_models:
                            self.model = self.available_models[0]
                        self.is_connected = True
                        logger.info(f"Ollama Brain connected! Active model: {self.model}")
                        return True
        except Exception as e:
            logger.debug(f"Ollama Brain connection check: {e}")
        self.is_connected = False
        return False

    def generate_response(self, prompt, system_prompt="You are Ohverlay Personal VA, a concise, helpful workstation AI assistant."):
        """Synchronous generation from local Ollama model."""
        if not self.is_connected and not self._check_connection():
            return "Ollama offline. Start Ollama (`ollama serve`) to enable local AI assistant."

        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "num_predict": 120
            }
        }

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "Ohverlay-VA"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    result = json.loads(resp.read().decode('utf-8'))
                    return result.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation error: {e}")
            return f"Ollama error: {e}"

        return "No response from Ollama."

    def generate_async(self, prompt, callback, system_prompt=None):
        """Asynchronous non-blocking generation."""
        def _worker():
            res = self.generate_response(prompt, system_prompt) if system_prompt else self.generate_response(prompt)
            if callback:
                callback(res)
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

# Global Ollama Brain instance
ollama_brain = OllamaBrain()
