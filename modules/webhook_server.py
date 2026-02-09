"""
Local webhook server for receiving messages from WhatsApp, Messenger, or any
automation service (IFTTT, Zapier, Make, n8n, custom scripts).

Runs a tiny HTTP server on localhost that accepts POST /message with JSON body.
This lets you connect any messaging platform through automation:

WhatsApp -> IFTTT/Zapier/n8n -> POST http://localhost:7277/message
Messenger -> IFTTT/Zapier/n8n -> POST http://localhost:7277/message

JSON body format:
    {"text": "I love you", "sender": "Mahal", "source": "whatsapp"}
"""

import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque
from utils.logger import logger


class _WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the webhook endpoint."""

    server_instance = None  # Set by WebhookServer

    def do_POST(self):
        if self.path == "/message":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                text = data.get("text", "").strip()
                sender = data.get("sender", "Someone")
                source = data.get("source", "webhook")

                if text and self.server_instance:
                    self.server_instance._messages.append({
                        "text": text,
                        "sender": sender,
                        "source": source,
                    })
                    logger.info(f"Webhook message from {sender} ({source}): {text[:30]}...")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True}).encode())
                else:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Missing text field"}).encode())

            except (json.JSONDecodeError, ValueError) as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "zenfish"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "zenfish"}).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ZenFish Webhook Server. POST /message with {\"text\": \"...\", \"sender\": \"...\"}")

    def log_message(self, format, *args):
        """Suppress default HTTP logging - we use our own logger."""
        pass


class WebhookServer:
    """
    Local webhook server for receiving messages from messaging automations.

    Usage from external automation:
        curl -X POST http://localhost:7277/message \\
             -H "Content-Type: application/json" \\
             -d '{"text": "I love you", "sender": "Mahal", "source": "whatsapp"}'
    """

    def __init__(self, config=None):
        self.enabled = False
        self.port = 7277
        self._messages = deque(maxlen=100)
        self._server = None
        self._thread = None

        if config:
            self._load_config(config)

    def _load_config(self, config):
        wcfg = config.get("webhook") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(wcfg, dict):
            return
        self.enabled = wcfg.get("enabled", False)
        self.port = wcfg.get("port", 7277)

    def start(self):
        """Start the webhook HTTP server in a background thread."""
        if not self.enabled:
            return False

        try:
            _WebhookHandler.server_instance = self
            self._server = HTTPServer(("127.0.0.1", self.port), _WebhookHandler)
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            logger.info(f"Webhook server started on http://127.0.0.1:{self.port}")
            logger.info(f"  POST /message with {{\"text\": \"...\", \"sender\": \"...\", \"source\": \"whatsapp|messenger\"}}")
            return True
        except OSError as e:
            logger.warning(f"Webhook server failed to start on port {self.port}: {e}")
            return False

    def stop(self):
        """Stop the webhook server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("Webhook server stopped.")

    def check(self):
        """
        Return new messages as list of (message, category) tuples.
        Called by the brain's module polling.
        """
        if not self.enabled:
            return []

        messages = []
        while self._messages:
            try:
                msg_data = self._messages.popleft()
                text = msg_data.get("text", "")
                sender = msg_data.get("sender", "Someone")
                source = msg_data.get("source", "webhook")
                if text:
                    display = f"{text}"
                    messages.append((display, "love"))
            except IndexError:
                break
        return messages
