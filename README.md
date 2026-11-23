# KINETIK

**Control reality with your hands.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

KINETIK is an open-source, webcam-powered telekinesis playground. It turns your standard computer webcam into a hands-free controller: pinch to grab virtual objects, move them with natural physics lag, and flick your wrist to fling them across the screen.

---

## ⚡ Quickstart

```bash
# Clone the repository
git clone https://github.com/devFiend/kinetik.git
cd kinetik

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch KINETIK
python main.py
```

---

## 🎮 Controls

* **Pinch (Thumb + Index)**: Grab and hold nearest physics object within reach.
* **Flick & Release**: Impart momentum and throw the held object.
* **Open Palm Push**: Cast kinetic shockwave repelling nearby objects.
* **Space**: Spawn new physics objects.
* **R**: Reset physics world.
* **M**: Toggle audio mute.
* **Esc**: Pause / Exit.

---

## 📖 Documentation

* [Documentation Hub](docs/INDEX.md)
* [Product Requirements Document (PRD)](docs/PRD.md)
* [System Architecture](docs/ARCHITECTURE.md)
* [Development Phases](docs/DEVELOPMENT_PHASES.md)
* [Features & Gamification Engine](docs/FEATURES_AND_GAMIFICATION.md)
* [Testing Strategy](docs/TESTING_STRATEGY.md)
* [Contributing Guide](docs/CONTRIBUTING.md)

---

## 📜 License

MIT License. Copyright (c) 2026 devFiend.
