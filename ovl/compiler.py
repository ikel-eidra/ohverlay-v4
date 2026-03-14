"""
OVL Compiler - Compiles OVL AST to HTML5 Canvas Overlays
==========================================================
Takes parsed OVLNode trees and generates standalone HTML files
with canvas-based animations.

Usage:
    from ovl.parser import parse_ovl
    from ovl.compiler import compile_ovl

    ast = parse_ovl('''
    @overlay "Neon Jellyfish"
      type: ambient
      size: 800 x 600

      @creature jellyfish
        style: wireframe
        glow: cyan 0.8
        count: 3
        movement: float, drift
        speed: slow
    ''')

    html = compile_ovl(ast)
    # → Complete standalone HTML file
"""

from typing import List, Optional
from ovl.parser import OVLNode
from ovl.spec import NAMED_COLORS


class OVLCompiler:
    """Compiles OVL AST into HTML5 Canvas overlay files."""

    def __init__(self):
        self.overlay_name = "Ohverlay"
        self.width = "window.innerWidth"
        self.height = "window.innerHeight"
        self.fixed_size = False

    def compile(self, nodes: List[OVLNode]) -> str:
        """Compile a list of OVLNodes into a complete HTML file."""
        if not nodes:
            return self._empty_overlay()

        # Find root @overlay block
        overlay = None
        for node in nodes:
            if node.type == "overlay":
                overlay = node
                break

        if not overlay:
            # Treat all nodes as children of an implicit overlay
            overlay = OVLNode("overlay", "Ohverlay", children=nodes)

        self.overlay_name = overlay.name or "Ohverlay"

        # Parse size
        size = overlay.get("size")
        if isinstance(size, dict) and size.get("type") == "size":
            if size["width"] != "full":
                self.width = str(size["width"])
                self.height = str(size["height"])
                self.fixed_size = True

        # Collect all generation parts
        creatures_js = []
        particles_js = []
        behaviors_js = []
        video_js = []

        for child in overlay.children:
            if child.type == "creature":
                creatures_js.append(self._compile_creature(child))
            elif child.type == "particles":
                particles_js.append(self._compile_particles(child))
            elif child.type == "behavior":
                behaviors_js.append(self._compile_behavior(child))
            elif child.type == "video":
                video_js.append(self._compile_video(child))
            elif child.type == "text":
                creatures_js.append(self._compile_text(child))
            elif child.type == "background":
                creatures_js.append(self._compile_background(child))

        # Assemble HTML
        return self._assemble(
            creatures_js="\n".join(creatures_js),
            particles_js="\n".join(particles_js),
            behaviors_js="\n".join(behaviors_js),
            video_js="\n".join(video_js),
            overlay_node=overlay,
        )

    def _resolve_color(self, color_val):
        """Resolve a color value to hex string."""
        if isinstance(color_val, dict):
            if color_val.get("type") == "color":
                return color_val["value"]
            if color_val.get("type") == "glow":
                return color_val["color"]
        if isinstance(color_val, str):
            return NAMED_COLORS.get(color_val.lower(), color_val)
        return "#00d4ff"

    def _resolve_number(self, val, default=1.0):
        """Resolve a value to a number."""
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, dict):
            if val.get("type") == "percent":
                return val["value"] / 100
            if val.get("type") == "range":
                return (val["min"] + val["max"]) / 2
        if isinstance(val, str):
            try:
                return float(val)
            except ValueError:
                pass
        return default

    def _speed_to_number(self, val):
        """Convert speed keyword to number."""
        if isinstance(val, str):
            speeds = {"slow": 0.5, "normal": 1.0, "fast": 2.0, "very-slow": 0.25, "very-fast": 3.0}
            return speeds.get(val.lower(), 1.0)
        return self._resolve_number(val, 1.0)

    def _compile_creature(self, node: OVLNode) -> str:
        """Compile a @creature block into JS class."""
        name = node.name or "creature"
        body = name.lower()
        style = node.get("style", "wireframe")
        color = self._resolve_color(node.get("color") or node.get("glow", "#00d4ff"))
        glow_intensity = 0.6
        glow_val = node.get("glow")
        if isinstance(glow_val, dict) and glow_val.get("type") == "glow":
            glow_intensity = glow_val.get("intensity", 0.6)
        count = int(self._resolve_number(node.get("count", 1)))
        speed = self._speed_to_number(node.get("speed", "normal"))
        opacity = self._resolve_number(node.get("opacity", 0.8))

        # Movement types
        movements = node.get("movement", "float")
        if isinstance(movements, dict) and movements.get("type") == "list":
            move_list = [str(m) for m in movements["items"]]
        elif isinstance(movements, str):
            move_list = [movements]
        else:
            move_list = ["float"]

        # Generate creature-specific drawing code
        draw_code = self._get_creature_draw(body, style, color, glow_intensity)

        return f"""
// ─── Creature: {name} ───
class Creature_{name.replace('-','_')} {{
  constructor(x, y) {{
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 2 * {speed};
    this.vy = (Math.random() - 0.5) * 2 * {speed};
    this.phase = Math.random() * Math.PI * 2;
    this.size = 30 + Math.random() * 20;
    this.opacity = {opacity};
    this.speed = {speed};
    this.color = '{color}';
    this.glowIntensity = {glow_intensity};
    this.movements = {move_list};
  }}

  update(dt, w, h) {{
    this.phase += dt * this.speed;
    // Movement: float + drift
    this.x += this.vx * dt * 60;
    this.y += this.vy * dt * 60;
    this.vy += Math.sin(this.phase * 0.5) * 0.02 * this.speed;
    this.vx += Math.cos(this.phase * 0.3) * 0.015 * this.speed;
    // Boundaries
    if (this.x < -50) this.x = w + 50;
    if (this.x > w + 50) this.x = -50;
    if (this.y < -50) this.y = h + 50;
    if (this.y > h + 50) this.y = -50;
    // Damping
    this.vx *= 0.998;
    this.vy *= 0.998;
  }}

  draw(ctx) {{
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.globalAlpha = this.opacity;
    {draw_code}
    ctx.restore();
  }}
}}

const {name.replace('-','_')}_instances = [];
for (let i = 0; i < {count}; i++) {{
  {name.replace('-','_')}_instances.push(
    new Creature_{name.replace('-','_')}(
      Math.random() * canvas.width,
      Math.random() * canvas.height
    )
  );
}}
creatures.push(...{name.replace('-','_')}_instances);
"""

    def _get_creature_draw(self, body, style, color, glow_intensity):
        """Generate the canvas draw code for a creature type."""
        glow_blur = max(2, int(glow_intensity * 15))

        if body in ("jellyfish",):
            return f"""
    // Jellyfish body
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = {glow_blur};
    // Bell
    ctx.beginPath();
    const bellW = this.size;
    const bellH = this.size * 0.6;
    const pulse = Math.sin(this.phase * 2) * 0.15;
    ctx.ellipse(0, 0, bellW * (1 + pulse), bellH * (1 - pulse * 0.5), 0, Math.PI, 0);
    ctx.stroke();
    // Tentacles
    for (let t = 0; t < 7; t++) {{
      ctx.beginPath();
      const tx = -bellW + (t / 6) * bellW * 2;
      ctx.moveTo(tx, 0);
      for (let s = 1; s <= 5; s++) {{
        const sx = tx + Math.sin(this.phase + t + s * 0.5) * 8;
        const sy = s * this.size * 0.25;
        ctx.lineTo(sx, sy);
      }}
      ctx.stroke();
    }}
    ctx.shadowBlur = 0;"""

        elif body in ("fish", "betta"):
            return f"""
    // Fish body
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = {glow_blur};
    const facing = this.vx >= 0 ? 1 : -1;
    ctx.scale(facing, 1);
    // Body
    ctx.beginPath();
    ctx.ellipse(0, 0, this.size, this.size * 0.4, 0, 0, Math.PI * 2);
    ctx.stroke();
    // Tail
    const tailSwing = Math.sin(this.phase * 3) * 0.3;
    ctx.beginPath();
    ctx.moveTo(-this.size, 0);
    ctx.quadraticCurveTo(-this.size * 1.5, -this.size * 0.5 + tailSwing * 20, -this.size * 1.8, -this.size * 0.3);
    ctx.moveTo(-this.size, 0);
    ctx.quadraticCurveTo(-this.size * 1.5, this.size * 0.5 + tailSwing * 20, -this.size * 1.8, this.size * 0.3);
    ctx.stroke();
    // Eye
    ctx.beginPath();
    ctx.arc(this.size * 0.5, -this.size * 0.1, 3, 0, Math.PI * 2);
    ctx.stroke();
    ctx.shadowBlur = 0;"""

        elif body in ("manta",):
            return f"""
    // Manta ray
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = {glow_blur};
    const wingFlap = Math.sin(this.phase * 1.5) * 0.3;
    // Wings
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(-this.size * 1.5, -this.size * wingFlap, -this.size * 2, this.size * 0.2 * wingFlap);
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(this.size * 1.5, -this.size * wingFlap, this.size * 2, this.size * 0.2 * wingFlap);
    ctx.stroke();
    // Body
    ctx.beginPath();
    ctx.ellipse(0, 0, this.size * 0.4, this.size * 0.8, 0, 0, Math.PI * 2);
    ctx.stroke();
    // Tail
    ctx.beginPath();
    ctx.moveTo(0, this.size * 0.8);
    const tailSway = Math.sin(this.phase * 2) * 10;
    ctx.quadraticCurveTo(tailSway, this.size * 1.5, tailSway * 0.5, this.size * 2.5);
    ctx.stroke();
    ctx.shadowBlur = 0;"""

        elif body in ("fairy",):
            return f"""
    // Fairy wireframe
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = {glow_blur};
    const bob = Math.sin(this.phase * 2) * 3;
    // Body
    ctx.beginPath();
    ctx.moveTo(0, -this.size * 0.5 + bob);
    ctx.lineTo(0, this.size * 0.3 + bob);
    ctx.stroke();
    // Head
    ctx.beginPath();
    ctx.arc(0, -this.size * 0.6 + bob, this.size * 0.15, 0, Math.PI * 2);
    ctx.stroke();
    // Wings
    const wingBeat = Math.sin(this.phase * 4) * 0.4;
    ctx.beginPath();
    ctx.ellipse(-this.size * 0.3, -this.size * 0.2 + bob, this.size * 0.5, this.size * 0.25 * (1 + wingBeat), -0.3 + wingBeat, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(this.size * 0.3, -this.size * 0.2 + bob, this.size * 0.5, this.size * 0.25 * (1 + wingBeat), 0.3 - wingBeat, 0, Math.PI * 2);
    ctx.stroke();
    ctx.shadowBlur = 0;"""

        else:
            # Generic glowing orb for unknown creatures
            return f"""
    // Generic creature
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = {glow_blur};
    ctx.beginPath();
    const pulse = 1 + Math.sin(this.phase * 2) * 0.1;
    ctx.arc(0, 0, this.size * pulse, 0, Math.PI * 2);
    ctx.stroke();
    // Inner ring
    ctx.beginPath();
    ctx.arc(0, 0, this.size * 0.5 * pulse, 0, Math.PI * 2);
    ctx.stroke();
    ctx.shadowBlur = 0;"""

    def _compile_particles(self, node: OVLNode) -> str:
        """Compile a @particles block into JS."""
        name = node.name or "particles"
        count = int(self._resolve_number(node.get("count", 30)))
        color = self._resolve_color(node.get("color", "#00d4ff"))
        opacity = self._resolve_number(node.get("opacity", 0.5))
        speed = self._speed_to_number(node.get("speed", "slow"))

        emit = node.get("emit", "stream")
        direction = node.get("direction", "up")
        shape = node.get("shape", "circle")

        # Direction vector
        dy = -1 if direction == "up" else (1 if direction == "down" else 0)
        dx = 0

        return f"""
// ─── Particles: {name} ───
class Particle_{name.replace('-','_')} {{
  constructor(w, h) {{
    this.reset(w, h);
  }}
  reset(w, h) {{
    this.x = Math.random() * w;
    this.y = {'Math.random() * h' if direction != 'up' else 'h + Math.random() * 20'};
    this.vx = (Math.random() - 0.5) * 0.5 * {speed};
    this.vy = {dy} * (0.3 + Math.random() * 0.7) * {speed};
    this.size = 1 + Math.random() * 3;
    this.opacity = Math.random() * {opacity};
    this.life = 1.0;
    this.decay = 0.002 + Math.random() * 0.005;
    this.phase = Math.random() * Math.PI * 2;
  }}
  update(dt, w, h) {{
    this.x += this.vx * dt * 60;
    this.y += this.vy * dt * 60;
    this.vx += Math.sin(this.phase + performance.now() * 0.001) * 0.01;
    this.life -= this.decay;
    if (this.life <= 0 || this.y < -10 || this.y > h + 10) this.reset(w, h);
  }}
  draw(ctx) {{
    ctx.globalAlpha = this.opacity * this.life;
    ctx.fillStyle = '{color}';
    ctx.shadowColor = '{color}';
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }}
}}

const {name.replace('-','_')}_list = [];
for (let i = 0; i < {count}; i++) {{
  {name.replace('-','_')}_list.push(new Particle_{name.replace('-','_')}(canvas.width, canvas.height));
}}
particleSystems.push({name.replace('-','_')}_list);
"""

    def _compile_behavior(self, node: OVLNode) -> str:
        """Compile @behavior rules into JS."""
        behaviors = node.properties.get("behaviors", {})
        if not behaviors:
            return ""

        rules = []
        for event, action in behaviors.items():
            rules.append(f'    "{event}": "{action}"')

        joined = ',\n'.join(rules)
        return f"""
// ─── Behavior Rules ───
const behaviorRules = {{
{joined}
}};
"""

    def _compile_video(self, node: OVLNode) -> str:
        """Compile @video block (video source overlay)."""
        source = node.get("source", "")
        convert = node.get("convert", "wireframe")
        return f"""
// ─── Video Overlay ───
// Source: {source}
// Convert mode: {convert}
// (Requires video-converter pipeline)
"""

    def _compile_text(self, node: OVLNode) -> str:
        """Compile @text block."""
        content = node.get("content", node.name or "")
        color = self._resolve_color(node.get("color", "#00d4ff"))
        size = self._resolve_number(node.get("font-size", 14))
        return f"""
// ─── Text: {content} ───
function drawText(ctx) {{
  ctx.font = '{int(size)}px monospace';
  ctx.fillStyle = '{color}';
  ctx.shadowColor = '{color}';
  ctx.shadowBlur = 8;
  ctx.globalAlpha = 0.7;
  ctx.fillText("{content}", 20, 30);
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}}
textDraws.push(drawText);
"""

    def _compile_background(self, node: OVLNode) -> str:
        """Compile @background effect."""
        return ""  # Background effects drawn as full-canvas operations

    def _assemble(self, creatures_js, particles_js, behaviors_js, video_js, overlay_node):
        """Assemble the final HTML file."""
        blend = overlay_node.get("blend", "screen")

        w_expr = self.width
        h_expr = self.height

        return f"""<!--
  {self.overlay_name}
  Generated by OVL Compiler v1.0
  Ohverlay Factory - ohverlay.com
-->
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{self.overlay_name}</title>
<style>
  * {{ margin: 0; padding: 0; }}
  body {{ background: transparent; overflow: hidden; }}
  canvas {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    mix-blend-mode: {blend};
  }}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

function resize() {{
  canvas.width = {w_expr};
  canvas.height = {h_expr};
}}
resize();
window.addEventListener('resize', resize);

const creatures = [];
const particleSystems = [];
const textDraws = [];

{creatures_js}

{particles_js}

{behaviors_js}

{video_js}

let lastTime = performance.now();

function animate(now) {{
  const dt = Math.min((now - lastTime) / 1000, 0.1);
  lastTime = now;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const w = canvas.width, h = canvas.height;

  // Update and draw creatures
  for (const c of creatures) {{
    c.update(dt, w, h);
    c.draw(ctx);
  }}

  // Update and draw particles
  for (const system of particleSystems) {{
    for (const p of system) {{
      p.update(dt, w, h);
      p.draw(ctx);
    }}
  }}

  // Draw text overlays
  for (const fn of textDraws) fn(ctx);

  requestAnimationFrame(animate);
}}

requestAnimationFrame(animate);
</script>
</body>
</html>"""

    def _empty_overlay(self):
        return """<!DOCTYPE html><html><head><title>Empty Ohverlay</title>
<style>body{background:transparent;}</style></head><body></body></html>"""


def compile_ovl(nodes: List[OVLNode]) -> str:
    """Convenience function to compile OVL AST to HTML."""
    compiler = OVLCompiler()
    return compiler.compile(nodes)


def compile_ovl_file(filepath: str, output_path: str = None) -> str:
    """Parse and compile an .ovl file to HTML."""
    from ovl.parser import parse_ovl_file
    nodes = parse_ovl_file(filepath)
    html = compile_ovl(nodes)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    return html
