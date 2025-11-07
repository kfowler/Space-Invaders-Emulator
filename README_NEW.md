# Space Invaders Emulator + Gymnasium RL Environment

A complete Intel 8080 emulator for the classic Space Invaders arcade game, with a full-featured Gymnasium environment optimized for reinforcement learning on Apple Silicon using MLX.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)

## Features

### Emulation
- ✅ Complete Intel 8080 CPU emulation (all 256 opcodes)
- ✅ Accurate Space Invaders hardware emulation
- ✅ Save/load states for curriculum learning
- ✅ Configurable speed (1x to uncapped for training)
- ✅ Headless mode for maximum performance (1000+ FPS)

### Reinforcement Learning
- ✅ Gymnasium-compatible environment
- ✅ Multiple observation spaces (grayscale, downscaled, RGB, RAM)
- ✅ Multiple action spaces (discrete, multi-discrete)
- ✅ Customizable reward functions
- ✅ Frame stacking support
- ✅ Parallel environment support
- ✅ Optimized for Apple Silicon (M1/M2/M3)
- ✅ MLX framework integration ready

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/kfowler/Space-Invaders-Emulator.git
cd Space-Invaders-Emulator

# Build C library
make libspaceinvaders.dylib

# Install Python package with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Basic Usage

```python
import gymnasium as gym
import space_invaders_gym

# Create environment
env = gym.make('SpaceInvaders-v0')

# Run episode
obs, info = env.reset()
for _ in range(1000):
    action = env.action_space.sample()  # Replace with your agent
    obs, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

### Run Examples

```bash
# Random agent
uv run examples/random_agent.py

# Run tests
uv run pytest tests/

# Train DQN agent (coming in Phase 2)
uv run examples/train_dqn_mlx.py
```

## Environment Configuration

The environment is highly configurable to support different RL research needs:

```python
env = gym.make(
    'SpaceInvaders-v0',
    obs_type='downscaled',          # grayscale, rgb, downscaled, ram
    action_type='discrete6',         # discrete6, discrete4, multi_discrete
    reward_type='shaped',            # score_delta, shaped, terminal, custom
    max_episode_steps=10000,         # Maximum steps per episode
    frame_skip=4,                    # Execute action for N frames
    frame_stack=4,                   # Stack last N frames
    repeat_action_probability=0.25,  # Sticky actions (like ALE)
)
```

### Observation Spaces

| Type | Shape | Description |
|------|-------|-------------|
| `grayscale` | (224, 256) | Full resolution grayscale |
| `rgb` | (224, 256, 3) | Full resolution RGB |
| `downscaled` | (84, 84) | Downscaled grayscale (DQN-style) |
| `ram` | (8192,) | Raw RAM dump |

With `frame_stack=4`, shapes become `(4, 224, 256)`, `(4, 84, 84)`, etc.

### Action Spaces

| Type | Actions | Description |
|------|---------|-------------|
| `discrete6` | 6 actions | NOOP, FIRE, LEFT, RIGHT, LEFT+FIRE, RIGHT+FIRE |
| `discrete4` | 4 actions | NOOP, FIRE, LEFT, RIGHT |
| `multi_discrete` | [3, 2] | Movement and fire separately |

### Reward Functions

| Type | Description |
|------|-------------|
| `score_delta` | Change in game score (default) |
| `shaped` | Shaped rewards: +score, -100/life, +0.1/frame |
| `terminal` | Only reward at episode end (final score) |
| `custom` | User-provided reward function |

## Advanced Features

### Save/Load States (Curriculum Learning)

```python
env = gym.make('SpaceInvaders-v0')
obs, info = env.reset()

# Play until interesting state
for _ in range(1000):
    obs, reward, terminated, truncated, info = env.step(action)

# Save current state
env.unwrapped.save_state('checkpoint_level2.state')

# Later, reset to that state
obs, info = env.reset(options={'state_file': 'checkpoint_level2.state'})
```

### Parallel Environments

```python
from gymnasium.vector import AsyncVectorEnv

# Create 16 parallel environments
envs = AsyncVectorEnv([
    lambda: gym.make('SpaceInvaders-v0')
    for _ in range(16)
])

obs = envs.reset()
for _ in range(1000):
    actions = envs.action_space.sample()
    obs, rewards, dones, truncated, infos = envs.step(actions)
```

### Custom Reward Function

```python
def my_reward_fn(info):
    reward = info['score_delta']

    # Extra reward for clearing rows
    if info['score_delta'] >= 50:  # UFO or many aliens
        reward += 10

    # Penalty for death
    if info['lives_lost'] > 0:
        reward -= 200

    return reward

env = gym.make(
    'SpaceInvaders-v0',
    reward_type='custom',
    reward_fn=my_reward_fn
)
```

## Performance

On Apple M2 Max:

| Mode | FPS | Use Case |
|------|-----|----------|
| Headless (single) | 1000+ | Fast training |
| Headless (16 parallel) | 800+ | Maximum throughput |
| With rendering | 60 | Human playability |

## Project Structure

```
Space-Invaders-Emulator/
├── src/
│   ├── 8080Core.c/h           # Intel 8080 CPU emulation
│   ├── 8080Memory.c/h         # Memory management
│   ├── space_invaders_core.c/h # Core emulator logic
│   ├── space_invaders_api.c/h  # C API for Python
│   └── space_invaders_gym/     # Python package
│       ├── emulator.py         # ctypes wrapper
│       └── envs/
│           └── space_invaders.py  # Gymnasium environment
├── examples/
│   ├── random_agent.py         # Simple random agent
│   └── train_dqn_mlx.py        # DQN training (Phase 2)
├── tests/
│   └── test_integration.py    # Integration tests
├── invaders.{h,g,f,e}          # ROM files (not included)
├── Makefile                    # Build configuration
└── pyproject.toml              # Python package config
```

## ROM Files

You'll need the original Space Invaders ROM files:
- `invaders.h` (2KB)
- `invaders.g` (2KB)
- `invaders.f` (2KB)
- `invaders.e` (2KB)

These are copyrighted and not included. You must obtain them legally.

Common CRC32 checksums:
```
invaders.h: 0x734f5ad8
invaders.g: 0x6bfaca4a
invaders.f: 0x0ccead96
invaders.e: 0x14e538b0
```

## Development

### Building

```bash
# Build everything
make

# Build only library
make libspaceinvaders.dylib

# Build playable version (requires SDL2)
make sinv

# Clean
make clean
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=space_invaders_gym

# Run integration tests only
uv run pytest tests/test_integration.py -v
```

### Code Quality

```bash
# Format code
uv run black src/ examples/ tests/

# Lint
uv run ruff check src/ examples/ tests/

# Type check
uv run mypy src/
```

## Roadmap

### Phase 1: RL MVP ✅ (Complete)
- [x] Core emulator with save/load states
- [x] Speed control and headless mode
- [x] C API and Python bindings
- [x] Gymnasium environment
- [x] Multiple observation/action spaces
- [x] Frame stacking and sticky actions
- [x] Integration tests
- [x] Example random agent

### Phase 2: Human Playable (In Progress)
- [ ] Color overlays (red/white/green zones)
- [ ] Score and lives display
- [ ] Sound implementation (9 effects)
- [ ] Gamepad support
- [ ] Configuration file
- [ ] Fullscreen mode

### Phase 3: Polished
- [ ] Structured state observations
- [ ] RAM address documentation
- [ ] Performance optimizations
- [ ] Comprehensive documentation
- [ ] DQN training example with MLX
- [ ] Curriculum learning examples

## Technical Details

### Intel 8080 Emulation

The emulator implements a complete Intel 8080 CPU:
- All 256 opcodes implemented
- Cycle-accurate timing
- Interrupt support (RST 1 @ mid-screen, RST 2 @ end-screen)
- Passes `8080EXM.COM` test suite

### Space Invaders Hardware

- **Display**: 256x224 monochrome, rotated 90° CCW
- **VRAM**: Memory-mapped at 0x2400-0x4000
- **Shift Register**: 16-bit hardware shift register (ports 2, 4)
- **Interrupts**: 60 Hz (mid-frame and end-frame)
- **Input**: DIP switches and controls via ports 0, 1, 2
- **Clock**: 2 MHz

## License

This project contains code from:
- Original emulator by The Lemon Man (lem0nboy) - 2010
- Enhancements and RL integration - 2025

The emulator is for educational purposes. Space Invaders is a trademark of Taito Corporation.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Acknowledgments

- **The Lemon Man (lem0nboy)**: Original emulator implementation
- **Intel**: 8080 CPU documentation
- **Emutalk forums**: Technical documentation
- **#hackerchannel on Freenode**: Support and advice
- **OpenAI**: Gymnasium framework
- **Apple**: MLX framework for Apple Silicon

## References

- [Intel 8080 Programmer's Manual](http://www.emulator101.com/reference/8080-by-opcode.html)
- [Space Invaders Hardware](http://www.computerarcheology.com/Arcade/SpaceInvaders/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [MLX Documentation](https://ml-explore.github.io/mlx/)

---

**Note**: This project is in active development. Phase 1 (RL MVP) is complete.
Phase 2 (Human Playable) and Phase 3 (Polished) are coming soon.

For questions or issues, please open a GitHub issue.
