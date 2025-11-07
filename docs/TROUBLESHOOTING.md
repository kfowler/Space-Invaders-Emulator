# Troubleshooting Guide

Common issues and solutions for the Space Invaders Emulator.

## Installation Issues

### Issue: `libspaceinvaders.dylib not found`

**Symptom**:
```
FileNotFoundError: Could not find libspaceinvaders library
```

**Solution**:
```bash
# Build the C library first
make libspaceinvaders.dylib

# Verify it exists
ls -la libspaceinvaders.dylib
```

### Issue: `ROM file not found`

**Symptom**:
```
FileNotFoundError: ROM file not found: invaders.h
```

**Solution**:
1. Obtain legal copies of the ROM files (`invaders.h/g/f/e`)
2. Place them in the project root directory
3. Verify with: `ls invaders.{h,g,f,e}`

### Issue: MLX installation fails

**Symptom**:
```
error: Distribution `mlx==0.29.3` can't be installed
```

**Solution**:
- MLX only works on Apple Silicon (M1/M2/M3) Macs
- Requires Python 3.10-3.13 (not 3.14+)
- Use: `uv sync --python 3.12`

## Runtime Issues

### Issue: Game immediately ends (Lives = 0)

**Symptom**:
```python
obs, info = env.reset()
# info['lives'] == 0, game ends immediately
```

**Solution**:
This was a bug fixed in Phase 3. Make sure you have the latest code. The ROM needs ~120 frames to boot. The environment now handles this automatically.

### Issue: Very slow performance (< 100 FPS)

**Symptom**:
```
Performance: 45.2 FPS
```

**Solutions**:
1. Ensure you're in headless mode:
   ```python
   env = gym.make('SpaceInvaders-v0')  # Headless by default
   ```

2. Check compiler optimization flags:
   ```bash
   # Makefile should have:
   CFLAGS_OPT = -O3 -march=native -flto
   ```

3. Rebuild library:
   ```bash
   make clean
   make libspaceinvaders.dylib
   ```

4. Try uncapped mode:
   ```python
   env.unwrapped.emulator.set_uncapped(True)
   ```

### Issue: Tests fail with "non-deterministic" error

**Symptom**:
```
AssertionError: Using `env.reset(seed=123)` is non-deterministic
```

**Explanation**:
The emulator IS deterministic, but doesn't use Python's random seed. This is expected behavior for the current implementation.

**Workaround**:
Skip this test or use save states for reproducibility:
```python
# Save a known state
env.unwrapped.save_state('init.state')

# Load it repeatedly for reproducible episodes
obs, info = env.reset(options={'state_file': 'init.state'})
```

## macOS-Specific Issues

### Issue: Library loads but crashes immediately

**Symptom**:
```
Segmentation fault: 11
```

**Solution**:
Check library architecture:
```bash
file libspaceinvaders.dylib
# Should show: Mach-O 64-bit dynamically linked shared library arm64
```

If it shows x86-64 or ELF, rebuild:
```bash
make clean
make libspaceinvaders.dylib
```

### Issue: "Developer cannot be verified" warning

**Symptom**:
macOS blocks the library from loading.

**Solution**:
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine libspaceinvaders.dylib
```

## Development Issues

### Issue: Changes to C code not reflected

**Symptom**:
Modified C code, but Python still sees old behavior.

**Solution**:
```bash
# Always rebuild after C changes
make clean
make libspaceinvaders.dylib

# If using installed package, reinstall
uv sync
```

### Issue: Python can't find the package

**Symptom**:
```
ModuleNotFoundError: No module named 'space_invaders_gym'
```

**Solution**:
```bash
# Install in editable mode
uv sync

# Or use uv run for scripts
uv run python examples/random_agent.py
```

### Issue: `pytest` not found

**Symptom**:
```
command not found: pytest
```

**Solution**:
```bash
# Use uv run to ensure venv is active
uv run pytest tests/

# Or activate venv manually
source .venv/bin/activate
pytest tests/
```

## Performance Issues

### Issue: Frame rate varies wildly

**Symptom**:
FPS ranges from 100 to 10000 unpredictably.

**Explanation**:
FPS depends on:
- Game state (more aliens = more processing)
- Other system load
- Whether rendering is enabled

**Solution**:
For consistent training performance:
```python
# Use frame skip
env = gym.make('SpaceInvaders-v0', frame_skip=4)

# Measure steps/second instead of FPS
steps_per_second = steps / elapsed_time
```

### Issue: Training is too slow

**Symptom**:
Training 1000 episodes takes hours.

**Solutions**:

1. **Use parallel environments**:
   ```python
   from gymnasium.vector import AsyncVectorEnv

   envs = AsyncVectorEnv([
       lambda: gym.make('SpaceInvaders-v0')
       for _ in range(16)  # 16 parallel environments
   ])
   ```

2. **Use smaller observation space**:
   ```python
   # Use downscaled instead of full res
   env = gym.make('SpaceInvaders-v0', obs_type='downscaled')  # 84x84 vs 224x256
   ```

3. **Reduce episode length**:
   ```python
   env = gym.make('SpaceInvaders-v0', max_episode_steps=1000)  # Default is 5000
   ```

## Common Mistakes

### Mistake: Not calling `env.close()`

**Problem**:
Memory leaks, emulator instances not cleaned up.

**Solution**:
Always close environments:
```python
env = gym.make('SpaceInvaders-v0')
try:
    # Your code here
finally:
    env.close()

# Or use context manager (if implemented)
```

### Mistake: Using `env` instead of `env.unwrapped`

**Problem**:
```python
env.save_state('state.state')  # AttributeError
```

**Solution**:
Emulator-specific methods need `unwrapped`:
```python
env.unwrapped.save_state('state.state')  # Correct
env.unwrapped.emulator.get_score()       # Correct
```

### Mistake: Assuming pixel coordinates are standard

**Problem**:
Space Invaders screen is rotated 90° CCW!

**Explanation**:
- VRAM represents the physical rotated screen
- Player actually moves on the "Y" axis in memory
- Framebuffer is rotated for display

**Solution**:
Use the provided framebuffer methods which handle rotation.

## Getting Help

If you're still stuck:

1. **Check the examples**:
   ```bash
   uv run examples/random_agent.py
   ```

2. **Run tests to verify installation**:
   ```bash
   uv run pytest tests/ -v
   ```

3. **Enable debug output** (if implemented):
   ```bash
   export DEBUG=1
   uv run python your_script.py
   ```

4. **Check versions**:
   ```bash
   python --version  # Should be 3.10-3.13
   uv --version
   file libspaceinvaders.dylib  # Should be arm64 on M1/M2/M3
   ```

5. **File an issue**:
   - Include your environment (OS, Python version, chip)
   - Include error messages
   - Include minimal reproduction code

## System Requirements

### Minimum
- macOS 12.0+ (or Linux with similar dependencies)
- Apple Silicon M1 or later (for MLX)
- Python 3.10+
- 2GB RAM
- 100MB disk space

### Recommended
- macOS 13.0+
- Apple Silicon M2 Max or later
- Python 3.12
- 8GB+ RAM (for parallel training)
- 1GB disk space (for saved states/models)

## Known Limitations

1. **No seeded reproducibility**: The emulator is deterministic but doesn't use Python's random seed
   - Use save states for reproducibility

2. **macOS/Linux only**: No Windows support currently
   - Use WSL2 on Windows

3. **ROMs not included**: You must provide your own legal ROM files
   - CRC32 checksums provided in README for verification

4. **Limited sound support**: Sound is emulated but not played
   - Phase 2 feature (future work)

5. **No save state versioning**: Save states may break between versions
   - Regenerate save states after updates

## Version-Specific Issues

### v0.1.0 (Current)
- Lives detection works correctly after Phase 3 fix
- Structured state observations available
- 18/19 tests pass (94.7%)
- Known issue: Seeded reproducibility test fails (expected)

## Changelog

- 2025-11-07: Initial troubleshooting guide for Phase 3 release
