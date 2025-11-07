# Space Invaders Emulator - Architecture Documentation

## Overview

This is a complete Intel 8080 CPU emulator designed specifically for the Space Invaders arcade game, with a focus on reinforcement learning research on Apple Silicon.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Python/Gymnasium Layer                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  space_invaders_gym.envs.SpaceInvadersEnv                │  │
│  │  - Gymnasium-compatible interface                         │  │
│  │  - Observation/action spaces                              │  │
│  │  - Reward shaping                                         │  │
│  │  - Frame stacking                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲                                    │
│                            │ ctypes bindings                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  space_invaders_gym.emulator.SpaceInvadersEmulator       │  │
│  │  - Python wrapper around C library                        │  │
│  │  - Memory management                                      │  │
│  │  - Type conversions                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │ C API (libspaceinvaders.dylib)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        C Emulator Core                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  space_invaders_api.c                                    │  │
│  │  - C interface layer                                      │  │
│  │  - Type-safe wrappers                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲                                    │
│                            │                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  space_invaders_core.c                                   │  │
│  │  - Hardware emulation                                     │  │
│  │  - Port I/O handlers                                      │  │
│  │  - Shift register                                         │  │
│  │  - Framebuffer management                                 │  │
│  │  - State queries                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲                                    │
│                            │                                    │
│  ┌───────────────────┬────────────────┬───────────────────┐  │
│  │   8080Core.c      │  8080Memory.c  │ 8080Opcodes.h     │  │
│  │   - CPU registers │  - Banking     │ - All 256 opcodes │  │
│  │   - Execution     │  - Read/write  │ - Flags           │  │
│  │   - Interrupts    │  - ROM/RAM     │ - Timing          │  │
│  └───────────────────┴────────────────┴───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Intel 8080 CPU Emulation

### Core Components

#### 1. CPU State (`8080Core.c`)
```c
typedef struct {
    int clock;           // Processor frequency (2MHz for Space Invaders)
    uint8_t halt;        // Halt flag

    // 8-bit registers (can be accessed as 16-bit pairs)
    union {
        struct {
            uint8_t C, B;      // BC register pair
            uint8_t E, D;      // DE register pair
            uint8_t L, H;      // HL register pair
            uint8_t F, A;      // Accumulator & Flags
        };
        struct {
            uint16_t BC, DE, HL, AF;
        };
    };

    uint16_t PC;         // Program Counter
    uint16_t SP;         // Stack Pointer
    Mem *ram;            // Memory bank linked list
    uint8_t IE;          // Interrupts enabled flag
    uint8_t iPending;    // Pending interrupt

    // Port I/O callbacks
    uint8_t (*portIn)(int port);
    void (*portOut)(int port, uint8_t value);
} e8080_t;
```

#### 2. Instruction Execution
- **Opcode Dispatch**: Jump table for all 256 opcodes
- **Cycle Accuracy**: Each instruction tracks CPU cycles
- **Timing**: 2 MHz clock (500ns per cycle)

#### 3. Flags Register
```
  7   6   5   4   3   2   1   0
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ S │ Z │ 0 │AC │ 0 │ P │ 1 │ C │
└───┴───┴───┴───┴───┴───┴───┴───┘
  │   │       │       │       └─ Carry
  │   │       │       └───────── Parity
  │   │       └───────────────── Auxiliary Carry
  │   └───────────────────────── Zero
  └───────────────────────────── Sign
```

### Memory System (`8080Memory.c`)

#### Memory Banking
The memory system uses a linked-list of memory banks to support ROM/RAM separation:

```c
typedef struct Mem {
    uint16_t start;      // Start address
    uint16_t size;       // Bank size
    uint8_t *buffer;     // Data buffer
    uint8_t readOnly;    // ROM flag
    struct Mem *next;    // Next bank
} Mem;
```

#### Memory Map
```
0x0000 ┌─────────────────┐
       │   ROM (8KB)     │  Read-only, contains game code
       │   invaders.h    │
       │   invaders.g    │
       │   invaders.f    │
       │   invaders.e    │
0x1FFF └─────────────────┘
0x2000 ┌─────────────────┐
       │  Work RAM (1KB) │  Game state variables
0x23FF └─────────────────┘
0x2400 ┌─────────────────┐
       │  VRAM (7KB)     │  Display buffer
       │  224 x 256 bits │  (rotated 90° CCW)
0x3FFF └─────────────────┘
0x4000 ┌─────────────────┐
       │  RAM Mirror     │  (unused)
0xFFFF └─────────────────┘
```

## Space Invaders Hardware (`space_invaders_core.c`)

### Hardware Components

#### 1. Display System
- **Resolution**: 256×224 pixels, monochrome
- **Rotation**: 90° counter-clockwise (tall cabinet)
- **VRAM**: Memory-mapped at 0x2400-0x3FFF
- **Framebuffer**: Converted to RGB for display/RL

```
Physical Screen         Memory Layout
┌──────────┐            ┌─────────────┐
│    ┌─┐   │            │ Bit 0 = Top │
│    │A│   │   ══>      │ Bit 7 = Bot │
│    │B│   │            │ Each byte = │
│    └─┘   │            │ 8 v-pixels  │
└──────────┘            └─────────────┘
  256 wide                224/8 = 28 bytes
  224 tall                per row
```

#### 2. Shift Register
Hardware shift register for efficient sprite operations:
- **Write**: Port 4 - shifts in 8 bits
- **Offset**: Port 2 - sets shift amount (0-7)
- **Read**: Port 3 - returns shifted result

```c
// Example: Shift register operation
shift_reg = (shift_reg >> 8) | (value << 8);  // Write
result = shift_reg >> (8 - offset);            // Read
```

#### 3. Interrupt System
Two interrupts per frame (60 Hz):
- **RST 1** (0x0008): Mid-screen interrupt (~1/120 sec)
- **RST 2** (0x0010): End-screen interrupt (~1/60 sec)

```c
// Interrupt timing
const int half_frame_cycles = 17066;  // ~1/120 second

// First half
emulate8080(half_frame_cycles);
causeInt(8);  // RST 1

// Second half
emulate8080(half_frame_cycles);
causeInt(16); // RST 2
```

#### 4. Input System
Port 1 input layout:
```
Bit 7 6 5 4 3 2 1 0
    │ │ │ │ │ │ │ └─ COIN
    │ │ │ │ │ │ └─── P2_START
    │ │ │ │ │ └───── P1_START
    │ │ │ │ └─────── Always 1
    │ │ │ └───────── P1_FIRE
    │ │ └─────────── LEFT
    │ └───────────── RIGHT
    └─────────────── (unused)
```

### Reset Sequence

The reset function must preserve critical state across resets:

```c
void si_reset(void) {
    // Save pointers that reset8080() would clear
    Mem *saved_ram = e8080.ram;
    uint8_t (*saved_portIn)(int) = e8080.portIn;
    void (*saved_portOut)(int, uint8_t) = e8080.portOut;

    reset8080(0x0001);  // Reset CPU to address 0x0001

    // Restore pointers
    e8080.ram = saved_ram;
    e8080.portIn = saved_portIn;
    e8080.portOut = saved_portOut;

    // Reset hardware state
    si_state.input_state = 0x08;
    si_state.shift_reg = 0x0000;
    // ... etc
}
```

This prevents the memory system from being destroyed during reset.

## Gymnasium Environment

### Observation Spaces

| Type | Shape | Description | Use Case |
|------|-------|-------------|----------|
| `grayscale` | (224, 256) | Full resolution, single channel | High-fidelity agents |
| `rgb` | (224, 256, 3) | Full resolution, RGB | Visual learning |
| `downscaled` | (84, 84) | DQN-standard size | Standard RL benchmarks |
| `ram` | (8192,) | Raw memory dump | Feature engineering |

With `frame_stack=4`:
- Shapes become `(4, 224, 256)`, `(4, 84, 84)`, etc.
- Provides motion information to the agent

### Action Spaces

| Type | Actions | Description |
|------|---------|-------------|
| `discrete6` | 6 | NOOP, FIRE, LEFT, RIGHT, LEFT+FIRE, RIGHT+FIRE |
| `discrete4` | 4 | NOOP, FIRE, LEFT, RIGHT |
| `multi_discrete` | [3, 2] | Movement (NOOP/LEFT/RIGHT) and Fire (NO/YES) |

### Reward Shaping

| Type | Formula | Purpose |
|------|---------|---------|
| `score_delta` | Δscore | Direct game score |
| `shaped` | Δscore - 100×lives_lost + 0.1 | Incentivize survival |
| `terminal` | final_score | Sparse rewards only |
| `custom` | user_fn(info) | Research-specific rewards |

## Performance Optimizations

### 1. Headless Mode
```c
#ifdef HEADLESS
    // No SDL, no graphics
    // 10-20x faster than rendered
#endif
```

### 2. Uncapped Speed
```c
si_set_uncapped(true);  // Remove frame rate limiting
// Achieves 1000+ FPS on M2 Max
```

### 3. Compiler Flags
```makefile
CFLAGS_OPT = -O3 -march=native -flto
# -O3: Maximum optimization
# -march=native: CPU-specific optimizations (Apple Silicon)
# -flto: Link-time optimization
```

### 4. MLX Integration
- Native Apple Silicon acceleration
- Efficient tensor operations
- Seamless NumPy interop

## Data Flow

### Training Step Flow
```
1. Python: action = policy(observation)
2. Python → C: si_api_set_input(action)
3. C: Execute 60 frames (1 game frame)
4. C: Update VRAM, game state
5. C → Python: Get observation (pixels/RAM)
6. C → Python: Get reward (score delta)
7. Python: Update policy with (s, a, r, s')
8. Repeat
```

### State Management
```
┌──────────────┐
│ Python Reset │
└──────┬───────┘
       │
       ▼
┌──────────────────┐      ┌─────────────────┐
│ C: si_reset()    │ ───> │ Clear RAM       │
│ Boot ROM (120f)  │      │ Reset registers │
└──────┬───────────┘      │ Restore pointers│
       │                  └─────────────────┘
       ▼
┌──────────────────┐
│ Insert Coin (30f)│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Press Start (30f)│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Wait Init (10f)  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Game Running!    │
│ Lives: 3         │
│ Score: 0         │
└──────────────────┘
```

## File Structure

```
Space-Invaders-Emulator/
├── src/
│   ├── 8080Core.c/h          # CPU core
│   ├── 8080Memory.c/h        # Memory system
│   ├── 8080Opcodes.h         # All opcodes
│   ├── space_invaders_core.c/h    # Hardware emulation
│   ├── space_invaders_api.c/h     # C API
│   └── space_invaders_gym/        # Python package
│       ├── __init__.py
│       ├── emulator.py            # ctypes wrapper
│       └── envs/
│           └── space_invaders.py  # Gymnasium env
├── examples/
│   ├── random_agent.py            # Simple demo
│   ├── train_dqn_mlx.py          # DQN training
│   └── curriculum_learning.py     # Curriculum demo
├── tests/
│   └── test_integration.py       # Integration tests
├── docs/
│   ├── RAM_MAP.md                # Memory map
│   ├── ARCHITECTURE.md           # This file
│   └── TROUBLESHOOTING.md        # Common issues
├── Makefile                      # Build system
├── pyproject.toml               # Python package
└── README.md                    # Main docs
```

## Key Design Decisions

### 1. Why C Core + Python Wrapper?
- **Performance**: C achieves 1000+ FPS vs ~60 FPS in pure Python
- **Accuracy**: Low-level control for cycle-accurate emulation
- **Flexibility**: Python wrapper enables easy RL integration

### 2. Why Memory Banking?
- Separates ROM (read-only) from RAM (writable)
- Efficient for different memory regions
- Supports memory-mapped I/O

### 3. Why Headless Mode?
- RL training doesn't need graphics
- 10-20x performance improvement
- Enables massive parallel training

### 4. Why MLX Focus?
- Native Apple Silicon support
- Competitive with CUDA on M-series chips
- Simplified deployment (no external dependencies)

## References

- [Intel 8080 Programmer's Manual](http://www.emulator101.com/reference/8080-by-opcode.html)
- [Space Invaders Hardware](http://www.computerarcheology.com/Arcade/SpaceInvaders/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [MLX Documentation](https://ml-explore.github.io/mlx/)

## Changelog

- 2025-11-07: Initial architecture documentation for Phase 3
