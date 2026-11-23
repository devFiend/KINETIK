# Contributing to KINETIK

Welcome! We are thrilled that you are interested in contributing to **KINETIK** — the open-source, webcam-powered telekinesis playground.

KINETIK is built by and for developers, creative coders, and gamers who love pushing the boundaries of human-computer interaction (HCI). Whether you want to add a new game mode, create dynamic visual shaders, optimize physics constraints, or refine gesture heuristics, your contributions are welcome.

---

## 1. Code of Conduct & Values

* **Respect & Inclusivity**: Be welcoming, friendly, and patient.
* **Game-Feel First**: Every pull request altering controls or physics should be evaluated against tactile responsiveness and fun.
* **Local-First & Privacy Always**: KINETIK will never include cloud telemetry, trackers, or account requirements. All code must run offline.

---

## 2. Development Setup

### 2.1 Prerequisites
* Python 3.12+ (CPython recommended)
* A functioning USB or integrated laptop webcam (or recorded test video feed)
* Git

### 2.2 Local Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/devFiend/kinetik.git
   cd kinetik
   ```

2. **Create and activate a virtual environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pytest pytest-cov ruff mypy
   ```

4. **Verify the environment**:
   ```bash
   # Run automated test suite
   pytest
   
   # Launch game in test mode
   python main.py --mode sandbox --debug
   ```

---

## 3. Architecture Decision Records (ADR)

If you are proposing a significant architectural change (e.g., swapping physics solvers, migrating to GPU shader pipelines, or modifying the threading model), please submit an **ADR** in `docs/adr/` before starting implementation.

Each ADR should follow this format:
```markdown
# ADR-00X: [Short Descriptive Title]

* **Status**: [Proposed | Accepted | Superseded]
* **Deciders**: [Names / Handles]
* **Date**: [YYYY-MM-DD]

## Context & Problem Statement
What problem are we solving? Why does the current architecture fall short?

## Decision Drivers
* Performance (FPS / Latency)
* Cross-platform compatibility
* Code ergonomics & maintainability

## Considered Options
1. Option A
2. Option B

## Decision Outcome & Consequences
Why Option A was chosen, trade-offs accepted, and implementation roadmap.
```

---

## 4. Coding Standards & Style

* **Language**: Python 3.12+.
* **Formatting & Linting**: We use **Ruff** for high-speed linting and code formatting:
  ```bash
  ruff check .
  ruff format .
  ```
* **Type Annotations**: All public classes, functions, and method signatures must include Python type hints (`typing` / `types`).
* **Docstrings**: Google-style docstrings for non-trivial functions and classes.
* **Headless Capability**: Ensure all game and physics logic can be instantiated without requiring active display hardware or camera frames (see [Testing Strategy](./TESTING_STRATEGY.md)).

---

## 5. Branching & Commit Conventions

### 5.1 Branch Naming
* `feature/<short-description>`: New gameplay mechanics, abilities, or modes.
* `fix/<bug-description>`: Bug fixes or stability patches.
* `perf/<area>`: Performance and latency optimizations.
* `docs/<topic>`: Documentation enhancements.

### 5.2 Conventional Commits
Commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:
* `feat(gestures): add two-finger stasis hover pose classifier`
* `fix(physics): prevent ball tunneling through floor at high velocities`
* `perf(vision): decouple mediapipe inference into dedicated worker thread`
* `docs(prd): expand target rush scoring specification`

---

## 6. Pull Request Checklist

Before submitting your PR, ensure:
- [ ] Code is formatted with `ruff format .` and passes `ruff check .`.
- [ ] All existing and new tests pass via `pytest tests/`.
- [ ] Code does not introduce blocking delays into the main 60 FPS Pygame loop.
- [ ] Telekinesis mechanics are tested for comfortable sensitivity and hysteresis stability.
- [ ] Documentation in `docs/` is updated if requirements or APIs changed.

---

## 7. Community & Questions

Have ideas or questions?
* **Discussions & Ideas**: Open an issue labeled `discussion` or `proposal`.
* **Bug Reports**: Use the GitHub Bug Report issue template with camera model, OS version, and console logs.
