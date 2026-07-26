# 🌿 Ohverlay — Living Ambient Desktop Environment

<div align="center">

![Ohverlay Banner](https://img.shields.io/badge/Ohverlay-v4.0.0-2563eb?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green?style=for-the-badge&logo=qt&logoColor=white)
![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Offline-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)

**Transform your desktop into a tranquil, living digital ecosystem.**  
Ohverlay renders ultra-lightweight, frameless, transparent nature overlays right over your Windows desktop. 

[Explore Features](#-key-features) • [Installation](#-quick-start) • [Control Center](#-floating-control-center) • [Website](#-official-website) • [Privacy](#-privacy--security)

</div>

---

## ✨ Overview

**Ohverlay** brings subtle, organic life to your workspace without distracting your workflow or draining your system resources. Floating seamlessly above your applications and wallpaper, ambient nature species drift, hover, and respond to environmental time cycles across all your displays.

```
       .---.          🌿 Dandelion Seeds floating gently on the breeze
      /     \         ✨ Fireflies glowing with realistic bioluminescent ignition
     |  (o)  |        🪶 Dragonflies hovering with metallic sheer 3D wings
      \     /         
       '---'          ⚡ Click-Through • Zero CPU Lag • 100% Private
```

---

## 🌟 Key Features

### 🪟 Living Ambient Species
- **✨ Bioluminescent Fireflies:** Realistic 3D depth, organic ignition phase curves, abdominal lantern gradients, and flight turbulence.
- **🪶 Metallic Dragonflies:** Detailed 10-segment abdominal gradients, compound eye radial highlights, translucent wing veining, and 3D darting trajectories.
- **🌱 Drifting Dandelion Pappus:** 48 individual reference filaments per seed head, achene seed coats, and periodic 20-minute gentle breeze impulses.

### 🎛️ Floating Control Center
- **Quick-Access Dock:** Left-click the system tray icon to reveal a sleek floating control panel anchored above your taskbar.
- **Independent Quantity Sliders:** Adjust quantity (1–12) for each species independently in real-time.
- **Independent Scale Selection:** Set individual sizing (`Small`, `Normal`, `Large`) per species.
- **First-Run Welcome Guide:** Instant onboarding card detailing tray controls and hotkeys.

### ⚡ Performance & Desktop Integration
- **Click-Through Transparency:** All overlays use hardware-accelerated transparent canvas windows (`Qt.WindowTransparentForInput`) so your mouse clicks pass right through to your apps.
- **Ultra Low Memory Footprint:** Built on native PySide6 Qt WebEngine, consuming negligible CPU/RAM.
- **Multi-Monitor Support:** Automatically spans across your multi-display layout seamlessly.

---

## 🎮 Global Hotkeys

Stay in complete control with global keyboard shortcuts:

| Shortcut | Function | Description |
|---|---|---|
| `<Ctrl> + <Alt> + H` | **Toggle Overlays** | Instant hide/show for all active desktop overlays |
| `<Ctrl> + <Alt> + I` | **Toggle Interactivity** | Switch overlays between click-through and interactive modes |
| `<Ctrl> + <Alt> + F` | **Ambient Action** | Trigger an immediate gentle breeze across nature species |

---

## 🚀 Quick Start

### Option A: Portable Pre-Built Executable (Recommended)
1. Download the latest `Ohverlay-Portable.zip` from the [Releases](https://github.com/michaelfutol/ohverlay-v4/releases) page or build it locally.
2. Extract the ZIP file to any directory on your PC.
3. Double-click `Ohverlay.exe`.
4. Look for the stylized **O** icon in your system tray!

### Option B: Run from Source
```bash
# 1. Clone the repository
git clone https://github.com/michaelfutol/ohverlay-v4.git
cd ohverlay-v4

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Ohverlay
python main.py
```

---

## 🛠️ Building Standalone App & Installer

To generate a fresh portable build or installer package:

```bash
# Build Portable ZIP (located in installer_output/Ohverlay-Portable.zip)
python build.py --zip

# Build Windows Installer (.exe setup)
python build.py --installer
```

---

## 🔒 Privacy & Security

Ohverlay is designed around strict privacy principles:
- **100% Local Execution:** No background network calls, no analytics, no telemetry.
- **Zero Screen Recording:** Ohverlay never captures, inspects, or transmits your desktop or app windows.
- **Open Source Transparency:** Read our full [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

---

## 🌐 Official Website

Visit our landing page in the [`website/`](website/) directory or browse live documentation:
- [Website Landing Page](website/index.html)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Product Doctrine](docs/PRODUCT_DOCTRINE.md)
- [Marketing Strategy](docs/MARKETING_STRATEGY.md)

---

<div align="center">

Crafted with care by **FutolTech** • [GitHub Repository](https://github.com/michaelfutol/ohverlay-v4)

</div>
