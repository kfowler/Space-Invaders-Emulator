#!/usr/bin/env python3
"""
Curriculum learning example for Space Invaders.

Demonstrates how to use save states to create a curriculum:
1. Train on easier scenarios (fewer aliens)
2. Gradually increase difficulty
3. Use save states to skip early game phases

Usage:
    uv run examples/curriculum_learning.py
"""

import gymnasium as gym
import numpy as np

import space_invaders_gym  # noqa: F401


def create_curriculum_states():
    """Create save states at different difficulty levels.

    This function plays the game to reach different states and saves them:
    - Level 1: Full alien grid (hardest - start of game)
    - Level 2: Half aliens defeated (medium)
    - Level 3: Only a few aliens left (easiest)

    Returns:
        List of (state_file, difficulty_name) tuples
    """
    env = gym.make("SpaceInvaders-v0", max_episode_steps=10000)

    states = []

    # State 1: Game start (full grid)
    obs, info = env.reset()
    env.unwrapped.save_state("curriculum_level1_full_grid.state")
    states.append(("curriculum_level1_full_grid.state", "Full Grid (55 aliens)"))
    print(f"✓ Saved Level 1: Full grid - {info['lives']} lives, {info['score']} score")

    # State 2: Play until half aliens defeated
    print("\nPlaying to create Level 2 (half aliens)...")

    for step in range(5000):
        action = env.action_space.sample()  # Random for demo
        obs, reward, terminated, truncated, info = env.step(action)

        # Check alien count (we'd need to add this to the API)
        # For now, use score as proxy: ~15 points avg per alien
        if info["score"] >= 400:  # Approximately 27 aliens defeated
            env.unwrapped.save_state("curriculum_level2_half_aliens.state")
            states.append(("curriculum_level2_half_aliens.state", "Half Grid (27 aliens)"))
            print(f"✓ Saved Level 2: Half aliens - {info['lives']} lives, {info['score']} score")
            break

        if terminated or truncated:
            print("  Game over before reaching Level 2, using what we have")
            break

    # State 3: Play until few aliens left
    print("\nPlaying to create Level 3 (few aliens)...")
    for step in range(5000):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        if info["score"] >= 800:  # Approximately 50 aliens defeated
            env.unwrapped.save_state("curriculum_level3_few_aliens.state")
            states.append(("curriculum_level3_few_aliens.state", "Few aliens (5 aliens)"))
            print(f"✓ Saved Level 3: Few aliens - {info['lives']} lives, {info['score']} score")
            break

        if terminated or truncated:
            print("  Game over before reaching Level 3, using what we have")
            break

    env.close()
    return states


def train_with_curriculum(states: list, steps_per_level: int = 1000):
    """Train agent using curriculum learning.

    Start with easiest state, gradually move to harder states.

    Args:
        states: List of (state_file, description) tuples
        steps_per_level: Number of steps to train on each level
    """
    print("\n" + "=" * 80)
    print("Curriculum Learning Training")
    print("=" * 80)

    env = gym.make("SpaceInvaders-v0", max_episode_steps=5000)

    # Train in reverse order (easiest to hardest)
    for level, (state_file, description) in enumerate(reversed(states), 1):
        print(f"\n--- Curriculum Level {level}/{len(states)}: {description} ---")

        level_rewards = []

        for episode in range(3):  # 3 episodes per level for demo
            # Reset to this curriculum state
            obs, info = env.reset(options={"state_file": state_file})

            episode_reward = 0
            steps = 0

            for _ in range(steps_per_level):
                # In real training, this would be your agent's action
                action = env.action_space.sample()

                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                steps += 1

                if terminated or truncated:
                    break

            level_rewards.append(episode_reward)
            print(
                f"  Episode {episode+1}: {episode_reward:6.0f} reward, "
                f"{steps:4d} steps, "
                f"{info['score']:4d} score, "
                f"{info['lives']} lives"
            )

        avg_reward = np.mean(level_rewards)
        print(f"  Average reward: {avg_reward:.1f}")

        # In real training, you would check if performance threshold is met
        # before moving to next (harder) level

    env.close()

    print("\n" + "=" * 80)
    print("Curriculum training complete!")
    print("=" * 80)
    print("\nKey benefits of curriculum learning:")
    print("  1. Faster initial learning (easier states)")
    print("  2. More stable training (gradual difficulty increase)")
    print("  3. Better exploration (focused scenarios)")
    print("  4. Can skip boring early game phases")


def demonstrate_state_loading():
    """Quick demo of save/load functionality."""
    print("\n" + "=" * 80)
    print("Save/Load State Demo")
    print("=" * 80)

    env = gym.make("SpaceInvaders-v0")

    # Save initial state
    print("\n1. Creating initial state...")
    obs, info = env.reset()
    env.unwrapped.save_state("demo_state.state")
    print(f"   Saved: Lives={info['lives']}, Score={info['score']}")

    # Play for a bit
    print("\n2. Playing 100 steps...")
    for _ in range(100):
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        if terminated or truncated:
            break
    print(f"   After play: Lives={info['lives']}, Score={info['score']}")

    # Load back to initial state
    print("\n3. Loading saved state...")
    obs, info = env.reset(options={"state_file": "demo_state.state"})
    print(f"   Restored: Lives={info['lives']}, Score={info['score']}")

    env.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Space Invaders Curriculum Learning Example")
    print("=" * 80)

    # Demonstrate save/load
    demonstrate_state_loading()

    # Create curriculum states
    print("\n" + "=" * 80)
    print("Creating Curriculum States")
    print("=" * 80)
    states = create_curriculum_states()

    # Train with curriculum
    if states:
        train_with_curriculum(states)
    else:
        print("\nNo curriculum states created (game ended too early)")

    print("\nDone!")
