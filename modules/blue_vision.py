"""
Blue Vision Module - Ohverlay v4.0
Gives Blue the ability to see the user's screen using free Groq Llama Vision.

Supports:
- Screenshot capture (full screen or active window)
- Image analysis via Groq Llama 3.2 Vision (free)
- Webcam capture (optional, if available)
- Clipboard image reading
"""

import base64
import io
import json
import os
import time
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

# Try to import screenshot tools
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    HAS_QT = True
except ImportError:
    HAS_QT = False

try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class BlueVision:
    """Vision capabilities for Blue AI assistant using free Groq Llama Vision."""

    # Groq vision model (free tier)
    VISION_MODEL = 'llama-3.2-11b-vision-preview'
    VISION_URL = 'https://api.groq.com/openai/v1/chat/completions'

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GROQ_API_KEY', '')
        self.last_analysis = None
        self.last_screenshot_time = 0
        self.cooldown = 5  # seconds between screenshots

    def set_api_key(self, key):
        """Update the API key."""
        self.api_key = key

    # ─── Screenshot Capture ───

    def capture_screenshot(self, max_size=1024):
        """Capture the screen and return as base64 JPEG.
        Tries PySide6 first, falls back to PIL.
        Returns (base64_string, width, height) or (None, 0, 0) on failure.
        """
        now = time.time()
        if now - self.last_screenshot_time < self.cooldown:
            return None, 0, 0

        self.last_screenshot_time = now

        # Method 1: PIL (most reliable cross-platform)
        if HAS_PIL:
            try:
                img = ImageGrab.grab()
                # Resize to save tokens and bandwidth
                w, h = img.size
                if max(w, h) > max_size:
                    ratio = max_size / max(w, h)
                    img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                    w, h = img.size

                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=75)
                b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return b64, w, h
            except Exception:
                pass

        # Method 2: PySide6
        if HAS_QT:
            try:
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                    if screen:
                        pixmap = screen.grabWindow(0)
                        # Scale down
                        w, h = pixmap.width(), pixmap.height()
                        if max(w, h) > max_size:
                            pixmap = pixmap.scaled(max_size, max_size, aspectMode=1)  # KeepAspectRatio
                            w, h = pixmap.width(), pixmap.height()

                        ba = QByteArray()
                        buf = QBuffer(ba)
                        buf.open(QIODevice.WriteOnly)
                        pixmap.save(buf, 'JPEG', 75)
                        b64 = base64.b64encode(ba.data()).decode('utf-8')
                        return b64, w, h
            except Exception:
                pass

        return None, 0, 0

    def capture_from_file(self, file_path, max_size=1024):
        """Read an image file and return as base64 JPEG."""
        if not HAS_PIL:
            return None, 0, 0

        try:
            img = Image.open(file_path)
            w, h = img.size
            if max(w, h) > max_size:
                ratio = max_size / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                w, h = img.size

            if img.mode == 'RGBA':
                img = img.convert('RGB')

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=75)
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return b64, w, h
        except Exception:
            return None, 0, 0

    def capture_from_clipboard(self, max_size=1024):
        """Read an image from the clipboard."""
        if not HAS_PIL:
            return None, 0, 0

        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                return None, 0, 0

            w, h = img.size
            if max(w, h) > max_size:
                ratio = max_size / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                w, h = img.size

            if img.mode == 'RGBA':
                img = img.convert('RGB')

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=75)
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return b64, w, h
        except Exception:
            return None, 0, 0

    # ─── Vision Analysis ───

    def analyze_image(self, image_b64, prompt=None, context=''):
        """Send image to Groq Llama Vision for analysis.

        Args:
            image_b64: Base64-encoded JPEG image
            prompt: What to ask about the image (default: describe what you see)
            context: Additional context for Blue

        Returns:
            str: The analysis text, or error message
        """
        if not requests:
            return 'Error: requests library not installed'

        if not self.api_key:
            return 'Error: No Groq API key configured. Set it in .env or settings.'

        if not image_b64:
            return 'Error: No image to analyze'

        if prompt is None:
            prompt = (
                'Describe what you see on this screen. Be concise and helpful. '
                'If you see any text, mention key content. '
                'If you see code, briefly describe what it does. '
                'If you see a chat or message, summarize it.'
            )

        system_msg = (
            'You are Blue, a friendly AI desktop assistant with vision. '
            'You can see the user\'s screen. Be concise (2-3 sentences). '
            'Be helpful and observant. If you notice something the user might need help with, mention it. '
            + (f'\nContext: {context}' if context else '')
        )

        messages = [
            {'role': 'system', 'content': system_msg},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{image_b64}'
                        }
                    }
                ]
            }
        ]

        try:
            resp = requests.post(
                self.VISION_URL,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                },
                json={
                    'model': self.VISION_MODEL,
                    'messages': messages,
                    'max_tokens': 300,
                    'temperature': 0.5,
                },
                timeout=30,
            )

            if resp.status_code != 200:
                error_text = resp.text[:150]
                return f'Vision API error ({resp.status_code}): {error_text}'

            data = resp.json()
            result = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            self.last_analysis = {
                'text': result,
                'timestamp': time.time(),
                'prompt': prompt,
            }

            return result

        except requests.Timeout:
            return 'Vision request timed out. Try again.'
        except Exception as e:
            return f'Vision error: {str(e)[:100]}'

    # ─── Convenience Methods ───

    def look_at_screen(self, question=None):
        """Take a screenshot and analyze it. The main method users will call."""
        b64, w, h = self.capture_screenshot()
        if not b64:
            return 'Could not capture screenshot. Make sure PIL or PySide6 is available.'

        prompt = question or 'What do you see on my screen? Be brief and helpful.'
        return self.analyze_image(b64, prompt)

    def look_at_clipboard(self, question=None):
        """Analyze an image from the clipboard."""
        b64, w, h = self.capture_from_clipboard()
        if not b64:
            return 'No image found in clipboard.'

        prompt = question or 'What do you see in this image? Be brief and helpful.'
        return self.analyze_image(b64, prompt)

    def look_at_file(self, file_path, question=None):
        """Analyze an image file."""
        b64, w, h = self.capture_from_file(file_path)
        if not b64:
            return f'Could not read image: {file_path}'

        prompt = question or 'What do you see in this image? Be brief and helpful.'
        return self.analyze_image(b64, prompt)

    def read_screen_text(self):
        """Specifically ask to read text visible on screen."""
        return self.look_at_screen('Read all visible text on the screen. List the key content you can see.')

    def check_screen_health(self):
        """Check if the user has been staring at the same thing too long."""
        return self.look_at_screen(
            'Look at this screen. Is the user likely working or idle? '
            'If you see signs of long work sessions (many tabs, code editor, documents), '
            'gently suggest a break using the 20-20-20 rule.'
        )
