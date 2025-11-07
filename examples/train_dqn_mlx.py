#!/usr/bin/env python3
"""
Simple DQN training example for Space Invaders using MLX on Apple Silicon.

This demonstrates a basic DQN implementation optimized for M1/M2/M3 Macs.
For production training, consider using more advanced algorithms (Rainbow DQN, PPO, etc.)

Usage:
    uv run examples/train_dqn_mlx.py

Requirements:
    - MLX framework (Apple Silicon only)
    - Gymnasium
    - space-invaders-gym
"""

import time
from collections import deque

import gymnasium as gym
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np

import space_invaders_gym  # noqa: F401


class DQN(nn.Module):
    """Simple DQN network for Space Invaders.

    Architecture:
    - Conv layers to process 84x84 grayscale frames
    - Fully connected layers
    - Output: Q-values for each action
    """

    def __init__(self, num_actions: int = 6):
        super().__init__()
        self.conv1 = nn.Conv2d(4, 32, kernel_size=8, stride=4)  # 4 stacked frames
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        self.fc1 = nn.Linear(3136, 512)  # 64 * 7 * 7 = 3136
        self.fc2 = nn.Linear(512, num_actions)

    def __call__(self, x):
        x = nn.relu(self.conv1(x))
        x = nn.relu(self.conv2(x))
        x = nn.relu(self.conv3(x))
        x = x.reshape(x.shape[0], -1)  # Flatten
        x = nn.relu(self.fc1(x))
        return self.fc2(x)


class ReplayBuffer:
    """Experience replay buffer for DQN."""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]

        states = mx.array(np.stack([b[0] for b in batch]))
        actions = mx.array([b[1] for b in batch])
        rewards = mx.array([b[2] for b in batch])
        next_states = mx.array(np.stack([b[3] for b in batch]))
        dones = mx.array([b[4] for b in batch])

        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Preprocess frame: already downscaled to 84x84, just normalize."""
    return frame.astype(np.float32) / 255.0


def train_dqn(
    num_episodes: int = 100,
    batch_size: int = 32,
    gamma: float = 0.99,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.1,
    epsilon_decay: int = 1000,
    target_update: int = 10,
):
    """Train DQN on Space Invaders.

    Args:
        num_episodes: Number of episodes to train
        batch_size: Batch size for training
        gamma: Discount factor
        epsilon_start: Initial epsilon for epsilon-greedy
        epsilon_end: Final epsilon
        epsilon_decay: Episodes over which to decay epsilon
        target_update: Update target network every N episodes
    """
    # Create environment
    env = gym.make(
        "SpaceInvaders-v0",
        obs_type="downscaled",  # 84x84 frames
        frame_stack=4,  # Stack 4 frames
        max_episode_steps=5000,
    )

    # Initialize networks
    policy_net = DQN(num_actions=env.action_space.n)
    target_net = DQN(num_actions=env.action_space.n)
    target_net.load_weights(list(policy_net.parameters()))

    optimizer = optim.Adam(learning_rate=1e-4)
    replay_buffer = ReplayBuffer(capacity=10000)

    # Training stats
    episode_rewards = []
    best_reward = -float("inf")

    print("=" * 80)
    print("DQN Training on Space Invaders (MLX)")
    print("=" * 80)
    print(f"Episodes: {num_episodes}")
    print(f"Observation space: {env.observation_space.shape}")
    print(f"Action space: {env.action_space.n} actions")
    print("Device: Apple Silicon (MLX)")
    print("=" * 80)

    for episode in range(num_episodes):
        state, _ = env.reset()
        state = preprocess_frame(state)
        episode_reward = 0
        steps = 0
        start_time = time.time()

        # Epsilon-greedy decay
        epsilon = max(
            epsilon_end, epsilon_start - (epsilon_start - epsilon_end) * episode / epsilon_decay
        )

        while True:
            # Select action
            if np.random.random() < epsilon:
                action = env.action_space.sample()
            else:
                with mx.no_grad():
                    state_mx = mx.array(state[None, ...])  # Add batch dimension
                    q_values = policy_net(state_mx)
                    action = int(mx.argmax(q_values[0]).item())

            # Take step
            next_state, reward, terminated, truncated, info = env.step(action)
            next_state = preprocess_frame(next_state)
            done = terminated or truncated

            # Store transition
            replay_buffer.add(state, action, reward, next_state, done)

            state = next_state
            episode_reward += reward
            steps += 1

            # Train if enough samples
            if len(replay_buffer) >= batch_size:
                # Sample batch
                states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)

                # Compute Q-values
                def loss_fn(params):
                    policy_net.update(params)
                    current_q = policy_net(states)
                    current_q = mx.take_along_axis(current_q, actions[:, None], axis=1).squeeze()

                    with mx.no_grad():
                        next_q = target_net(next_states)
                        max_next_q = mx.max(next_q, axis=1)
                        target_q = rewards + gamma * max_next_q * (1 - dones)

                    loss = nn.losses.mse_loss(current_q, target_q)
                    return loss

                # Backward pass
                loss, grads = mx.value_and_grad(loss_fn)(dict(policy_net.parameters()))
                optimizer.update(policy_net, grads)
                mx.eval(policy_net.parameters())

            if done:
                break

        # Stats
        elapsed = time.time() - start_time
        fps = steps / elapsed if elapsed > 0 else 0
        episode_rewards.append(episode_reward)
        avg_reward = np.mean(episode_rewards[-100:]) if episode_rewards else 0

        if episode_reward > best_reward:
            best_reward = episode_reward

        print(
            f"Episode {episode+1:3d}/{num_episodes} | "
            f"Reward: {episode_reward:6.0f} | "
            f"Avg(100): {avg_reward:6.1f} | "
            f"Best: {best_reward:6.0f} | "
            f"ε: {epsilon:.3f} | "
            f"Steps: {steps:4d} | "
            f"FPS: {fps:6.1f}"
        )

        # Update target network
        if (episode + 1) % target_update == 0:
            target_net.load_weights(list(policy_net.parameters()))
            print("  → Updated target network")

    env.close()

    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print(f"Best reward: {best_reward:.0f}")
    print(f"Final avg reward (last 100): {np.mean(episode_rewards[-100:]):.1f}")
    print("=" * 80)


if __name__ == "__main__":
    train_dqn(num_episodes=100)
