# Work Breakdown Structure (WBS)
## Space Invaders Emulator - Three-Phase Completion

**Project Manager**: Claude
**Date**: 2025-11-07
**Approach**: Three-phase development (RL MVP → Playable → Polished)

---

## Phase Overview

| Phase | Focus | Estimated Time | Key Deliverables |
|-------|-------|----------------|------------------|
| **Phase 1** | RL MVP | 12-15 hours | Headless emulator, Gymnasium API, training pipeline |
| **Phase 2** | Human Playable | 8-10 hours | Graphics polish, sound, controls, UI improvements |
| **Phase 3** | Polished | 5-7 hours | Structured observations, advanced features, docs |
| **Total** | | **25-32 hours** | Production-ready emulator + RL environment |

---

# PHASE 1: RL MVP (12-15 hours)

**Goal**: Get RL agents training as quickly as possible with headless, fast emulation.

## 1.1 Build System & Project Structure (2-3 hours)

### Task 1.1.1: Fix and Enhance Makefile
- **Specific**: Update Makefile to use sdl2-config, add shared library target
- **Measurable**: Builds complete without errors, produces .dylib
- **Achievable**: Standard Makefile changes
- **Relevant**: Required for Python bindings
- **Timely**: 30 minutes
- **Output**: Updated Makefile with targets: `sinv`, `testr`, `libspaceinvaders.dylib`, `headless`
- **Dependencies**: None
- **Priority**: P0 (blocking)

### Task 1.1.2: Create Headless Build Target
- **Specific**: Add conditional compilation for headless mode (no SDL)
- **Measurable**: Compiles without SDL dependency when `-DHEADLESS` flag set
- **Achievable**: #ifdef guards around SDL code
- **Relevant**: Critical for fast RL training
- **Timely**: 45 minutes
- **Output**: Headless binary that runs emulation without graphics
- **Dependencies**: Task 1.1.1
- **Priority**: P0 (blocking)

### Task 1.1.3: Set Up uv Python Project Structure
- **Specific**: Create pyproject.toml, src/ directory, package structure
- **Measurable**: `uv sync` installs all dependencies
- **Achievable**: Standard Python packaging
- **Relevant**: Required for uv-based workflow
- **Timely**: 45 minutes
- **Output**:
  - `pyproject.toml` with dependencies (MLX, Gymnasium, NumPy)
  - `src/space_invaders_gym/` package directory
  - `README.md` with installation instructions
- **Dependencies**: None
- **Priority**: P0 (blocking)

### Task 1.1.4: Optimize Build for M2 Max
- **Specific**: Add M2-specific compiler flags (-O3, -march=native, -flto)
- **Measurable**: Benchmark shows performance improvement
- **Achievable**: Compiler flag additions
- **Relevant**: Maximize performance for training
- **Timely**: 15 minutes
- **Output**: Updated Makefile with optimization flags
- **Dependencies**: Task 1.1.1
- **Priority**: P1

---

## 1.2 Core Emulator Enhancements (2-3 hours)

### Task 1.2.1: Implement Save/Load State System
- **Specific**: Serialize/deserialize complete emulator state (CPU + memory)
- **Measurable**: Can save state, load state, resume execution identically
- **Achievable**: Struct serialization to binary file
- **Relevant**: Critical for curriculum learning, debugging
- **Timely**: 90 minutes
- **Output**:
  - `save_state(const char *filename)` function in C
  - `load_state(const char *filename)` function in C
  - Binary format documentation
- **Dependencies**: None
- **Priority**: P0 (blocking)
- **Testing**: Save at frame N, load, verify identical execution for 100 frames

### Task 1.2.2: Implement Speed Control & Uncapped Mode
- **Specific**: Remove SDL_Delay, add configurable frame timing
- **Measurable**: Can run at 10x, 100x, or unlimited FPS
- **Achievable**: Replace fixed delay with configurable timestep
- **Relevant**: Essential for fast training
- **Timely**: 45 minutes
- **Output**:
  - `set_speed_multiplier(float multiplier)` function
  - `set_uncapped(bool uncapped)` function
  - FPS measurement/reporting
- **Dependencies**: Task 1.1.2 (headless mode)
- **Priority**: P0 (blocking)
- **Testing**: Measure FPS in headless uncapped mode (target: 1000+ FPS)

### Task 1.2.3: Add Frame Buffer Access API
- **Specific**: Expose VRAM framebuffer for reading without SDL
- **Measurable**: Can read 256x224 pixel data as array
- **Achievable**: Return pointer to screen_buf or VRAM
- **Relevant**: Required for pixel observations
- **Timely**: 30 minutes
- **Output**:
  - `get_framebuffer(uint8_t **buffer, int *width, int *height)` function
  - Returns grayscale or RGB data
- **Dependencies**: None
- **Priority**: P0 (blocking)

### Task 1.2.4: Add Programmatic Input Injection API
- **Specific**: Replace SDL keyboard polling with settable input state
- **Measurable**: Can set LEFT/RIGHT/FIRE state programmatically
- **Achievable**: Replace SDL_PollEvent with function calls
- **Relevant**: Required for RL agent control
- **Timely**: 30 minutes
- **Output**:
  - `set_input(uint8_t buttons)` function
  - Button constants: BTN_LEFT, BTN_RIGHT, BTN_FIRE, etc.
- **Dependencies**: None
- **Priority**: P0 (blocking)

### Task 1.2.5: Add Game State Query API
- **Specific**: Expose score, lives, game-over status
- **Measurable**: Can read current score, lives remaining, episode done flag
- **Achievable**: Read from known RAM locations or add tracking
- **Relevant**: Required for reward calculation and episode management
- **Timely**: 60 minutes
- **Output**:
  - `get_score()` function
  - `get_lives()` function
  - `is_game_over()` function
  - Documentation of RAM locations used
- **Dependencies**: None
- **Priority**: P0 (blocking)
- **Note**: May require reverse-engineering RAM addresses

### Task 1.2.6: Add Reset Functionality
- **Specific**: Reset emulator to initial state (power-on or from save state)
- **Measurable**: Reset returns emulator to frame 0 state
- **Achievable**: Re-initialize CPU and memory
- **Relevant**: Required for episode resets
- **Timely**: 30 minutes
- **Output**:
  - `reset_emulator()` function
  - `reset_from_state(const char *filename)` function
- **Dependencies**: Task 1.2.1 (save/load states)
- **Priority**: P0 (blocking)

---

## 1.3 C Shared Library API (1-2 hours)

### Task 1.3.1: Design C API Header
- **Specific**: Create clean C API header for Python bindings
- **Measurable**: All required functions exposed with clear signatures
- **Achievable**: Standard C header design
- **Relevant**: Interface between C emulator and Python
- **Timely**: 45 minutes
- **Output**: `space_invaders_api.h` with:
  - Initialization: `si_init()`, `si_destroy()`
  - Control: `si_reset()`, `si_step(uint8_t action)`, `si_render()`
  - State: `si_save()`, `si_load()`, `si_get_state()`
  - Observation: `si_get_framebuffer()`, `si_get_ram()`
  - Info: `si_get_score()`, `si_get_lives()`, `si_is_done()`
  - Config: `si_set_speed()`, `si_set_headless()`
- **Dependencies**: Tasks 1.2.1-1.2.6
- **Priority**: P0 (blocking)

### Task 1.3.2: Implement C API Wrapper Functions
- **Specific**: Implement all functions declared in API header
- **Measurable**: Library compiles and links successfully
- **Achievable**: Wrapper around existing emulator code
- **Relevant**: Required for Python ctypes binding
- **Timely**: 60 minutes
- **Output**: `space_invaders_api.c` implementation
- **Dependencies**: Task 1.3.1
- **Priority**: P0 (blocking)

### Task 1.3.3: Build Shared Library (.dylib)
- **Specific**: Compile emulator as shared library for macOS
- **Measurable**: libspaceinvaders.dylib loads in Python via ctypes
- **Achievable**: Standard shared library build
- **Relevant**: Required for Python binding
- **Timely**: 15 minutes
- **Output**: Build target producing `libspaceinvaders.dylib`
- **Dependencies**: Tasks 1.3.1, 1.3.2
- **Priority**: P0 (blocking)
- **Testing**: `ctypes.CDLL('libspaceinvaders.dylib')` succeeds

---

## 1.4 Python Bindings (2-3 hours)

### Task 1.4.1: Create ctypes Wrapper Module
- **Specific**: Python module wrapping C library via ctypes
- **Measurable**: Can call all C functions from Python
- **Achievable**: Standard ctypes binding
- **Relevant**: Bridge between C emulator and Gymnasium
- **Timely**: 90 minutes
- **Output**: `src/space_invaders_gym/emulator.py` with:
  - `SpaceInvadersEmulator` class
  - Methods matching C API functions
  - Proper type conversions (pointers, arrays)
  - NumPy array integration for framebuffer
- **Dependencies**: Task 1.3.3
- **Priority**: P0 (blocking)

### Task 1.4.2: Test Emulator Wrapper
- **Specific**: Verify wrapper works correctly (init, step, reset)
- **Measurable**: Can run emulator for 1000 frames from Python
- **Achievable**: Simple test script
- **Relevant**: Validate binding before Gymnasium integration
- **Timely**: 30 minutes
- **Output**: `tests/test_emulator_wrapper.py` passing
- **Dependencies**: Task 1.4.1
- **Priority**: P0 (blocking)
- **Testing**: Run game, verify score increases, reset works

---

## 1.5 Gymnasium Environment (3-4 hours)

### Task 1.5.1: Implement Base Gymnasium Environment
- **Specific**: Create `SpaceInvadersEnv(gym.Env)` class
- **Measurable**: Passes `gymnasium.utils.env_checker.check_env()`
- **Achievable**: Standard Gymnasium API implementation
- **Relevant**: Core RL interface
- **Timely**: 120 minutes
- **Output**: `src/space_invaders_gym/envs/space_invaders.py` with:
  - `__init__(config)` - configuration handling
  - `reset(seed, options)` - episode reset
  - `step(action)` - execute action, return obs/reward/done/info
  - `render()` - optional rendering
  - `close()` - cleanup
  - `observation_space` - defined space
  - `action_space` - defined space
- **Dependencies**: Task 1.4.1
- **Priority**: P0 (blocking)

### Task 1.5.2: Implement Observation Spaces
- **Specific**: Support multiple observation types (configurable)
- **Measurable**: Can switch between observation modes via config
- **Achievable**: Conditional space definition
- **Relevant**: Flexibility for different RL algorithms
- **Timely**: 60 minutes
- **Output**: Observation modes:
  - `mode='raw_pixels'`: Box(0, 255, (224, 256), uint8) - grayscale
  - `mode='rgb'`: Box(0, 255, (224, 256, 3), uint8) - if colors enabled
  - `mode='downscaled'`: Box(0, 255, (84, 84), uint8) - DQN-style
  - `mode='ram'`: Box(0, 255, (8192,), uint8) - raw RAM dump
  - Frame stacking: Stack last N frames
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

### Task 1.5.3: Implement Action Spaces
- **Specific**: Support multiple action space types (configurable)
- **Measurable**: Can switch between action modes via config
- **Achievable**: Conditional space definition
- **Relevant**: Different RL algorithms prefer different action spaces
- **Timely**: 45 minutes
- **Output**: Action modes:
  - `mode='discrete6'`: Discrete(6) - NOOP, FIRE, LEFT, RIGHT, LEFT+FIRE, RIGHT+FIRE
  - `mode='discrete4'`: Discrete(4) - NOOP, FIRE, LEFT, RIGHT
  - `mode='multi_discrete'`: MultiDiscrete([3, 2]) - [LEFT/NOOP/RIGHT, FIRE/NOOP]
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

### Task 1.5.4: Implement Reward Functions
- **Specific**: Support multiple reward calculation modes (configurable)
- **Measurable**: Can switch between reward modes via config
- **Achievable**: Conditional reward calculation
- **Relevant**: Reward shaping affects learning
- **Timely**: 45 minutes
- **Output**: Reward modes:
  - `mode='score_delta'`: Return change in score (default)
  - `mode='shaped'`: +10/alien, +50/UFO, -100/death, +1/frame
  - `mode='terminal'`: 0 until done, then final score
  - `mode='custom'`: User-provided callback function
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

### Task 1.5.5: Add Episode Management
- **Specific**: Handle episode termination, truncation, reset logic
- **Measurable**: Episodes end correctly, reset cleanly
- **Achievable**: Standard Gymnasium episode handling
- **Relevant**: Proper RL training loop
- **Timely**: 30 minutes
- **Output**:
  - Termination: Game over (lives = 0)
  - Truncation: Max steps reached (configurable)
  - Reset: Return to initial state or saved state
  - Info dict: score, lives, level, etc.
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

### Task 1.5.6: Register Environment with Gymnasium
- **Specific**: Make environment importable and creatable via `gymnasium.make()`
- **Measurable**: `gymnasium.make('SpaceInvaders-v0')` works
- **Achievable**: Standard Gymnasium registration
- **Relevant**: Standard RL workflow
- **Timely**: 15 minutes
- **Output**: `src/space_invaders_gym/__init__.py` with registration
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

---

## 1.6 Parallel Environments (1-2 hours)

### Task 1.6.1: Implement Vectorized Environment Support
- **Specific**: Support running multiple environments in parallel
- **Measurable**: Can run 16 environments simultaneously
- **Achievable**: Use Gymnasium's `AsyncVectorEnv` or `SyncVectorEnv`
- **Relevant**: Essential for fast training
- **Timely**: 60 minutes
- **Output**:
  - Wrapper for vectorized environments
  - Thread-safe or process-safe C library
  - Performance benchmarks
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)
- **Testing**: Create 16 envs, step all, verify no crashes, measure FPS

### Task 1.6.2: Optimize for Parallel Performance
- **Specific**: Profile and optimize parallel execution
- **Measurable**: Achieve 1000+ FPS aggregate across all environments
- **Achievable**: Profiling and targeted optimization
- **Relevant**: Meet performance requirements
- **Timely**: 45 minutes
- **Output**:
  - Performance profiling results
  - Optimizations applied
  - Final benchmark results
- **Dependencies**: Task 1.6.1
- **Priority**: P1
- **Testing**: Benchmark with 1, 4, 8, 16 parallel environments

---

## 1.7 Basic Testing & Validation (1-2 hours)

### Task 1.7.1: Create Unit Tests for Python API
- **Specific**: Test all environment methods
- **Measurable**: 90%+ code coverage on Python code
- **Achievable**: Standard pytest tests
- **Relevant**: Ensure correctness before training
- **Timely**: 60 minutes
- **Output**: `tests/test_environment.py` covering:
  - Environment creation
  - Reset functionality
  - Step execution
  - Observation/action/reward correctness
  - Episode termination
- **Dependencies**: Task 1.5.1
- **Priority**: P1

### Task 1.7.2: Create Integration Test
- **Specific**: Run full episode with random agent
- **Measurable**: Can complete 10 episodes without crashes
- **Achievable**: Simple test script
- **Relevant**: Validate end-to-end pipeline
- **Timely**: 30 minutes
- **Output**: `tests/test_integration.py` that:
  - Creates environment
  - Runs random agent for 10 episodes
  - Verifies no crashes, proper resets
  - Prints performance metrics
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

### Task 1.7.3: Validate Gymnasium Compatibility
- **Specific**: Run `gymnasium.utils.env_checker.check_env()`
- **Measurable**: Passes all Gymnasium validation checks
- **Achievable**: Fix any issues found
- **Relevant**: Ensure standard compliance
- **Timely**: 15 minutes
- **Output**: Environment passes all checks
- **Dependencies**: Task 1.5.1
- **Priority**: P0 (blocking)

---

## 1.8 Example RL Training Script (1-2 hours)

### Task 1.8.1: Create Simple Random Agent Example
- **Specific**: Minimal example showing environment usage
- **Measurable**: Runs and prints results
- **Achievable**: ~20 lines of code
- **Relevant**: Documentation and validation
- **Timely**: 15 minutes
- **Output**: `examples/random_agent.py`
- **Dependencies**: Task 1.5.1
- **Priority**: P1

### Task 1.8.2: Create DQN Training Script with MLX
- **Specific**: Full RL training example using MLX
- **Measurable**: Agent learns to improve score over time
- **Achievable**: Adapt standard DQN to MLX
- **Relevant**: Demonstrate full pipeline
- **Timely**: 90 minutes
- **Output**: `examples/train_dqn_mlx.py` with:
  - DQN network definition (MLX)
  - Experience replay buffer
  - Training loop
  - Logging and checkpointing
  - Hyperparameters tuned for Space Invaders
- **Dependencies**: Tasks 1.5.1, 1.6.1
- **Priority**: P1
- **Note**: May require research into MLX DQN implementation

### Task 1.8.3: Create Basic Documentation
- **Specific**: README with installation and usage
- **Measurable**: New user can follow and run examples
- **Achievable**: Markdown documentation
- **Relevant**: Usability requirement
- **Timely**: 30 minutes
- **Output**: Updated `README.md` with:
  - Installation (`uv sync`)
  - Quick start (random agent)
  - Training (DQN example)
  - Configuration options
  - Troubleshooting
- **Dependencies**: Tasks 1.8.1, 1.8.2
- **Priority**: P1

---

# PHASE 2: Human Playable (8-10 hours)

**Goal**: Make the game fun and authentic for human players.

## 2.1 Graphics Enhancements (2-3 hours)

### Task 2.1.1: Implement Color Overlays
- **Specific**: Add authentic Space Invaders color regions
- **Measurable**: Display shows red/white/green zones
- **Achievable**: Color lookup table in rendering
- **Relevant**: Authentic retro experience
- **Timely**: 45 minutes
- **Output**:
  - Color regions: Top (RED), Middle (WHITE), Bottom (GREEN)
  - Configurable (can disable for pure B&W)
- **Dependencies**: None
- **Priority**: P1

### Task 2.1.2: Add On-Screen Score Display
- **Specific**: Render score, high score, lives as text overlay
- **Measurable**: Scores display correctly during gameplay
- **Achievable**: SDL_ttf or bitmap font rendering
- **Relevant**: Essential gameplay feedback
- **Timely**: 90 minutes
- **Output**:
  - 1P/2P score display
  - High score display
  - Lives remaining (ship icons)
  - Credit display
- **Dependencies**: None
- **Priority**: P1

### Task 2.1.3: Add Window Scaling Options
- **Specific**: Support 1x, 2x, 3x, 4x window scaling
- **Measurable**: Can toggle between scales without distortion
- **Achievable**: SDL rendering with scale factor
- **Relevant**: Modern displays need larger windows
- **Timely**: 30 minutes
- **Output**: Configurable window scale, hotkeys for toggling
- **Dependencies**: None
- **Priority**: P2

### Task 2.1.4: Add Fullscreen Mode
- **Specific**: Toggle fullscreen with F key
- **Measurable**: Fullscreen works, maintains aspect ratio
- **Achievable**: SDL fullscreen API
- **Relevant**: Immersive gameplay
- **Timely**: 20 minutes
- **Output**: Fullscreen toggle (F key)
- **Dependencies**: None
- **Priority**: P2

---

## 2.2 Sound Implementation (3-4 hours)

### Task 2.2.1: Research Space Invaders Sound System
- **Specific**: Understand port 3/5/6 sound bit mappings
- **Measurable**: Document all 9 sound effects and their triggers
- **Achievable**: Reference existing emulator docs
- **Relevant**: Required for accurate implementation
- **Timely**: 45 minutes
- **Output**: Documentation of sound system architecture
- **Dependencies**: None
- **Priority**: P1

### Task 2.2.2: Obtain or Generate Audio Samples
- **Specific**: Get WAV files for all 9 sound effects
- **Measurable**: Have audio files for all effects
- **Achievable**: Download from archive.org or generate synthetically
- **Relevant**: Required for playback
- **Timely**: 60 minutes
- **Output**: WAV files in `assets/sounds/` directory:
  - ufo_loop.wav
  - shot.wav
  - player_explosion.wav
  - invader_explosion.wav
  - fleet_move_1.wav, fleet_move_2.wav, fleet_move_3.wav, fleet_move_4.wav
  - ufo_hit.wav
- **Dependencies**: None
- **Priority**: P1

### Task 2.2.3: Integrate SDL_mixer
- **Specific**: Add SDL_mixer for audio playback
- **Measurable**: Can load and play WAV files
- **Achievable**: Standard SDL_mixer usage
- **Relevant**: Audio output
- **Timely**: 30 minutes
- **Output**: SDL_mixer initialization in main loop
- **Dependencies**: None
- **Priority**: P1

### Task 2.2.4: Implement Sound Port Handlers
- **Specific**: Complete port 3, 5, 6 OUT handlers to trigger sounds
- **Measurable**: Sounds play at correct game events
- **Achievable**: Bit checking and sound triggering
- **Relevant**: Core sound functionality
- **Timely**: 90 minutes
- **Output**: Completed `spaceInvaders_portOut()` cases for ports 3, 5, 6
- **Dependencies**: Tasks 2.2.2, 2.2.3
- **Priority**: P1
- **Testing**: Play game, verify sounds match events

### Task 2.2.5: Add Audio Configuration
- **Specific**: Mute toggle, volume control
- **Measurable**: Can mute/unmute, adjust volume
- **Achievable**: SDL_mixer volume API
- **Relevant**: User preference
- **Timely**: 20 minutes
- **Output**: M key for mute, config for volume
- **Dependencies**: Task 2.2.3
- **Priority**: P2

---

## 2.3 Input & Controls (1-2 hours)

### Task 2.3.1: Enhance Keyboard Controls
- **Specific**: Add missing keys (SPACE for fire, ESC for quit, etc.)
- **Measurable**: All expected keys work
- **Achievable**: SDL key handling updates
- **Relevant**: Better user experience
- **Timely**: 30 minutes
- **Output**: Updated key mappings:
  - SPACE or UP: Fire (in addition to current system)
  - ESC: Quit
  - M: Mute
  - F: Fullscreen
  - +/-: Speed control
  - F5/F9: Quick save/load
- **Dependencies**: None
- **Priority**: P1

### Task 2.3.2: Add Gamepad Support
- **Specific**: Support standard game controllers
- **Measurable**: Xbox/PlayStation controller works
- **Achievable**: SDL_GameController API
- **Relevant**: Console-like experience
- **Timely**: 60 minutes
- **Output**: Gamepad support with standard button mapping
- **Dependencies**: None
- **Priority**: P2

### Task 2.3.3: Create Configuration File
- **Specific**: JSON/TOML config for keybindings, audio, display
- **Measurable**: Can modify config file to change settings
- **Achievable**: Config file parsing
- **Relevant**: User customization
- **Timely**: 45 minutes
- **Output**: `config.toml` with all configurable options
- **Dependencies**: None
- **Priority**: P2

---

## 2.4 Game Configuration (1-2 hours)

### Task 2.4.1: Implement DIP Switch Configuration
- **Specific**: Expose DIP switches for lives, difficulty, bonus
- **Measurable**: Can change game difficulty/lives
- **Achievable**: Modify hardcoded dip values
- **Relevant**: Game variety
- **Timely**: 45 minutes
- **Output**: Config options for:
  - Lives (3, 4, 5, 6)
  - Bonus life threshold (1000, 1500)
  - Coin info display
- **Dependencies**: Task 2.3.3 (config file)
- **Priority**: P2

### Task 2.4.2: Add Difficulty Presets
- **Specific**: Easy/Medium/Hard presets
- **Measurable**: Selecting preset changes game behavior
- **Achievable**: Preset DIP switch combinations
- **Relevant**: User convenience
- **Timely**: 15 minutes
- **Output**: Preset configurations in config file
- **Dependencies**: Task 2.4.1
- **Priority**: P2

### Task 2.4.3: Implement Two-Player Mode
- **Specific**: Enable/test two-player alternating gameplay
- **Measurable**: 2P mode works (alternating turns)
- **Achievable**: Likely already works, just test/document
- **Relevant**: Original game feature
- **Timely**: 30 minutes
- **Output**: Verified 2P mode, documented controls
- **Dependencies**: None
- **Priority**: P3 (nice to have)

---

## 2.5 UI Polish (1 hour)

### Task 2.5.1: Add Startup Screen
- **Specific**: Show controls/credits before game starts
- **Measurable**: Displays on launch, dismisses on input
- **Achievable**: Simple SDL rendering
- **Relevant**: User onboarding
- **Timely**: 30 minutes
- **Output**: Startup screen with controls reference
- **Dependencies**: None
- **Priority**: P3

### Task 2.5.2: Add Pause Functionality
- **Specific**: P key pauses game
- **Measurable**: Game pauses/resumes correctly
- **Achievable**: Halt emulation loop on flag
- **Relevant**: Quality of life
- **Timely**: 20 minutes
- **Output**: Pause toggle (P key)
- **Dependencies**: None
- **Priority**: P2

### Task 2.5.3: Improve Error Messages
- **Specific**: Replace asserts with helpful error messages
- **Measurable**: Errors guide user to solution (e.g., missing ROMs)
- **Achievable**: Error handling improvements
- **Relevant**: User experience
- **Timely**: 15 minutes
- **Output**: User-friendly error messages
- **Dependencies**: None
- **Priority**: P2

---

# PHASE 3: Polished (5-7 hours)

**Goal**: Advanced features, structured observations, comprehensive documentation.

## 3.1 Structured State Observations (2-3 hours)

### Task 3.1.1: Reverse Engineer Game State Memory Layout
- **Specific**: Find RAM locations for player, aliens, bullets, shields
- **Measurable**: Document exact memory addresses
- **Achievable**: Use IDA database + emulator inspection
- **Relevant**: Required for structured observations
- **Timely**: 90 minutes
- **Output**: Documentation of memory map:
  - Player X position
  - Alien grid state (11x5 alive/dead flags)
  - Bullet positions (player + enemy)
  - Shield damage states
  - UFO state
- **Dependencies**: None
- **Priority**: P2
- **Tools**: invaders.idb (IDA Pro database), memory viewer

### Task 3.1.2: Implement State Parsing Functions (C)
- **Specific**: C functions to extract structured state from RAM
- **Measurable**: Functions return correct values during gameplay
- **Achievable**: Read specific memory addresses
- **Relevant**: API for structured observations
- **Timely**: 60 minutes
- **Output**: C API functions:
  - `si_get_player_position()`
  - `si_get_alien_grid()`
  - `si_get_bullets()`
  - `si_get_shields()`
- **Dependencies**: Task 3.1.1
- **Priority**: P2

### Task 3.1.3: Add Structured Observation Mode
- **Specific**: New observation space with structured data
- **Measurable**: Environment returns dict observation
- **Achievable**: Add observation mode to Gymnasium env
- **Relevant**: Alternative to pixels for research
- **Timely**: 45 minutes
- **Output**: `mode='structured'` observation space:
  - Dict with keys: player_x, aliens (grid), bullets, shields, score, lives
  - Properly defined Gymnasium spaces
- **Dependencies**: Task 3.1.2
- **Priority**: P2

---

## 3.2 Advanced Features (1-2 hours)

### Task 3.2.1: Add Determinism Verification
- **Specific**: Test that emulation is deterministic
- **Measurable**: Same inputs produce identical outputs
- **Achievable**: Record/replay test
- **Relevant**: Required for reproducible research
- **Timely**: 45 minutes
- **Output**: Test that verifies determinism
- **Dependencies**: None
- **Priority**: P2

### Task 3.2.2: Add Input Recording/Replay
- **Specific**: Record input sequence to file, replay later
- **Measurable**: Can replay recorded game perfectly
- **Achievable**: Log inputs, play back on reset
- **Relevant**: Debugging and sharing gameplay
- **Timely**: 60 minutes
- **Output**:
  - `record_inputs(filename)` mode
  - `replay_inputs(filename)` mode
  - Binary input log format
- **Dependencies**: None
- **Priority**: P3

### Task 3.2.3: Add Frame-by-Frame Debug Mode
- **Specific**: Step emulator one frame at a time
- **Measurable**: Can advance single frames with key press
- **Achievable**: Pause loop with step-forward
- **Relevant**: Debugging
- **Timely**: 20 minutes
- **Output**: Debug mode with single-step (N key)
- **Dependencies**: None
- **Priority**: P3

---

## 3.3 Performance Optimization (1 hour)

### Task 3.3.1: Profile Critical Paths
- **Specific**: Identify performance bottlenecks
- **Measurable**: Profiling data collected
- **Achievable**: Use Instruments or gprof
- **Relevant**: Meet performance targets
- **Timely**: 30 minutes
- **Output**: Profiling report
- **Dependencies**: None
- **Priority**: P2

### Task 3.3.2: Optimize Hot Paths
- **Specific**: Apply optimizations to bottlenecks
- **Measurable**: FPS improves by 10%+
- **Achievable**: Targeted optimizations
- **Relevant**: Performance goals
- **Timely**: 45 minutes
- **Output**: Optimized code, benchmark results
- **Dependencies**: Task 3.3.1
- **Priority**: P2

---

## 3.4 Comprehensive Documentation (2-3 hours)

### Task 3.4.1: Write Complete API Documentation
- **Specific**: Document all Python API functions, classes, parameters
- **Measurable**: Every public API has docstring
- **Achievable**: Python docstrings + Sphinx/mkdocs
- **Relevant**: Usability for researchers
- **Timely**: 90 minutes
- **Output**: API reference documentation (HTML or PDF)
- **Dependencies**: None
- **Priority**: P1

### Task 3.4.2: Write Architecture Documentation
- **Specific**: Explain how emulator works (CPU, memory, timing, etc.)
- **Measurable**: Technical document exists
- **Achievable**: Markdown documentation
- **Relevant**: Educational value
- **Timely**: 60 minutes
- **Output**: `ARCHITECTURE.md` explaining:
  - Intel 8080 emulation
  - Memory banking
  - Space Invaders hardware
  - Timing and interrupts
  - Graphics rendering
- **Dependencies**: None
- **Priority**: P2

### Task 3.4.3: Create Advanced Training Examples
- **Specific**: Example scripts for curriculum learning, hyperparameter tuning
- **Measurable**: Examples run and demonstrate concepts
- **Achievable**: Python scripts with documentation
- **Relevant**: Research use case
- **Timely**: 45 minutes
- **Output**:
  - `examples/curriculum_learning.py`
  - `examples/hyperparameter_search.py`
  - Documentation explaining concepts
- **Dependencies**: Phase 1 complete
- **Priority**: P2

### Task 3.4.4: Create Troubleshooting Guide
- **Specific**: Common issues and solutions
- **Measurable**: Covers common user problems
- **Achievable**: FAQ-style documentation
- **Relevant**: Support/usability
- **Timely**: 30 minutes
- **Output**: `TROUBLESHOOTING.md` with:
  - Installation issues
  - ROM problems
  - Performance issues
  - macOS-specific quirks
- **Dependencies**: None
- **Priority**: P2

---

## Testing & Quality Assurance (Ongoing)

### Continuous Tasks
- **Code Review**: Review each task's code for quality
- **Testing**: Test each feature as implemented
- **Documentation**: Document as you build
- **Performance**: Benchmark after major changes

### Final Validation Checklist
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance targets met (1000+ FPS headless, 16 parallel envs)
- [ ] Gymnasium environment passes `check_env()`
- [ ] Example DQN trains successfully
- [ ] Human can play and enjoy the game
- [ ] Sound effects work correctly
- [ ] Documentation complete and clear
- [ ] No memory leaks (verified with `leaks` command)
- [ ] Code follows style guide
- [ ] All requirements met

---

## Dependency Graph

```
Phase 1 (RL MVP):
  1.1 Build System ──┬──> 1.2 Core Emulator
                     └──> 1.3 C API ──> 1.4 Python Bindings ──> 1.5 Gymnasium Env ──> 1.6 Parallel Envs
                                                                           │
                                                                           └──> 1.7 Testing
                                                                           └──> 1.8 Examples

Phase 2 (Playable):
  2.1 Graphics ──┐
  2.2 Sound     ─┼──> Complete Playable Experience
  2.3 Input     ─┤
  2.4 Config    ─┘
  2.5 UI Polish

Phase 3 (Polished):
  3.1 Structured Obs ──┐
  3.2 Advanced Features ┼──> Production Ready
  3.3 Optimization     ─┤
  3.4 Documentation    ─┘
```

---

## Risk Management

| Risk | Mitigation | Owner | Status |
|------|------------|-------|--------|
| MLX integration issues | Test early, have NumPy fallback | Dev | Not Started |
| Performance targets not met | Profile early, optimize critical paths | Dev | Not Started |
| ROM legality | Clear documentation, no distribution | Dev | Not Started |
| Save state portability | Use standard serialization | Dev | Not Started |
| Memory leaks | Use `leaks` tool, valgrind if available | Dev | Not Started |
| Sound samples unavailable | Generate synthetic or use placeholders | Dev | Not Started |

---

## Success Metrics

### Phase 1 Success Criteria:
- [ ] Can run 1000+ FPS in headless mode
- [ ] Can run 16 parallel environments
- [ ] Gymnasium environment validates successfully
- [ ] Random agent completes episodes
- [ ] DQN training shows improvement
- [ ] All P0 tasks complete

### Phase 2 Success Criteria:
- [ ] Game is enjoyable to play as human
- [ ] All sound effects work
- [ ] Graphics are authentic/appealing
- [ ] Controls are responsive
- [ ] All P1 tasks complete

### Phase 3 Success Criteria:
- [ ] Structured observations work correctly
- [ ] Documentation is comprehensive
- [ ] Advanced features functional
- [ ] All P2 tasks complete
- [ ] Production-ready quality

---

## Timeline Estimate

| Phase | Optimistic | Realistic | Pessimistic |
|-------|-----------|-----------|-------------|
| Phase 1 | 12 hours | 15 hours | 18 hours |
| Phase 2 | 8 hours | 10 hours | 12 hours |
| Phase 3 | 5 hours | 7 hours | 9 hours |
| **Total** | **25 hours** | **32 hours** | **39 hours** |

**Recommended Approach**: Allocate 35 hours with buffer for unknowns.

---

**WBS Status**: ✅ **APPROVED - READY FOR EXECUTION**

**Next Step**: Begin Phase 1 implementation starting with Task 1.1.1
