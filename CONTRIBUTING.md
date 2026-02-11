# 🤝 Contributing to Ohverlay

Thank you for your interest in contributing to **Ohverlay**! This project is part of **Futol Ethical Technology Ecosystems** - we're building calm, ethical technology for better digital workspaces.

## 🏛️ Our Values

Before contributing, please understand our core principles:

```python
FUTOL_ETHICAL_PRINCIPLES = {
    "privacy_first": "Local processing by default",
    "transparency": "Open source, auditable code", 
    "user_control": "Opt-in, not opt-out",
    "calm_by_default": "Non-addictive, non-intrusive",
    "sustainability": "Low resource footprint",
    "accessibility": "Works on modest hardware"
}
```

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/ohverlay-v4.git
cd ohverlay-v4
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Run Tests

```bash
pytest tests/ -v
```

## 📋 Contribution Guidelines

### Code Style

We follow PEP 8 with some modifications:

```python
# ✅ Good - Calm, readable, well-documented
def calculate_swim_path(
    current_pos: np.ndarray,
    target_pos: np.ndarray,
    speed: float = 1.0
) -> np.ndarray:
    """
    Calculate smooth swimming path between positions.
    
    Args:
        current_pos: Current fish position [x, y]
        target_pos: Target position [x, y]
        speed: Swimming speed multiplier
        
    Returns:
        np.ndarray: New position vector
    """
    direction = target_pos - current_pos
    distance = np.linalg.norm(direction)
    
    if distance < 0.001:
        return current_pos
        
    return current_pos + (direction / distance) * speed * 0.016

# ❌ Bad - Hard to read, poorly documented
def calc(p, t, s=1):
    d = t - p
    return p + (d/np.linalg.norm(d))*s*0.016
```

### Performance Requirements

All code must work efficiently on **16GB RAM systems**:

```python
# ✅ Good - Memory efficient
class FishRenderer:
    def __init__(self):
        self._cache = {}  # LRU cache for sprites
        self._max_cache = 100  # Limit cache size

# ❌ Bad - Memory leak risk
class FishRenderer:
    def __init__(self):
        self._sprites = []  # Unbounded growth!
```

### Error Handling

Always provide graceful degradation:

```python
# ✅ Good - Graceful fallback
try:
    llm_response = self.llm_client.generate(prompt)
except APIError as e:
    logger.warning(f"LLM unavailable: {e}")
    llm_response = self.fallback_behavior()

# ❌ Bad - Crashes on error
def process_message(msg):
    return self.llm_client.generate(msg)  # No error handling!
```

## 🎯 Areas for Contribution

### 🐟 Fish Animation
- New swimming behaviors
- Additional fish species
- Improved physics

### 🎨 UI/UX
- New themes/skins
- Bubble designs
- Settings interface

### 🧠 AI Features
- Personality enhancements
- LLM integrations
- Behavioral patterns

### 🧪 Testing
- Unit tests
- Integration tests
- Performance benchmarks

### 📚 Documentation
- Code documentation
- User guides
- API documentation

## 🔄 Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation

3. **Test Thoroughly**
   ```bash
   pytest tests/
   python main.py --test-mode
   ```

4. **Commit with Clear Messages**
   ```bash
   git commit -m "feat: add sanctuary mode toggle"
   git commit -m "fix: memory leak in bubble renderer"
   git commit -m "docs: update API reference"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🐛 Reporting Bugs

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Clear reproduction steps
- Environment details
- Expected vs actual behavior
- Relevant logs

## 💡 Suggesting Features

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) and consider:

- Does it align with our ethical principles?
- Is it calm-by-default?
- Does it respect user privacy?

## 🏆 Recognition

Contributors will be:
- Listed in our `CONTRIBUTORS.md`
- Mentioned in release notes
- Credited in the application (if desired)

## 📞 Questions?

- Open a [Discussion](https://github.com/ikel-eidra/ohverlay-v4/discussions)
- Email: hello@futol.tech
- Discord: [Join our server](https://discord.gg/futol)

---

**Thank you for helping build ethical technology!** 🏢 Futol Ethical Technology Ecosystems
