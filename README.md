# KINETIK

> **Control reality with your bare hands.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-brightgreen.svg)](https://www.python.org/)
[![Physics: Pymunk](https://img.shields.io/badge/Physics-Pymunk_7-orange.svg)](https://www.pymunk.org/)
[![Vision: MediaPipe](https://img.shields.io/badge/Vision-MediaPipe_Tasks-blueviolet.svg)](https://developers.google.com/mediapipe)

**KINETIK** is an open-source, webcam-powered telekinesis playground that turns an ordinary computer camera into a hands-free physics controller. Pinch to grab virtual objects with natural spring lag, flick your wrist to fling them across the screen, cast force push shockwaves, and compete in the fast-paced **Target Rush** arcade mode.

100% local-first, zero telemetry, no account or API keys required.

---

## ⚡ Quickstart

### Automated Launcher (Recommended)
* **Windows**: Double-click [`setup.bat`](setup.bat) (or run `./setup.bat` in terminal).
* **Linux / macOS**: Run `chmod +x setup.sh && ./setup.sh`.

### Manual Setup
```bash
# 1. Clone repository
git clone https://github.com/devFiend/kinetik.git
cd kinetik

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch KINETIK
python main.py
```

---

## 🎮 Gestural Controls & Keybindings

| Gesture / Input | Action | Feedback |
| :--- | :--- | :--- |
| **Pinch (Thumb + Index)** | Grab nearest dynamic object within $80\text{px}$ radius | Electric lightning tether attaches to object; cyan focus ring |
| **Flick & Release** | Impart hand momentum with $1.4\times$ multiplier | High-speed release whoosh; kinetic motion blur trail |
| **Open Palm Forward Thrust** | Cast conical Force Push shockwave | Radial shockwave burst; bass boom; screen-shake |
| `[TAB]` | Toggle between **Target Rush** and **Free Play** | HUD mode switch |
| `[SPACE]` | Spawn bouncing kinetic sphere at hand focal point | Ambient spawn |
| `[B]` | Spawn heavy rigid crate | Physics spawn |
| `[R]` | Reset current game mode / Restart completed round | Simulation reset |
| `[G]` | Toggle Zero-Gravity floating mode | Gravity toggle |
| `[M]` | Toggle Audio Mute | Audio toggle |
| `[C]` | Toggle live camera video feed on/off | Background toggle |
| `[S]` | Toggle glowing hand skeleton overlay | Visual overlay |
| `[ESC / Q]` | Clean exit | System shutdown |

---

## 🕹️ Game Modes

### 1. Target Rush (60s Timed Arcade)
* Hit as many dynamic kinematic drones as possible before the clock expires!
* **Drone Types**:
  * **Standard Drone** (Cyan, $+100\text{ pts}$)
  * **Speed Runner** (Violet, fast oscillating trajectory, $+250\text{ pts}$)
  * **Golden Snitch** (Gold, rapid evasive drift, $+1000\text{ pts}$ and $+5.0\text{s}$ time bonus)
* **Combo Multiplier**: Tiers step up from $1.0\times \to 5.0\times$ with consecutive hits; decay gauge drains over $3.5\text{s}$.

### 2. Free Play Sandbox
* Unlimited kinetic physics playground with variable gravity, crates, bouncing balls, and zero time pressure.

---

## 🏆 Telekinetic Progression (8 Ranks)

Earn XP from Target Rush accuracy, combos, and trick shots:

$$\text{Awakening} \longrightarrow \text{Sensitive} \longrightarrow \text{Initiate} \longrightarrow \text{Manipulator} \longrightarrow \text{Adept} \longrightarrow \text{Master} \longrightarrow \text{Ascendant} \longrightarrow \text{Singularity}$$

Progress, high scores, and achievement badges persist automatically in local JSON (`storage/save.json`).

---

## 🧪 Testing

Run the automated test suite in headless mode (no webcam or physical display required):

```bash
pytest tests/ -v
```

All 38 automated test suites verify coordinate math, Schmitt-trigger pinch hysteresis, Pymunk constraint physics, procedural audio synthesis, and save serialization.

---

## 📚 Technical Documentation

Explore the complete technical and product documentation in [`docs/`](docs/INDEX.md):
* [Documentation Hub](docs/INDEX.md)
* [Product Requirements Document (PRD)](docs/PRD.md)
* [System Architecture](docs/ARCHITECTURE.md)
* [Development Phases & Milestones](docs/DEVELOPMENT_PHASES.md)
* [Features & Gamification Engine](docs/FEATURES_AND_GAMIFICATION.md)
* [Testing Strategy](docs/TESTING_STRATEGY.md)
* [Contributing Guide](docs/CONTRIBUTING.md)

---

## 📜 License

Distributed under the MIT License. Copyright (c) 2026 devFiend.
