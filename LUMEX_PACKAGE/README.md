# LUMEX PACKAGE - Betta Fish & Plants Division

**Owner:** Lumex  
**Source:** OHVERLAY-V4.0 Split

This package contains all biological creatures and plants that are now maintained by Lumex.

---

## 📦 Contents

### 🐟 `betta_skin.py`
**Standard Betta Fish Skin**
- Optimized for 16GB+ RAM systems
- Beautiful color palettes (Nemo Galaxy, Mustard Gas, Koi Candy, etc.)
- Smooth swimming animation
- Bubble communication system

**Usage:**
```python
from betta_skin import FishSkin
skin = FishSkin(config=config)
```

---

### 🐟 `betta_realistic_skin.py`
**Ultra-Realistic Betta Skin v2.0**
- Requires 32GB+ RAM for best performance
- 60-segment tail with Bezier curves
- 3D compound eyes with corneal bulge
- Protruding labyrinth mouth
- Gill plates and lateral line
- Traveling wave body undulation

**Usage:**
```python
from betta_realistic_skin import RealisticBettaSkin
skin = RealisticBettaSkin(config=config)
```

---

### 🌿 `aquarium_with_plants.py`
**Full Aquarium Engine with Plants**
- Needle-leaf plants (Cryptocoryne-style)
- 3-day growth cycle
- Plants grow UPWARD from taskbar top
- Does not cover Windows time/date
- 5-7 stems clustered bottom-right
- Ambient falling leaves (optional)

**Plant Features:**
- Daily growth progression
- Natural sway animation
- Resets cycle after 3 days
- Configurable growth speed

**Usage:**
```python
from aquarium_with_plants import AquariumSector
sector = AquariumSector(screen_geometry, sector_id, skin, bubble_system, config)
```

---

## 🎨 Betta Color Palettes

Included presets:
- **Nemo Galaxy** - Orange/Blue/White
- **Mustard Gas** - Blue/Yellow/Cream  
- **Koi Candy** - Red/White/Black
- **Black Orchid** - Deep purple/violet
- **Copper Dragon** - Bronze/Gold
- **Lavender Halfmoon** - Purple/Pink
- **Turquoise Butterfly** - Cyan/Blue
- **Royal Blue** - Deep blues

---

## 🚀 Integration

These files can be used standalone or integrated into any PySide6 application.

**Dependencies:**
- PySide6
- NumPy (for realistic skin)
- loguru (optional, for logging)

**Coordinates:**
- Supports dual monitors (3840x1080)
- Transparent overlay windows
- Click-through for desktop access

---

## 📁 File Structure

```
LUMEX_PACKAGE/
├── README.md                    # This file
├── betta_skin.py               # Standard Betta (16GB+)
├── betta_realistic_skin.py     # Ultra Betta (32GB+)
└── aquarium_with_plants.py     # Full aquarium + plants
```

---

## 📝 Notes

- These files were extracted from OHVERLAY-V4.0 main branch
- Plants code is fully functional with 3-day growth cycle
- Betta skins include all recent improvements
- Compatible with the bubble system and sanctuary zones

---

**Maintained by:** Lumex  
**Original Project:** OHVERLAY-V4.0
