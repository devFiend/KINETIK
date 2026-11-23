# KINETIK: Development Phases & Roadmap

* **Document Version**: 1.0.0  
* **Roadmap Model**: Milestone-Driven Iterative Delivery (`P0` through `P8`)  
* **Guiding Heuristic**: *Interaction quality $\to$ Responsiveness $\to$ Visual juice $\to$ Game modes $\to$ Progression $\to$ Polish.*

---

## 1. Roadmap Overview & Timeline

The KINETIK roadmap is structured to ensure that before expanding into complex scoring, progression, or UI trees, the foundational telekinetic interaction is polished, rock-solid, and immediately satisfying.

```mermaid
flowchart LR
    P0[P0: Setup] --> P1[P1: Vision]
    P1 --> P2[P2: Input]
    P2 --> P3[P3: Physics]
    P3 --> P4[P4: Telekinesis]
    P4 --> P5[P5: Feel]
    P5 --> P6[P6: Game]
    P6 --> P7[P7: Progression]
    P7 --> P8[P8: Release]
```

---

## 2. Phase-by-Phase Execution Plan

### Phase P0 — Setup & Foundation
* **Deliverable**: Development environment, virtual environment configuration, modular skeleton, dependency lock, CI/test scaffold, and application entry point.
* **Key Tasks**:
  1. Initialize Python 3.12+ virtual environment (`venv`).
  2. Pin dependencies in `requirements.txt`: `opencv-python`, `mediapipe`, `pygame`, `pymunk`, `numpy`, `pytest`.
  3. Scaffold repository directory structure (`src/`, `assets/`, `tests/`, `docs/`).
  4. Write barebones `main.py` verifying SDL2 window initialization and clean termination.
* **Acceptance Criteria**:
  * `python main.py` opens a responsive Pygame window and exits cleanly on `ESC` or window close.
  * `pytest tests/` runs and passes baseline environment sanity checks.
  * All documentation files indexed and linked.

---

### Phase P1 — Computer Vision Pipeline
* **Deliverable**: Threaded webcam frame acquisition and MediaPipe Hand Landmarker integration.
* **Key Tasks**:
  1. Implement `src/camera/webcam.py` with multi-threaded capture worker and OpenCV frame conversion.
  2. Implement `src/camera/hand_tracker.py` wrapping MediaPipe Hand Landmarker.
  3. Create mirror mode toggle ($X$-axis horizontal flip) for intuitive natural movement.
  4. Implement robust camera disconnect and permission fallback handling.
* **Acceptance Criteria**:
  * Live camera preview renders at steady $\ge 30\text{ FPS}$.
  * MediaPipe accurately tracks 21 hand landmarks under standard indoor lighting.
  * System displays clear "Camera Unavailable" / "Tracking Lost" indicators without crashing.

---

### Phase P2 — Input Processing & Gesture Engine
* **Deliverable**: Coordinate mapping, EMA/1€ signal smoothing, and dual-threshold pinch detection.
* **Key Tasks**:
  1. Map normalized $[0..1]$ hand landmarks to dynamic Pygame screen dimensions $[W, H]$.
  2. Implement `src/gestures/motion.py` providing adaptive Exponential Moving Average (EMA) and rolling velocity buffer.
  3. Implement `src/gestures/pinch.py` computing Euclidean thumb-to-index distance with Schmitt trigger hysteresis ($\theta_{enter} = 0.055, \theta_{exit} = 0.085$).
  4. Add visual cursor reticle that tracks hand anchor and animates during pinch state transitions.
* **Acceptance Criteria**:
  * Hand cursor tracks smoothly across the screen without jitter during static hold.
  * Pinch transition is stable with zero rapid on/off flickering when fingers are near the boundary.
  * Latency from physical hand movement to on-screen cursor displacement is imperceptible ($< 40\text{ms}$).

---

### Phase P3 — Physics Sandbox
* **Deliverable**: Pymunk 2D rigid-body simulation space with walls, gravity, and interactive entities.
* **Key Tasks**:
  1. Implement `src/physics/world.py` configuring Pymunk Space, gravity vector ($g = 900\text{ px/s}^2$), and boundary collision segments.
  2. Implement `src/physics/objects.py` supporting dynamic circles (balls), boxes (crates), and static target posts.
  3. Wire keyboard test controls: `SPACE` to spawn objects, `R` to reset simulation.
* **Acceptance Criteria**:
  * Objects drop, collide, bounce, and settle realistically on boundaries and against each other.
  * Pymunk simulation steps at fixed $60\text{Hz}$ rate independent of camera frame rate.

---

### Phase P4 — Telekinetic Interaction Loop (Core MVP)
* **Deliverable**: Full grab, soft-spring hold, kinetic throw, and open-palm push mechanics.
* **Key Tasks**:
  1. Implement proximity selection: calculate distance from hand anchor to nearest rigid body; lock target when pinch activates within selection radius $R_{select} = 80\text{px}$.
  2. Implement `src/physics/constraints.py`: attach target body to hand kinematic body via `Pymunk.DampedSpring` or `PivotJoint`.
  3. Implement kinetic release throw: sample rolling velocity history ($N=5$ frames); apply impulse vector $\mathbf{J} = m \cdot \mathbf{v}_{throw}$ on pinch release with safety velocity clamp.
  4. Implement open-palm push: detect forward motion / open palm gesture and cast radial impulse wave repelling unheld nearby objects.
* **Acceptance Criteria**:
  * Player can reliably pinch near a ball, lift it into the air, carry it smoothly across the screen, and fling it into boundary walls.
  * Thrown objects inherit intuitive release velocity; maximum velocity is clamped to prevent physics glitching.
  * If tracking drops momentarily while holding an object, a $300\text{ms}$ grace period prevents premature drop.

---

### Phase P5 — Game Feel & Sensory Juice
* **Deliverable**: Luminous visual effects, particle simulation, dynamic audio synthesis, and screen-shake.
* **Key Tasks**:
  1. Implement `src/rendering/effects.py`: dynamic bezier energy tether connecting hand cursor to held object with lightning sine displacement.
  2. Implement `src/rendering/particles.py`: object-pooled particle engine generating release trails, impact bursts, and pinch spark rings.
  3. Implement micro screen-shake triggered by high-energy collisions.
  4. Implement `Pygame.mixer` audio triggers: telekinetic hum (pitch modulated by hand velocity), grab chime, whoosh throw, and impact thuds.
* **Acceptance Criteria**:
  * Holding an object feels responsive, tactile, and visually vibrant.
  * High-velocity collisions generate satisfying impact particles, audio feedback, and screen shake.
  * Frame rate maintains $\ge 60\text{ FPS}$ during particle emissions.

---

### Phase P6 — Game Modes & Scoring Engine
* **Deliverable**: Free Play sandbox and structured "Target Rush" arcade game mode.
* **Key Tasks**:
  1. Implement `src/game/modes.py` with state machine (`INIT`, `PLAYING`, `PAUSED`, `ROUND_OVER`).
  2. Build "Target Rush": 60-second countdown, dynamic target spawning (static, drifting, and bonus gold targets).
  3. Implement `src/game/scoring.py`: score accumulation, combo multiplier ($1\times \to 5\times$) with decaying streak timer, and accuracy tracking.
  4. Display Game Over round summary screen with final score, accuracy %, and restart prompt.
* **Acceptance Criteria**:
  * A full 60-second Target Rush round can be started, played, scored, and restarted seamlessly.
  * Hitting targets consecutively increments combo; missing or letting timer expire resets combo.

---

### Phase P7 — Progression, Unlocks & Local Save
* **Deliverable**: Experience points (XP), telekinetic ranks, achievements, and persistent local storage.
* **Key Tasks**:
  1. Implement rank hierarchy: `Awakening` $\to$ `Sensitive` $\to$ `Initiate` $\to$ `Manipulator` $\to$ `Adept` $\to$ `Master` $\to$ `Ascendant` $\to$ `Singularity`.
  2. Implement `src/storage/save_manager.py`: atomic JSON serialization (`save.json`) storing total XP, highest scores, unlocked object skins, and earned achievement badges.
  3. Implement unlockable rewards: neon energy tether colors (Cyan, Violet, Emerald, Solar Gold), cosmic particle trails, and heavy tungsten metal balls.
* **Acceptance Criteria**:
  * XP and high scores persist across game restarts in local JSON.
  * Unlocking a rank triggers celebratory HUD callout and updates selectable cosmetic options.

---

### Phase P8 — Packaging, Polish & Open-Source Release
* **Deliverable**: Open-source release assets, cross-platform packaging, comprehensive docs, and community templates.
* **Key Tasks**:
  1. Create high-resolution demo GIF and gameplay video clips showcasing telekinetic flings and Target Rush combos.
  2. Author polished `README.md` with visual badges, quickstart instructions, and troubleshooting tips.
  3. Configure GitHub Issue templates (Bug Report, Feature Request) and PR guidelines.
  4. Provide standalone executable packaging via PyInstaller for single-click desktop launch.
* **Acceptance Criteria**:
  * A new user on a clean machine can clone the repo, run `pip install -r requirements.txt`, and execute `python main.py` in under 2 minutes without errors.

---

## 3. First Playable Build Checklist (v0.1 Sprint)

For the initial prototype build (verifying core mechanics in minimal turns):

- [ ] Initialize Python virtual environment and install `opencv-python`, `mediapipe`, `pygame`, `pymunk`, `numpy`.
- [ ] Create Pygame window displaying mirrored webcam video frame as background.
- [ ] Run MediaPipe Hand Landmarker on incoming camera frames.
- [ ] Draw glowing cursor at hand anchor (midpoint between thumb base and index knuckle).
- [ ] Calculate Euclidean pinch distance; change cursor color when pinch state activates.
- [ ] Initialize Pymunk space with boundary walls and spawn 3 bouncing physics spheres.
- [ ] Attach nearest sphere to hand cursor via Pymunk spring constraint when pinched.
- [ ] Measure hand velocity vector over 5 frames and fling sphere with inertia on pinch release.
- [ ] Render velocity trail and print collision events in console.

---

## 4. Risk Matrix & Engineering Mitigations

| Risk | Likelihood | Impact | Architectural Mitigation |
| :--- | :--- | :--- | :--- |
| **Pinch Flickering** | High | High | Dual-threshold Schmitt trigger hysteresis ($\theta_{enter} \ne \theta_{exit}$) combined with a 2-frame debounce window. |
| **Tracking Latency Stutter** | Medium | High | Threaded camera worker decoupling vision ingestion from the 60 FPS Pygame render loop. |
| **Weak / Unpredictable Throws** | Medium | Medium | Rolling 5-frame moving average velocity estimator with weighted recency and outlier impulse clamping. |
| **Involuntary Drops on Occlusion** | Medium | High | $300\text{ms}$ tracking loss grace period: held object maintains current velocity/hover rather than immediately vanishing or dropping. |
| **Physics Tunneling / Explosion** | Low | High | Velocity clamping ($V_{clamp} = 2500\text{px/s}$) and Pymunk fixed sub-stepping ($dt = 1/60\text{s}$). |
| **Lighting & Camera Variance** | High | Medium | In-game visual calibration utility and contrast preprocessing. |
