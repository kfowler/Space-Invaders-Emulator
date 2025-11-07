#!/usr/bin/env python3
"""Simple random agent example for Space Invaders.

This script demonstrates basic usage of the Space Invaders Gymnasium environment
with a random agent. It's useful for testing the environment and understanding
the API.

Usage:
    uv run examples/random_agent.py
"""

import time
from typing import Any, Dict

import gymnasium as gym
import numpy as np

import space_invaders_gym  # noqa: F401 - Registers environments


def print_info(info: Dict[str, Any], reward: float, step: int) -> None:
    """Print step information."""
    print(
        f"Step {step:4d} | "
        f"Score: {info['score']:6d} | "
        f"Lives: {info['lives']} | "
        f"Level: {info['level']} | "
        f"Reward: {reward:+7.2f} | "
        f"Frames: {info['frame_count']:6d}"
    )


def main() -> None:
    """Run random agent on Space Invaders."""
    print("=" * 80)
    print("Space Invaders - Random Agent Example")
    print("=" * 80)

    # Create environment
    print("\nCreating environment...")
    env = gym.make(
        "SpaceInvaders-v0",
        obs_type="grayscale",
        action_type="discrete6",
        reward_type="score_delta",
        max_episode_steps=5000,
    )

    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")

    # Run episodes
    num_episodes = 3
    total_rewards = []

    for episode in range(num_episodes):
        print(f"\n{'='*80}")
        print(f"Episode {episode + 1}/{num_episodes}")
        print(f"{'='*80}")

        # Reset environment
        obs, info = env.reset(seed=42 + episode)
        print(f"Initial state - Lives: {info['lives']}, Score: {info['score']}")

        episode_reward = 0.0
        step = 0

        start_time = time.time()

        # Run episode
        while True:
            # Random action
            action = env.action_space.sample()

            # Step environment
            obs, reward, terminated, truncated, info = env.step(action)

            episode_reward += reward
            step += 1

            # Print info every 100 steps
            if step % 100 == 0:
                print_info(info, reward, step)

            # Check if episode is done
            if terminated or truncated:
                elapsed = time.time() - start_time
                fps = step / elapsed if elapsed > 0 else 0

                print(f"\n{'='*40}")
                print("Episode finished!")
                print(f"Reason: {'Game Over' if terminated else 'Truncated'}")
                print(f"Steps: {step}")
                print(f"Final Score: {info['score']}")
                print(f"Total Reward: {episode_reward:.2f}")
                print(f"Time: {elapsed:.2f}s")
                print(f"FPS: {fps:.1f}")
                print(f"{'='*40}\n")

                total_rewards.append(episode_reward)
                break

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Episodes: {num_episodes}")
    print(f"Mean Reward: {np.mean(total_rewards):.2f} ± {np.std(total_rewards):.2f}")
    print(f"Min Reward: {np.min(total_rewards):.2f}")
    print(f"Max Reward: {np.max(total_rewards):.2f}")
    print("=" * 80)

    env.close()


if __name__ == "__main__":
    main()
