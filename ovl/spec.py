"""
OVL Language Specification v1.0
================================
The complete grammar and semantics of the Ohverlay Language.

─── SYNTAX ───

Blocks start with @ and are indented:
  @keyword "name"
    property: value

Properties are key: value pairs.
Comments start with //
Multi-value properties use commas: color: cyan, magenta, green
Ranges use ~: speed: 0.5 ~ 1.2
Percentages: opacity: 70%
Colors: hex (#00d4ff), named (cyan), rgb(0,212,255)
Sizes: 800 x 600, fullscreen, 50% x 50%
Time: 2s, 500ms, 1.5m

─── BLOCKS ───

@overlay     - Root block, defines the overlay itself
@creature    - Animated entity (fish, jellyfish, fairy, etc.)
@particles   - Particle system (bubbles, sparks, snow, etc.)
@background  - Background effect (gradient, stars, waves)
@text        - Text/label overlay
@behavior    - Behavioral rules (react to screen context)
@video       - Video source overlay (converted to transparent)
@sound       - Audio cue (optional, for events)
@timer       - Countdown/elapsed timer display
@widget      - Interactive UI widget (note, chatbox)
@import      - Import another .ovl file as component

─── PROPERTIES ───

Common:
  style      : wireframe | solid | glow | ghost | particle | neon
  color      : <color> | rainbow | gradient(<color>, <color>)
  glow       : <color> <intensity 0-1>
  opacity    : <0-100>%
  position   : center | random | top-left | x, y
  size       : <w> x <h> | fullscreen | <percent>%
  speed      : slow | normal | fast | <number>
  count      : <number>
  loop       : true | false | <count>
  blend      : screen | lighten | overlay | normal
  z-index    : <number>

Creature-specific:
  movement   : float | drift | swim | bounce | orbit | wander | follow-cursor
  body       : fish | jellyfish | manta | fairy | whale | custom(<path>)
  fins       : flowing | rigid | none
  tail       : long | short | split
  eyes       : glow | blink | none
  trail      : particles | ribbon | none
  ai         : reactive | calm | playful | sleepy

Particle-specific:
  shape      : circle | star | spark | snowflake | heart | custom
  emit       : burst | stream | wave | rain
  direction  : up | down | radial | wind(<angle>)
  gravity    : <number> | none
  lifetime   : <time>
  fade       : in | out | pulse

Video-specific:
  source     : <path or url>
  convert    : wireframe | glow | ghost | silhouette | chroma
  key-color  : <color>   // for chroma key
  threshold  : <0-100>

Behavior-specific:
  on <event> : <action>
  Events: idle, stressed, creative, gaming, break, morning, evening, click
  Actions: drift slowly, pulse gently, flare, speed up, change color, hide, show

─── BUILT-IN CREATURES ───

  fish       : Betta fish with flowing fins
  jellyfish  : Translucent jellyfish with tentacles
  manta      : Manta ray with wing-like motion
  fairy      : Humanoid wireframe with wings
  whale      : Large gentle whale
  dolphin    : Playful dolphin
  octopus    : Multi-tentacle creature
  butterfly  : Winged butterfly
  dragon     : Eastern dragon (serpentine)
  phoenix    : Fire bird with particle trail

─── BUILT-IN PARTICLES ───

  bubbles    : Rising circular bubbles
  sparks     : Short-lived bright sparks
  snow       : Gentle falling snowflakes
  rain       : Vertical rain drops
  fireflies  : Glowing wandering dots
  cherry     : Cherry blossom petals
  stars      : Twinkling stars
  dust       : Floating dust motes
  embers     : Rising fire embers
  confetti   : Colorful falling confetti
"""

# ─── Token Types ───
TOKEN_TYPES = {
    "BLOCK": "@",
    "COMMENT": "//",
    "PROPERTY": ":",
    "STRING": '"',
    "NUMBER": "0-9",
    "PERCENT": "%",
    "SIZE_SEP": "x",
    "RANGE": "~",
    "COMMA": ",",
    "NEWLINE": "\n",
    "INDENT": "  ",
}

# ─── Valid Block Names ───
VALID_BLOCKS = {
    "overlay", "creature", "particles", "background", "text",
    "behavior", "video", "sound", "timer", "widget", "import",
    "quiz", "question",
}

# ─── Valid Styles ───
VALID_STYLES = {
    "wireframe", "solid", "glow", "ghost", "particle", "neon",
}

# ─── Valid Movements ───
VALID_MOVEMENTS = {
    "float", "drift", "swim", "bounce", "orbit", "wander", "follow-cursor",
}

# ─── Built-in Creatures ───
BUILTIN_CREATURES = {
    "fish", "jellyfish", "manta", "fairy", "whale",
    "dolphin", "octopus", "butterfly", "dragon", "phoenix",
}

# ─── Built-in Particle Types ───
BUILTIN_PARTICLES = {
    "bubbles", "sparks", "snow", "rain", "fireflies",
    "cherry", "stars", "dust", "embers", "confetti",
}

# ─── Named Colors ───
NAMED_COLORS = {
    "cyan": "#00d4ff",
    "magenta": "#ff00ff",
    "green": "#00ff96",
    "orange": "#ff6600",
    "white": "#ffffff",
    "pink": "#ff3366",
    "blue": "#0066ff",
    "purple": "#9933ff",
    "red": "#ff0000",
    "yellow": "#ffff00",
    "gold": "#ffd700",
    "teal": "#008080",
    "coral": "#ff7f50",
    "lavender": "#b380ff",
    "neon-blue": "#00d4ff",
    "neon-pink": "#ff00ff",
    "neon-green": "#39ff14",
}

# ─── Behavior Events ───
BEHAVIOR_EVENTS = {
    "idle", "stressed", "creative", "gaming", "break",
    "morning", "afternoon", "evening", "night",
    "click", "hover", "feed",
}

# ─── Behavior Actions ───
BEHAVIOR_ACTIONS = {
    "drift slowly", "pulse gently", "flare", "flare display",
    "speed up", "slow down", "change color", "hide", "show",
    "dart", "rest", "glow brighter", "dim", "celebrate",
}
