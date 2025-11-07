"""Space Invaders Gymnasium Environment.

This package provides a Gymnasium-compatible environment for the classic
Space Invaders arcade game, optimized for reinforcement learning on Apple Silicon
using the MLX framework.

The environment supports:
- Multiple observation spaces (raw pixels, downscaled, grayscale, RAM)
- Configurable action spaces (discrete, multi-discrete)
- Customizable reward functions
- Save/load states for curriculum learning
- Parallel environments for fast training
- Headless mode for maximum performance

Example usage:
    >>> import gymnasium as gym
    >>> import space_invaders_gym
    >>>
    >>> # Create environment
    >>> env = gym.make('SpaceInvaders-v0')
    >>> obs, info = env.reset()
    >>>
    >>> # Run episode
    >>> for _ in range(1000):
    ...     action = env.action_space.sample()
    ...     obs, reward, terminated, truncated, info = env.step(action)
    ...     if terminated or truncated:
    ...         obs, info = env.reset()
"""

from gymnasium.envs.registration import register

from space_invaders_gym.envs.space_invaders import SpaceInvadersEnv

__version__ = "0.1.0"
__all__ = ["SpaceInvadersEnv"]

# Register environment with Gymnasium
register(
    id="SpaceInvaders-v0",
    entry_point="space_invaders_gym.envs:SpaceInvadersEnv",
    max_episode_steps=10000,
    reward_threshold=1000.0,
    kwargs={
        "obs_type": "grayscale",
        "action_type": "discrete6",
        "reward_type": "score_delta",
        "render_mode": None,
    },
)

# Downscaled version (84x84) like DQN
register(
    id="SpaceInvaders-v0-small",
    entry_point="space_invaders_gym.envs:SpaceInvadersEnv",
    max_episode_steps=10000,
    reward_threshold=1000.0,
    kwargs={
        "obs_type": "downscaled",
        "action_type": "discrete6",
        "reward_type": "score_delta",
        "render_mode": None,
    },
)

# RAM observation version for feature-based learning
register(
    id="SpaceInvaders-v0-ram",
    entry_point="space_invaders_gym.envs:SpaceInvadersEnv",
    max_episode_steps=10000,
    reward_threshold=1000.0,
    kwargs={
        "obs_type": "ram",
        "action_type": "discrete6",
        "reward_type": "score_delta",
        "render_mode": None,
    },
)

# Shaped reward version for easier learning
register(
    id="SpaceInvaders-v0-shaped",
    entry_point="space_invaders_gym.envs:SpaceInvadersEnv",
    max_episode_steps=10000,
    reward_threshold=1000.0,
    kwargs={
        "obs_type": "grayscale",
        "action_type": "discrete6",
        "reward_type": "shaped",
        "render_mode": None,
    },
)
