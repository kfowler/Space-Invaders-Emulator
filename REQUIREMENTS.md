# Space Invaders Emulator - Requirements Document
## Version 1.0 - Project Completion & RL Integration

---

## 1. Executive Summary

This document specifies requirements to complete the Space Invaders Emulator and prepare it as a foundation for deep learning/reinforcement learning through self-play. The emulator will be playable by humans and trainable by ML agents using Apple's MLX framework on macOS.

### Project Goals
1. **Playability**: Fully functional Space Invaders game with authentic experience
2. **RL/DL Ready**: Gymnasium-compatible environment for MLX-based reinforcement learning
3. **Performance**: Support for headless, parallel training at high FPS (1000+ headless)
4. **Flexibility**: Configurable observation spaces, action spaces, and reward functions

---

## 2. Target Platform & Technology Stack

### 2.1 Hardware Requirements
- **Platform**: macOS on Apple Silicon (M2 Max)
- **Memory**: 64GB RAM available (support for parallel environments)
- **Processor**: Apple M2 Max (leverage Metal GPU acceleration via MLX)

### 2.2 Technology Stack
- **Core Emulator**: C (existing codebase, Intel 8080 emulation)
- **Graphics**: SDL2 (existing, for playable mode)
- **ML Framework**: MLX (Apple's framework for Apple Silicon)
- **RL Interface**: Python with Gymnasium API
- **Bindings**: Python C API / ctypes / cffi for C-Python bridge
- **Package Management**: uv (fast Python package/project manager)
- **Build System**: Make + uv for Python components

### 2.3 Distribution
- **Format**: uv-managed Python project (`uv run` capable)
- **Installation**: Single-command setup via uv
- **ROM Handling**: Instructions for obtaining ROM files legally

---

## 3. Functional Requirements

### 3.1 Core Emulator Completion (Playability)

#### 3.1.1 Build System
- **REQ-BUILD-001**: Fix Makefile SDL version mismatch (sdl-config → sdl2-config)
- **REQ-BUILD-002**: Add build target for shared library (.dylib on macOS)
- **REQ-BUILD-003**: Support headless build (no SDL dependency)
- **REQ-BUILD-004**: Integrate with uv Python project structure
- **REQ-BUILD-005**: Add compilation flags for M2 optimization (-O3, -march=native)

#### 3.1.2 Graphics & Display
- **REQ-GFX-001**: Add authentic color overlay regions (green, red, white zones)
- **REQ-GFX-002**: Display lives remaining (1P, 2P)
- **REQ-GFX-003**: Display current score (1P, 2P) and high score
- **REQ-GFX-004**: Add configurable window scaling (1x, 2x, 3x, 4x)
- **REQ-GFX-005**: Support fullscreen mode toggle
- **REQ-GFX-006**: Headless mode (no window creation, frame buffer only)

#### 3.1.3 Sound System
- **REQ-SOUND-001**: Implement sound port handlers (ports 3, 5, 6)
- **REQ-SOUND-002**: Map Space Invaders sound events:
  - UFO (repeating)
  - Shot
  - Player explosion
  - Invader explosion
  - Fleet movement (4 alternating tones)
  - UFO hit
- **REQ-SOUND-003**: Generate or obtain audio samples
- **REQ-SOUND-004**: SDL_mixer integration for audio playback
- **REQ-SOUND-005**: Audio enable/disable configuration
- **REQ-SOUND-006**: Mute option in headless mode (default)

#### 3.1.4 Input Handling
- **REQ-INPUT-001**: Support keyboard controls:
  - LEFT/RIGHT arrows: Movement
  - SPACE: Fire
  - Z: Player 1 Start
  - X: Player 2 Start
  - C: Insert Coin
  - M: Mute/unmute
  - F: Fullscreen toggle
  - ESC: Quit
- **REQ-INPUT-002**: Support gamepad/joystick input
- **REQ-INPUT-003**: Configurable key bindings (config file)
- **REQ-INPUT-004**: Programmatic input injection (for RL agent)

#### 3.1.5 Game Configuration
- **REQ-CONFIG-001**: DIP switch configuration:
  - Number of lives (3, 4, 5, 6)
  - Extra life at (1000, 1500 points)
  - Coin info display
  - Bonus life setting
- **REQ-CONFIG-002**: Difficulty selection (easy/medium/hard presets)
- **REQ-CONFIG-003**: Two-player mode support
- **REQ-CONFIG-004**: Configuration file format (JSON or TOML)

#### 3.1.6 Game State Management
- **REQ-STATE-001**: Save state functionality (full emulator snapshot)
- **REQ-STATE-002**: Load state functionality
- **REQ-STATE-003**: Multiple save slots (numbered or named)
- **REQ-STATE-004**: Quick save/load hotkeys
- **REQ-STATE-005**: State serialization format (portable binary)

#### 3.1.7 Speed Control
- **REQ-SPEED-001**: Variable emulation speed (0.25x to 10x)
- **REQ-SPEED-002**: Uncapped mode for training (max FPS)
- **REQ-SPEED-003**: Frame skip support (run N frames, render 1)
- **REQ-SPEED-004**: Target FPS configuration
- **REQ-SPEED-005**: Speed hotkeys (+/- to adjust)

#### 3.1.8 Determinism
- **REQ-DET-001**: Seedable random number generator (if any RNG exists)
- **REQ-DET-002**: Deterministic replay from seed + input sequence
- **REQ-DET-003**: Input recording to file
- **REQ-DET-004**: Replay from input file
- **REQ-DET-005**: Frame-by-frame advance mode (for debugging)

---

### 3.2 Reinforcement Learning Integration

#### 3.2.1 Python API Design
- **REQ-API-001**: Gymnasium-compatible environment class
- **REQ-API-002**: C library exposed via ctypes/cffi (or Python C extension)
- **REQ-API-003**: Environment registration with Gymnasium
- **REQ-API-004**: Support for vectorized environments (parallel instances)
- **REQ-API-005**: Thread-safe or process-safe parallelization

#### 3.2.2 Observation Space (Configurable)
- **REQ-OBS-001**: Raw pixel observation (256x224x1, grayscale)
- **REQ-OBS-002**: Downscaled pixel observation (84x84x1, DQN-style)
- **REQ-OBS-003**: Color option (RGB channels if color overlay enabled)
- **REQ-OBS-004**: RAM state observation (direct memory access)
- **REQ-OBS-005**: Structured state observation:
  - Player position (x, y)
  - Alien positions (grid)
  - Bullet positions
  - Shield states
  - Score, lives
- **REQ-OBS-006**: Frame stacking (last N frames for velocity)
- **REQ-OBS-007**: Configurable observation type via environment parameter

#### 3.2.3 Action Space (Configurable)
- **REQ-ACT-001**: Discrete action space (primary):
  - NOOP (0)
  - FIRE (1)
  - RIGHT (2)
  - LEFT (3)
  - RIGHT+FIRE (4)
  - LEFT+FIRE (5)
- **REQ-ACT-002**: Simplified action space (NOOP, LEFT, RIGHT, FIRE)
- **REQ-ACT-003**: MultiDiscrete action space ([LEFT/NOOP/RIGHT, FIRE/NOOP])
- **REQ-ACT-004**: Configurable action space type via parameter
- **REQ-ACT-005**: Frame skip per action (agent sees every Nth frame)

#### 3.2.4 Reward Function (Configurable)
- **REQ-REWARD-001**: Score delta reward (default)
- **REQ-REWARD-002**: Shaped rewards:
  - +10 per alien killed
  - +50 for UFO
  - -100 for losing a life
  - +1 per frame survived
  - -1 for wasting shots (optional)
- **REQ-REWARD-003**: Terminal reward only (final score)
- **REQ-REWARD-004**: Custom reward function callback
- **REQ-REWARD-005**: Reward normalization/scaling options

#### 3.2.5 Episode Management
- **REQ-EP-001**: Episode termination on game over
- **REQ-EP-002**: Configurable max episode length (steps/frames)
- **REQ-EP-003**: Truncation vs termination distinction
- **REQ-EP-004**: Episode reset to start
- **REQ-EP-005**: Episode reset to random saved state (curriculum learning)

#### 3.2.6 Performance & Optimization
- **REQ-PERF-001**: Achieve 1000+ FPS in headless mode (single instance)
- **REQ-PERF-002**: Support 16+ parallel environments
- **REQ-PERF-003**: Minimal memory footprint per environment
- **REQ-PERF-004**: Efficient frame buffer access (zero-copy where possible)
- **REQ-PERF-005**: MLX-compatible observation format (numpy/mlx array)

#### 3.2.7 Environment Configuration
- **REQ-ENV-001**: Environment kwargs for all configurable options
- **REQ-ENV-002**: Configuration presets (beginner, standard, expert)
- **REQ-ENV-003**: Documentation of all configuration parameters
- **REQ-ENV-004**: Validation of configuration parameters

---

## 4. Non-Functional Requirements

### 4.1 Code Quality
- **REQ-QUAL-001**: Clean, commented code following existing style
- **REQ-QUAL-002**: No memory leaks (verified with valgrind or leaks)
- **REQ-QUAL-003**: Proper error handling (no assert(0) crashes in production)
- **REQ-QUAL-004**: Type hints in all Python code
- **REQ-QUAL-005**: Docstrings for all public APIs

### 4.2 Documentation
- **REQ-DOC-001**: Updated README with:
  - Installation instructions (uv-based)
  - Usage examples (playable + RL)
  - Controls reference
  - Configuration guide
  - Troubleshooting
- **REQ-DOC-002**: API documentation for Python environment
- **REQ-DOC-003**: Example RL training script (DQN with MLX)
- **REQ-DOC-004**: Architecture documentation (how emulator works)
- **REQ-DOC-005**: ROM acquisition guide (legal sources)

### 4.3 Testing
- **REQ-TEST-001**: Emulator validation (existing test ROMs pass)
- **REQ-TEST-002**: Unit tests for new Python API
- **REQ-TEST-003**: Integration tests for RL environment
- **REQ-TEST-004**: Performance benchmarks
- **REQ-TEST-005**: Example training run to verify RL pipeline

### 4.4 Portability
- **REQ-PORT-001**: macOS-specific optimizations (Metal via MLX)
- **REQ-PORT-002**: Clean separation of platform-specific code
- **REQ-PORT-003**: Document macOS-specific dependencies

### 4.5 Usability
- **REQ-USE-001**: Single-command installation (`uv sync`)
- **REQ-USE-002**: Single-command playable mode (`uv run play`)
- **REQ-USE-003**: Single-command training example (`uv run train`)
- **REQ-USE-004**: Helpful error messages with suggestions
- **REQ-USE-005**: Progress indicators for long operations

---

## 5. Success Criteria

### 5.1 Playability
- [ ] Game runs smoothly at 60 FPS on target hardware
- [ ] All controls responsive and mapped correctly
- [ ] Sound effects play at appropriate times
- [ ] Score, lives, and high score display correctly
- [ ] Color overlays render authentically
- [ ] Save/load states work flawlessly
- [ ] Can complete a full game as a human player

### 5.2 RL/DL Readiness
- [ ] Gymnasium environment passes `env.check()` validation
- [ ] Can run 16 parallel environments at 1000+ FPS (combined)
- [ ] Simple random agent can play (doesn't crash)
- [ ] Example DQN trains and shows improvement over 1M steps
- [ ] State saving/loading enables curriculum learning
- [ ] All observation/action/reward modes work correctly
- [ ] Reproducible results with same seed

### 5.3 Developer Experience
- [ ] Installation completes in < 2 minutes
- [ ] Documentation clear enough for RL newcomer to start training
- [ ] Example code runs without modification
- [ ] Error messages guide user to solutions
- [ ] Configuration is intuitive and well-documented

---

## 6. Out of Scope (Future Enhancements)

The following are explicitly out of scope for this phase:

- Other ROM support (Galaxian, Pac-Man, etc.)
- Network multiplayer
- Leaderboard/high score sharing
- Mobile/web ports
- Custom ROM hacking tools
- Advanced debugging UI (memory viewer, disassembler GUI)
- Windows/Linux support (macOS only for now)
- Pre-trained model weights (focus on training pipeline)

---

## 7. Dependencies & Constraints

### 7.1 External Dependencies
- SDL2 (graphics, for playable mode)
- SDL_mixer (audio, for sound)
- Python 3.10+ (for MLX compatibility)
- uv package manager
- MLX framework (pip installable)
- Gymnasium (RL interface)
- NumPy (array operations)

### 7.2 Legal Constraints
- **ROM Distribution**: Cannot distribute ROM files directly
- **Licensing**: Respect original emulator's licensing (if any)
- **Trademark**: "Space Invaders" is trademarked (educational use)

### 7.3 Technical Constraints
- Must maintain compatibility with original ROM files (invaders.h/g/f/e)
- Must preserve existing 8080 CPU emulation accuracy
- C codebase must remain portable (even if optimized for macOS)

---

## 8. Assumptions

1. User has macOS on Apple Silicon (M2+ series)
2. User can legally obtain Space Invaders ROM files
3. User has basic Python/ML knowledge for RL training
4. uv package manager is acceptable (preferred over pip/conda)
5. 64GB RAM allows for extensive parallel training
6. MLX framework is stable enough for production use
7. Gymnasium API is preferred over legacy OpenAI Gym

---

## 9. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| MLX API instability | High | Low | Pin MLX version, document tested version |
| C-Python binding complexity | Medium | Medium | Start with ctypes (simple), upgrade to C extension if needed |
| SDL2 installation issues | Medium | Low | Provide homebrew installation commands |
| ROM legality concerns | Low | Low | Clear documentation on legal acquisition |
| Performance targets not met | High | Low | Profile early, optimize critical paths |
| Save state portability | Low | Medium | Use portable serialization format |

---

## 10. Timeline Estimates

*(Rough estimates, single developer)*

| Phase | Estimated Time |
|-------|----------------|
| Requirements Review | 0.5 hours |
| WBS Creation | 0.5 hours |
| Core Emulator Completion | 4-6 hours |
| Sound Implementation | 2-3 hours |
| Python C Bindings | 2-3 hours |
| Gymnasium Environment | 3-4 hours |
| Testing & Debugging | 2-3 hours |
| Documentation | 2-3 hours |
| Example Training Script | 1-2 hours |
| **Total** | **17-25 hours** |

---

## 11. Approval

This requirements document serves as the foundation for completing the Space Invaders Emulator project. Once approved, we proceed to critical review and WBS creation.

**Prepared by**: Claude (AI Assistant)
**Date**: 2025-11-07
**Version**: 1.0
**Status**: Pending Review
