"""Low-level ctypes wrapper for the Space Invaders emulator C library."""

import ctypes
import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt

# Button constants (matching C API)
BTN_COIN = 1 << 0
BTN_P2_START = 1 << 1
BTN_P1_START = 1 << 2
BTN_P1_FIRE = 1 << 4
BTN_LEFT = 1 << 5
BTN_RIGHT = 1 << 6

# Screen dimensions
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 224


class SpaceInvadersEmulator:
    """Python wrapper for the Space Invaders C emulator library.

    This class provides a Python interface to the headless Space Invaders
    emulator, handling all ctypes bindings and memory management.

    Args:
        rom_dir: Directory containing ROM files (invaders.h/g/f/e)
        headless: If True, run in headless mode (no SDL, faster)
        dip_switches: Optional tuple of 3 DIP switch values

    Example:
        >>> emu = SpaceInvadersEmulator()
        >>> emu.reset()
        >>> for _ in range(60):
        ...     emu.step_frame()
        ...     frame = emu.get_framebuffer_gray()
    """

    def __init__(
        self,
        rom_dir: Optional[str] = None,
        headless: bool = True,
        dip_switches: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """Initialize the emulator wrapper."""
        # Find the shared library
        if rom_dir is None:
            rom_dir = Path(__file__).parent.parent.parent.absolute()
        else:
            rom_dir = Path(rom_dir).absolute()

        # Load shared library
        lib_path = rom_dir / "libspaceinvaders.dylib"
        if not lib_path.exists():
            # Try .so extension for Linux
            lib_path = rom_dir / "libspaceinvaders.so"

        if not lib_path.exists():
            raise FileNotFoundError(
                f"Could not find libspaceinvaders library in {rom_dir}. "
                "Please run 'make libspaceinvaders.dylib' first."
            )

        self.lib = ctypes.CDLL(str(lib_path))

        # Define function signatures
        self._define_functions()

        # ROM file paths
        self.rom_h = str(rom_dir / "invaders.h")
        self.rom_g = str(rom_dir / "invaders.g")
        self.rom_f = str(rom_dir / "invaders.f")
        self.rom_e = str(rom_dir / "invaders.e")

        # Verify ROM files exist
        for rom_file in [self.rom_h, self.rom_g, self.rom_f, self.rom_e]:
            if not os.path.exists(rom_file):
                raise FileNotFoundError(f"ROM file not found: {rom_file}")

        # Initialize emulator
        if headless:
            dip = dip_switches if dip_switches else (0x0E, 0x08, 0x00)
            dip_array = (ctypes.c_uint8 * 3)(*dip)
            result = self.lib.si_api_init_headless(
                self.rom_h.encode(),
                self.rom_g.encode(),
                self.rom_f.encode(),
                self.rom_e.encode(),
                dip_array,
            )
        else:
            result = self.lib.si_api_init(
                self.rom_h.encode(),
                self.rom_g.encode(),
                self.rom_f.encode(),
                self.rom_e.encode(),
            )

        if result != 0:
            raise RuntimeError(f"Failed to initialize emulator (error code: {result})")

        self._initialized = True

    def _define_functions(self) -> None:
        """Define C function signatures for ctypes."""
        lib = self.lib

        # Initialization
        lib.si_api_init.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        lib.si_api_init.restype = ctypes.c_int

        lib.si_api_init_headless.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.si_api_init_headless.restype = ctypes.c_int

        lib.si_api_destroy.argtypes = []
        lib.si_api_destroy.restype = None

        lib.si_api_reset.argtypes = []
        lib.si_api_reset.restype = None

        # Execution
        lib.si_api_step_frame.argtypes = []
        lib.si_api_step_frame.restype = ctypes.c_int

        lib.si_api_step_cycles.argtypes = [ctypes.c_int]
        lib.si_api_step_cycles.restype = ctypes.c_int

        # State management
        lib.si_api_save_state.argtypes = [ctypes.c_char_p]
        lib.si_api_save_state.restype = ctypes.c_int

        lib.si_api_load_state.argtypes = [ctypes.c_char_p]
        lib.si_api_load_state.restype = ctypes.c_int

        # Input
        lib.si_api_set_input.argtypes = [ctypes.c_uint8]
        lib.si_api_set_input.restype = None

        lib.si_api_get_input.argtypes = []
        lib.si_api_get_input.restype = ctypes.c_uint8

        # Display
        lib.si_api_update_framebuffer.argtypes = []
        lib.si_api_update_framebuffer.restype = None

        lib.si_api_get_framebuffer.argtypes = [
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        lib.si_api_get_framebuffer.restype = None

        lib.si_api_get_framebuffer_gray.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        lib.si_api_get_framebuffer_gray.restype = None

        # Game state
        lib.si_api_get_score.argtypes = []
        lib.si_api_get_score.restype = ctypes.c_uint32

        lib.si_api_get_lives.argtypes = []
        lib.si_api_get_lives.restype = ctypes.c_int

        lib.si_api_is_game_over.argtypes = []
        lib.si_api_is_game_over.restype = ctypes.c_bool

        lib.si_api_get_level.argtypes = []
        lib.si_api_get_level.restype = ctypes.c_int

        # Configuration
        lib.si_api_set_speed.argtypes = [ctypes.c_float]
        lib.si_api_set_speed.restype = None

        lib.si_api_set_uncapped.argtypes = [ctypes.c_bool]
        lib.si_api_set_uncapped.restype = None

        lib.si_api_set_dip_switches.argtypes = [
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
        ]
        lib.si_api_set_dip_switches.restype = None

        # Statistics
        lib.si_api_get_frame_count.argtypes = []
        lib.si_api_get_frame_count.restype = ctypes.c_uint32

        lib.si_api_get_cycle_count.argtypes = []
        lib.si_api_get_cycle_count.restype = ctypes.c_uint64

    def __del__(self) -> None:
        """Cleanup emulator resources."""
        if hasattr(self, "_initialized") and self._initialized:
            self.lib.si_api_destroy()

    def reset(self) -> None:
        """Reset emulator to initial state."""
        self.lib.si_api_reset()

    def step_frame(self) -> int:
        """Execute one frame of emulation.

        Returns:
            Number of CPU cycles executed
        """
        return self.lib.si_api_step_frame()

    def step_cycles(self, cycles: int) -> int:
        """Execute N CPU cycles.

        Args:
            cycles: Number of cycles to execute

        Returns:
            Number of cycles actually executed
        """
        return self.lib.si_api_step_cycles(cycles)

    def save_state(self, filename: str) -> None:
        """Save emulator state to file.

        Args:
            filename: Path to save file

        Raises:
            RuntimeError: If save fails
        """
        result = self.lib.si_api_save_state(filename.encode())
        if result != 0:
            raise RuntimeError(f"Failed to save state to {filename}")

    def load_state(self, filename: str) -> None:
        """Load emulator state from file.

        Args:
            filename: Path to save file

        Raises:
            RuntimeError: If load fails
        """
        result = self.lib.si_api_load_state(filename.encode())
        if result != 0:
            raise RuntimeError(f"Failed to load state from {filename}")

    def set_input(self, buttons: int) -> None:
        """Set input button state.

        Args:
            buttons: Bitfield of button flags (BTN_LEFT, BTN_RIGHT, etc.)
        """
        self.lib.si_api_set_input(buttons)

    def get_input(self) -> int:
        """Get current input state.

        Returns:
            Current button bitfield
        """
        return self.lib.si_api_get_input()

    def update_framebuffer(self) -> None:
        """Update framebuffer from VRAM."""
        self.lib.si_api_update_framebuffer()

    def get_framebuffer(self) -> npt.NDArray[np.uint8]:
        """Get ARGB framebuffer as numpy array.

        Returns:
            Array of shape (height, width, 4) with ARGB data
        """
        buffer_ptr = ctypes.POINTER(ctypes.c_uint8)()
        width = ctypes.c_int()
        height = ctypes.c_int()

        self.lib.si_api_get_framebuffer(
            ctypes.byref(buffer_ptr), ctypes.byref(width), ctypes.byref(height)
        )

        # Create numpy array from pointer (no copy)
        size = width.value * height.value * 4
        array = np.ctypeslib.as_array(buffer_ptr, shape=(size,))

        # Reshape to (height, width, 4)
        return array.reshape((height.value, width.value, 4))

    def get_framebuffer_gray(self) -> npt.NDArray[np.uint8]:
        """Get grayscale framebuffer as numpy array.

        Returns:
            Array of shape (height, width) with grayscale data (0-255)
        """
        size = SCREEN_WIDTH * SCREEN_HEIGHT
        buffer = np.zeros(size, dtype=np.uint8)

        self.lib.si_api_get_framebuffer_gray(
            buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        )

        return buffer.reshape((SCREEN_HEIGHT, SCREEN_WIDTH))

    def get_score(self) -> int:
        """Get current score.

        Returns:
            Current player score
        """
        return self.lib.si_api_get_score()

    def get_lives(self) -> int:
        """Get lives remaining.

        Returns:
            Number of lives
        """
        return self.lib.si_api_get_lives()

    def is_game_over(self) -> bool:
        """Check if game is over.

        Returns:
            True if game over
        """
        return self.lib.si_api_is_game_over()

    def get_level(self) -> int:
        """Get current level/wave.

        Returns:
            Current level number
        """
        return self.lib.si_api_get_level()

    def set_speed(self, multiplier: float) -> None:
        """Set speed multiplier.

        Args:
            multiplier: Speed multiplier (1.0 = normal, 0 = uncapped)
        """
        self.lib.si_api_set_speed(multiplier)

    def set_uncapped(self, uncapped: bool) -> None:
        """Enable/disable uncapped mode.

        Args:
            uncapped: If True, run as fast as possible
        """
        self.lib.si_api_set_uncapped(uncapped)

    def set_dip_switches(self, dip0: int, dip1: int, dip2: int) -> None:
        """Set DIP switch configuration.

        Args:
            dip0: DIP switch 0 value
            dip1: DIP switch 1 value
            dip2: DIP switch 2 value
        """
        self.lib.si_api_set_dip_switches(dip0, dip1, dip2)

    def get_frame_count(self) -> int:
        """Get total frames executed.

        Returns:
            Frame count
        """
        return self.lib.si_api_get_frame_count()

    def get_cycle_count(self) -> int:
        """Get total CPU cycles executed.

        Returns:
            Cycle count
        """
        return self.lib.si_api_get_cycle_count()
