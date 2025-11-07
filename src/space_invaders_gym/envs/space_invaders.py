"""Space Invaders Gymnasium Environment.

This module provides a Gymnasium-compatible environment for reinforcement learning
with the Space Invaders emulator.
"""

from typing import Any, Dict, Optional, Tuple, Callable

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from PIL import Image

from space_invaders_gym.emulator import (
    SpaceInvadersEmulator,
    BTN_COIN,
    BTN_LEFT,
    BTN_RIGHT,
    BTN_P1_FIRE,
    BTN_P1_START,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class SpaceInvadersEnv(gym.Env):
    """Space Invaders Gymnasium Environment.

    A fully-featured Gymnasium environment for the classic Space Invaders arcade game,
    optimized for reinforcement learning on Apple Silicon using MLX.

    Args:
        obs_type: Observation type - "grayscale", "rgb", "downscaled", "ram"
        action_type: Action space type - "discrete6", "discrete4", "multi_discrete"
        reward_type: Reward calculation - "score_delta", "shaped", "terminal", "custom"
        reward_fn: Custom reward function (only if reward_type="custom")
        render_mode: Rendering mode - None, "human", "rgb_array"
        max_episode_steps: Maximum steps per episode (None = unlimited)
        frame_skip: Execute action for N frames
        frame_stack: Stack last N frames for observation
        repeat_action_probability: Probability of repeating previous action (sticky actions)
        dip_switches: Tuple of 3 DIP switch values for game configuration

    Observation Spaces:
        - grayscale: Box(0, 255, (224, 256), uint8) - Full resolution grayscale
        - rgb: Box(0, 255, (224, 256, 3), uint8) - Full resolution RGB
        - downscaled: Box(0, 255, (84, 84), uint8) - Downscaled grayscale (DQN-style)
        - ram: Box(0, 255, (8192,), uint8) - Raw RAM dump

    Action Spaces:
        - discrete6: Discrete(6) - NOOP, FIRE, LEFT, RIGHT, LEFT+FIRE, RIGHT+FIRE
        - discrete4: Discrete(4) - NOOP, FIRE, LEFT, RIGHT
        - multi_discrete: MultiDiscrete([3, 2]) - [MOVE, FIRE] separately

    Reward Types:
        - score_delta: Return change in game score (default)
        - shaped: Shaped rewards for better learning
        - terminal: 0 until episode end, then final score
        - custom: User-provided reward function

    Example:
        >>> env = SpaceInvadersEnv(obs_type="downscaled", action_type="discrete6")
        >>> obs, info = env.reset(seed=42)
        >>> for _ in range(1000):
        ...     action = env.action_space.sample()
        ...     obs, reward, terminated, truncated, info = env.step(action)
        ...     if terminated or truncated:
        ...         break
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 60,
    }

    def __init__(
        self,
        obs_type: str = "grayscale",
        action_type: str = "discrete6",
        reward_type: str = "score_delta",
        reward_fn: Optional[Callable[[Dict[str, Any]], float]] = None,
        render_mode: Optional[str] = None,
        max_episode_steps: Optional[int] = None,
        frame_skip: int = 1,
        frame_stack: int = 1,
        repeat_action_probability: float = 0.0,
        dip_switches: Optional[Tuple[int, int, int]] = None,
        rom_dir: Optional[str] = None,
    ) -> None:
        """Initialize the Space Invaders environment."""
        super().__init__()

        # Configuration
        self.obs_type = obs_type
        self.action_type = action_type
        self.reward_type = reward_type
        self.reward_fn = reward_fn
        self.render_mode = render_mode
        self.max_episode_steps = max_episode_steps
        self.frame_skip = frame_skip
        self.frame_stack = frame_stack
        self.repeat_action_probability = repeat_action_probability

        # Validate configuration
        self._validate_config()

        # Initialize emulator
        self.emulator = SpaceInvadersEmulator(
            rom_dir=rom_dir, headless=(render_mode is None), dip_switches=dip_switches
        )

        # Set observation space
        self.observation_space = self._create_observation_space()

        # Set action space
        self.action_space = self._create_action_space()

        # Episode state
        self.steps = 0
        self.episode_score = 0
        self.prev_score = 0
        self.prev_lives = 3
        self.last_action = 0
        self.frame_buffer: list[np.ndarray] = []

        # RNG
        self.np_random: np.random.Generator
        self._np_random_seed: Optional[int] = None

    def _validate_config(self) -> None:
        """Validate environment configuration."""
        valid_obs_types = ["grayscale", "rgb", "downscaled", "ram"]
        if self.obs_type not in valid_obs_types:
            raise ValueError(f"Invalid obs_type: {self.obs_type}. Must be one of {valid_obs_types}")

        valid_action_types = ["discrete6", "discrete4", "multi_discrete"]
        if self.action_type not in valid_action_types:
            raise ValueError(
                f"Invalid action_type: {self.action_type}. Must be one of {valid_action_types}"
            )

        valid_reward_types = ["score_delta", "shaped", "terminal", "custom"]
        if self.reward_type not in valid_reward_types:
            raise ValueError(
                f"Invalid reward_type: {self.reward_type}. Must be one of {valid_reward_types}"
            )

        if self.reward_type == "custom" and self.reward_fn is None:
            raise ValueError("reward_fn must be provided when reward_type='custom'")

        if self.frame_skip < 1:
            raise ValueError(f"frame_skip must be >= 1, got {self.frame_skip}")

        if self.frame_stack < 1:
            raise ValueError(f"frame_stack must be >= 1, got {self.frame_stack}")

    def _create_observation_space(self) -> spaces.Space:
        """Create observation space based on obs_type."""
        if self.obs_type == "grayscale":
            base_shape = (SCREEN_HEIGHT, SCREEN_WIDTH)
        elif self.obs_type == "rgb":
            base_shape = (SCREEN_HEIGHT, SCREEN_WIDTH, 3)
        elif self.obs_type == "downscaled":
            base_shape = (84, 84)
        elif self.obs_type == "ram":
            return spaces.Box(low=0, high=255, shape=(8192,), dtype=np.uint8)

        # Apply frame stacking
        if self.frame_stack > 1:
            shape = (self.frame_stack,) + base_shape
        else:
            shape = base_shape

        return spaces.Box(low=0, high=255, shape=shape, dtype=np.uint8)

    def _create_action_space(self) -> spaces.Space:
        """Create action space based on action_type."""
        if self.action_type == "discrete6":
            # NOOP, FIRE, LEFT, RIGHT, LEFT+FIRE, RIGHT+FIRE
            return spaces.Discrete(6)
        elif self.action_type == "discrete4":
            # NOOP, FIRE, LEFT, RIGHT
            return spaces.Discrete(4)
        elif self.action_type == "multi_discrete":
            # [MOVE (left/noop/right), FIRE (no/yes)]
            return spaces.MultiDiscrete([3, 2])

        raise ValueError(f"Unknown action_type: {self.action_type}")

    def _action_to_buttons(self, action: Any) -> int:
        """Convert action to button bitfield."""
        if self.action_type == "discrete6":
            action_map = [
                0,  # NOOP
                BTN_P1_FIRE,  # FIRE
                BTN_LEFT,  # LEFT
                BTN_RIGHT,  # RIGHT
                BTN_LEFT | BTN_P1_FIRE,  # LEFT+FIRE
                BTN_RIGHT | BTN_P1_FIRE,  # RIGHT+FIRE
            ]
            return action_map[action]

        elif self.action_type == "discrete4":
            action_map = [
                0,  # NOOP
                BTN_P1_FIRE,  # FIRE
                BTN_LEFT,  # LEFT
                BTN_RIGHT,  # RIGHT
            ]
            return action_map[action]

        elif self.action_type == "multi_discrete":
            move, fire = action
            buttons = 0
            if move == 1:  # LEFT
                buttons |= BTN_LEFT
            elif move == 2:  # RIGHT
                buttons |= BTN_RIGHT
            if fire == 1:  # FIRE
                buttons |= BTN_P1_FIRE
            return buttons

        return 0

    def _get_observation(self) -> np.ndarray:
        """Get current observation from emulator."""
        self.emulator.update_framebuffer()

        if self.obs_type == "grayscale":
            frame = self.emulator.get_framebuffer_gray()
        elif self.obs_type == "rgb":
            frame = self.emulator.get_framebuffer()[:, :, :3]  # Drop alpha channel
        elif self.obs_type == "downscaled":
            frame = self.emulator.get_framebuffer_gray()
            # Downscale to 84x84 using PIL for quality
            img = Image.fromarray(frame)
            img = img.resize((84, 84), Image.BILINEAR)
            frame = np.array(img)
        elif self.obs_type == "ram":
            # TODO: Implement RAM reading
            # For now, return zeros
            return np.zeros(8192, dtype=np.uint8)

        # Frame stacking
        if self.frame_stack > 1:
            self.frame_buffer.append(frame)
            if len(self.frame_buffer) > self.frame_stack:
                self.frame_buffer.pop(0)

            # Pad with first frame if not enough frames yet
            while len(self.frame_buffer) < self.frame_stack:
                self.frame_buffer.insert(0, frame)

            return np.stack(self.frame_buffer, axis=0)

        return frame

    def _calculate_reward(self, info: Dict[str, Any]) -> float:
        """Calculate reward based on reward_type."""
        if self.reward_type == "score_delta":
            # Simple score delta
            return float(info["score_delta"])

        elif self.reward_type == "shaped":
            # Shaped rewards for better learning
            reward = 0.0

            # Score delta (main reward)
            reward += info["score_delta"]

            # Penalty for losing a life
            if info["lives_lost"] > 0:
                reward -= 100.0 * info["lives_lost"]

            # Small reward for staying alive
            reward += 0.1

            return reward

        elif self.reward_type == "terminal":
            # Only reward at episode end
            if info["terminated"]:
                return float(info["total_score"])
            return 0.0

        elif self.reward_type == "custom":
            # User-provided reward function
            assert self.reward_fn is not None
            return float(self.reward_fn(info))

        return 0.0

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment.

        Args:
            seed: Random seed for reproducibility
            options: Additional options (e.g., "state_file" to load from save state)

        Returns:
            observation: Initial observation
            info: Additional information
        """
        super().reset(seed=seed)

        # Reset emulator
        if options and "state_file" in options:
            # Load from save state (for curriculum learning)
            self.emulator.load_state(options["state_file"])
        else:
            # Normal reset
            self.emulator.reset()

        # Insert coin and start game
        self.emulator.set_input(BTN_COIN)
        self.emulator.step_frame()
        self.emulator.set_input(BTN_P1_START)
        self.emulator.step_frame()
        self.emulator.set_input(0)
        self.emulator.step_frame()

        # Reset episode state
        self.steps = 0
        self.episode_score = 0
        self.prev_score = 0
        self.prev_lives = self.emulator.get_lives()
        self.last_action = 0
        self.frame_buffer = []

        # Get initial observation
        obs = self._get_observation()

        info: Dict[str, Any] = {
            "score": 0,
            "lives": self.prev_lives,
            "level": 1,
            "frame_count": self.emulator.get_frame_count(),
        }

        return obs, info

    def step(
        self, action: Any
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one environment step.

        Args:
            action: Action to take

        Returns:
            observation: Current observation
            reward: Reward for this step
            terminated: Whether episode ended naturally (game over)
            truncated: Whether episode was truncated (max steps)
            info: Additional information
        """
        # Sticky actions (repeat previous action with some probability)
        if self.repeat_action_probability > 0 and self.np_random.random() < self.repeat_action_probability:
            action = self.last_action
        self.last_action = action

        # Convert action to buttons
        buttons = self._action_to_buttons(action)

        # Execute action for frame_skip frames
        for _ in range(self.frame_skip):
            self.emulator.set_input(buttons)
            self.emulator.step_frame()

        # Get new state
        score = self.emulator.get_score()
        lives = self.emulator.get_lives()
        game_over = self.emulator.is_game_over()
        level = self.emulator.get_level()

        # Calculate deltas
        score_delta = score - self.prev_score
        lives_lost = self.prev_lives - lives

        # Update state
        self.prev_score = score
        self.prev_lives = lives
        self.steps += 1

        # Get observation
        obs = self._get_observation()

        # Build info dict
        info: Dict[str, Any] = {
            "score": score,
            "total_score": score,
            "score_delta": score_delta,
            "lives": lives,
            "lives_lost": lives_lost,
            "level": level,
            "frame_count": self.emulator.get_frame_count(),
            "steps": self.steps,
            "terminated": game_over,
        }

        # Calculate reward
        reward = self._calculate_reward(info)

        # Check termination conditions
        terminated = game_over
        truncated = False
        if self.max_episode_steps and self.steps >= self.max_episode_steps:
            truncated = True

        return obs, reward, terminated, truncated, info

    def render(self) -> Optional[np.ndarray]:
        """Render the environment.

        Returns:
            RGB array if render_mode="rgb_array", None otherwise
        """
        if self.render_mode is None:
            return None

        self.emulator.update_framebuffer()
        frame = self.emulator.get_framebuffer()[:, :, :3]  # Drop alpha channel

        if self.render_mode == "rgb_array":
            return frame

        # For "human" mode, would need SDL rendering (not implemented in headless)
        return frame

    def close(self) -> None:
        """Clean up resources."""
        # Emulator cleanup happens in __del__
        pass

    def save_state(self, filename: str) -> None:
        """Save current emulator state to file.

        Useful for curriculum learning - save interesting states and reset to them.

        Args:
            filename: Path to save file
        """
        self.emulator.save_state(filename)

    def load_state(self, filename: str) -> None:
        """Load emulator state from file.

        Args:
            filename: Path to save file
        """
        self.emulator.load_state(filename)
