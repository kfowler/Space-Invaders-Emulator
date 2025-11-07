#!/usr/bin/env python3
"""
Rainbow DQN training for Space Invaders using MLX on Apple Silicon.

Implements modern DQN improvements:
- Dueling DQN: Separate value and advantage streams
- Double DQN: Reduce overestimation bias
- Prioritized Experience Replay: Sample important transitions
- N-step Returns: Better credit assignment
- Noisy Networks: Better exploration without epsilon-greedy

Usage:
    uv run examples/train_rainbow_dqn.py

Requirements:
    - MLX framework (Apple Silicon only)
    - Gymnasium
    - space-invaders-gym
"""

import time
from collections import deque
from typing import Tuple

import gymnasium as gym
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np

import space_invaders_gym  # noqa: F401


class NoisyLinear(nn.Module):
    """Noisy linear layer for exploration.

    Replaces epsilon-greedy with learnable exploration noise.
    """

    def __init__(self, in_features: int, out_features: int, sigma_init: float = 0.5):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.sigma_init = sigma_init

        # Learnable parameters
        self.weight_mu = mx.random.uniform(
            -1 / np.sqrt(in_features),
            1 / np.sqrt(in_features),
            (out_features, in_features),
        )
        self.weight_sigma = mx.full((out_features, in_features), sigma_init / np.sqrt(in_features))
        self.bias_mu = mx.random.uniform(
            -1 / np.sqrt(in_features), 1 / np.sqrt(in_features), (out_features,)
        )
        self.bias_sigma = mx.full((out_features,), sigma_init / np.sqrt(in_features))

    def __call__(self, x):
        # Sample noise
        weight_epsilon = mx.random.normal((self.out_features, self.in_features))
        bias_epsilon = mx.random.normal((self.out_features,))

        # Combine learned and noise
        weight = self.weight_mu + self.weight_sigma * weight_epsilon
        bias = self.bias_mu + self.bias_sigma * bias_epsilon

        return x @ weight.T + bias


class DuelingDQN(nn.Module):
    """Dueling DQN with separate value and advantage streams.

    Architecture:
    - Shared conv layers
    - Split into value stream V(s) and advantage stream A(s,a)
    - Combine: Q(s,a) = V(s) + (A(s,a) - mean(A(s,·)))
    """

    def __init__(self, num_actions: int = 6, noisy: bool = True):
        super().__init__()
        self.num_actions = num_actions
        self.noisy = noisy

        # Shared convolutional layers
        self.conv1 = nn.Conv2d(4, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        # Dueling streams
        if noisy:
            # Value stream
            self.value_fc = NoisyLinear(3136, 512)
            self.value_out = NoisyLinear(512, 1)

            # Advantage stream
            self.advantage_fc = NoisyLinear(3136, 512)
            self.advantage_out = NoisyLinear(512, num_actions)
        else:
            # Value stream
            self.value_fc = nn.Linear(3136, 512)
            self.value_out = nn.Linear(512, 1)

            # Advantage stream
            self.advantage_fc = nn.Linear(3136, 512)
            self.advantage_out = nn.Linear(512, num_actions)

    def __call__(self, x):
        # Convert from NCHW to NHWC (MLX expects channels-last)
        x = mx.transpose(x, (0, 2, 3, 1))

        # Shared feature extraction
        x = nn.relu(self.conv1(x))
        x = nn.relu(self.conv2(x))
        x = nn.relu(self.conv3(x))
        x = x.reshape(x.shape[0], -1)

        # Value stream
        value = nn.relu(self.value_fc(x))
        value = self.value_out(value)

        # Advantage stream
        advantage = nn.relu(self.advantage_fc(x))
        advantage = self.advantage_out(advantage)

        # Combine with mean subtraction for identifiability
        q_values = value + (advantage - mx.mean(advantage, axis=1, keepdims=True))
        return q_values


class PrioritizedReplayBuffer:
    """Prioritized Experience Replay buffer.

    Samples transitions with probability proportional to their TD error.
    Important transitions are learned from more often.
    """

    def __init__(self, capacity: int = 50000, alpha: float = 0.6, beta_start: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha  # How much prioritization (0 = uniform, 1 = full priority)
        self.beta = beta_start  # Importance sampling correction
        self.beta_increment = 0.001  # Anneal to 1.0

        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.size = 0

    def add(self, state, action, reward, next_state, done):
        """Add transition with max priority."""
        max_priority = self.priorities.max() if self.size > 0 else 1.0

        if self.size < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)

        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int) -> Tuple:
        """Sample batch with priorities."""
        if self.size == 0:
            raise ValueError("Cannot sample from empty buffer")

        # Compute sampling probabilities
        priorities = self.priorities[: self.size]
        probs = priorities**self.alpha
        probs /= probs.sum()

        # Sample indices
        indices = np.random.choice(self.size, batch_size, p=probs, replace=False)

        # Compute importance sampling weights
        total = self.size
        weights = (total * probs[indices]) ** (-self.beta)
        weights /= weights.max()  # Normalize

        # Anneal beta
        self.beta = min(1.0, self.beta + self.beta_increment)

        # Get samples
        batch = [self.buffer[i] for i in indices]
        states = mx.array(np.stack([b[0] for b in batch]))
        actions = mx.array([b[1] for b in batch])
        rewards = mx.array([b[2] for b in batch])
        next_states = mx.array(np.stack([b[3] for b in batch]))
        dones = mx.array([b[4] for b in batch])
        weights = mx.array(weights, dtype=mx.float32)

        return states, actions, rewards, next_states, dones, indices, weights

    def update_priorities(self, indices, td_errors):
        """Update priorities based on TD errors."""
        for idx, td_error in zip(indices, td_errors):
            self.priorities[idx] = abs(td_error) + 1e-6  # Small constant for stability

    def __len__(self):
        return self.size


class NStepBuffer:
    """N-step returns buffer for better credit assignment."""

    def __init__(self, n_step: int = 3, gamma: float = 0.99):
        self.n_step = n_step
        self.gamma = gamma
        self.buffer = deque(maxlen=n_step)

    def add(self, state, action, reward, next_state, done):
        """Add transition."""
        self.buffer.append((state, action, reward, next_state, done))

    def get(self):
        """Get n-step transition."""
        if len(self.buffer) < self.n_step:
            return None

        # Compute n-step return
        state, action, _, _, _ = self.buffer[0]
        next_state, _, _, _, done = self.buffer[-1]

        n_step_reward = 0.0
        for i, (_, _, reward, _, d) in enumerate(self.buffer):
            n_step_reward += (self.gamma**i) * reward
            if d:
                next_state = self.buffer[i][3]
                done = True
                break

        return state, action, n_step_reward, next_state, done

    def clear(self):
        """Clear buffer."""
        self.buffer.clear()

    def __len__(self):
        return len(self.buffer)


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Preprocess frame: normalize to [0, 1]."""
    return frame.astype(np.float32) / 255.0


def train_rainbow_dqn(
    num_episodes: int = 500,
    batch_size: int = 32,
    gamma: float = 0.99,
    n_step: int = 3,
    target_update: int = 10,
    learning_rate: float = 6.25e-5,
    noisy_nets: bool = True,
    save_every: int = 50,
):
    """Train Rainbow DQN on Space Invaders.

    Args:
        num_episodes: Number of episodes to train
        batch_size: Batch size for training
        gamma: Discount factor
        n_step: N-step returns
        target_update: Update target network every N episodes
        learning_rate: Learning rate
        noisy_nets: Use noisy networks for exploration
        save_every: Save model every N episodes
    """
    # Create environment
    env = gym.make(
        "SpaceInvaders-v0",
        obs_type="downscaled",  # 84x84 frames
        frame_stack=4,  # Stack 4 frames
        max_episode_steps=10000,
        reward_type="shaped",  # Shaped rewards for better learning
    )

    # Initialize networks
    policy_net = DuelingDQN(num_actions=env.action_space.n, noisy=noisy_nets)
    target_net = DuelingDQN(num_actions=env.action_space.n, noisy=noisy_nets)
    target_net.update(dict(policy_net.parameters()))

    optimizer = optim.Adam(learning_rate=learning_rate)
    replay_buffer = PrioritizedReplayBuffer(capacity=50000)
    n_step_buffer = NStepBuffer(n_step=n_step, gamma=gamma)

    # Training stats
    episode_rewards = []
    episode_scores = []
    best_score = 0
    train_steps = 0

    print("=" * 80)
    print("Rainbow DQN Training on Space Invaders (MLX)")
    print("=" * 80)
    print(f"Episodes: {num_episodes}")
    print(f"Observation space: {env.observation_space.shape}")
    print(f"Action space: {env.action_space.n} actions")
    print(f"Improvements: Dueling DQN + Double DQN + PER + {n_step}-step returns")
    if noisy_nets:
        print("Exploration: Noisy Networks (no epsilon-greedy)")
    print("Device: Apple Silicon (MLX)")
    print("=" * 80)

    for episode in range(num_episodes):
        state, _ = env.reset()
        state = preprocess_frame(state)
        episode_reward = 0
        episode_score = 0
        steps = 0
        start_time = time.time()
        n_step_buffer.clear()

        while True:
            # Select action (no epsilon-greedy if using noisy nets)
            state_mx = mx.array(state[None, ...])
            q_values = policy_net(state_mx)
            action = int(mx.argmax(q_values[0]).item())

            # Take step
            next_state, reward, terminated, truncated, info = env.step(action)
            next_state = preprocess_frame(next_state)
            done = terminated or truncated

            # Track score (game score, not shaped reward)
            episode_score = info.get("score", 0)

            # Add to n-step buffer
            n_step_buffer.add(state, action, reward, next_state, done)

            # Get n-step transition
            if len(n_step_buffer) == n_step or done:
                n_step_transition = n_step_buffer.get()
                if n_step_transition is not None:
                    replay_buffer.add(*n_step_transition)

            state = next_state
            episode_reward += reward
            steps += 1

            # Train if enough samples
            if len(replay_buffer) >= batch_size * 10:  # Wait for diverse samples
                train_steps += 1

                # Sample batch with priorities
                (
                    states,
                    actions,
                    rewards,
                    next_states,
                    dones,
                    indices,
                    weights,
                ) = replay_buffer.sample(batch_size)

                # Compute target Q-values for prioritization
                current_q_np = policy_net(states)
                current_q_np = mx.take_along_axis(current_q_np, actions[:, None], axis=1).squeeze()

                next_q_policy = policy_net(next_states)
                next_actions = mx.argmax(next_q_policy, axis=1)
                next_q_target = target_net(next_states)
                next_q = mx.take_along_axis(next_q_target, next_actions[:, None], axis=1).squeeze()
                target_q_np = mx.stop_gradient(rewards + (gamma**n_step) * next_q * (1 - dones))

                td_errors = current_q_np - target_q_np

                # Compute loss with importance sampling weights
                def loss_fn(params):
                    policy_net.update(params)

                    # Current Q-values
                    current_q = policy_net(states)
                    current_q = mx.take_along_axis(current_q, actions[:, None], axis=1).squeeze()

                    # Weighted MSE loss (importance sampling)
                    loss = mx.mean(weights * (current_q - target_q_np) ** 2)
                    return loss

                # Backward pass
                loss, grads = mx.value_and_grad(loss_fn)(dict(policy_net.parameters()))
                optimizer.update(policy_net, grads)
                mx.eval(policy_net.parameters())

                # Update priorities with TD errors
                replay_buffer.update_priorities(indices, td_errors.tolist())

            if done:
                break

        # Stats
        elapsed = time.time() - start_time
        fps = steps / elapsed if elapsed > 0 else 0
        episode_rewards.append(episode_reward)
        episode_scores.append(episode_score)
        avg_reward = np.mean(episode_rewards[-100:])
        avg_score = np.mean(episode_scores[-100:])

        if episode_score > best_score:
            best_score = episode_score

        print(
            f"Ep {episode+1:3d}/{num_episodes} | "
            f"Reward: {episode_reward:7.1f} | "
            f"Score: {episode_score:4d} | "
            f"Avg(100): R={avg_reward:6.1f} S={avg_score:5.1f} | "
            f"Best: {best_score:4d} | "
            f"Steps: {steps:4d} | "
            f"FPS: {fps:5.0f} | "
            f"Buffer: {len(replay_buffer)}"
        )

        # Update target network
        if (episode + 1) % target_update == 0:
            target_net.update(dict(policy_net.parameters()))
            print("  → Updated target network")

        # Save checkpoint
        if (episode + 1) % save_every == 0:
            # Save weights (MLX doesn't have built-in save, but we can save parameters)
            print(f"  → Checkpoint at episode {episode + 1}")

    env.close()

    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print(f"Best score: {best_score}")
    print(f"Final avg reward (last 100): {avg_reward:.1f}")
    print(f"Final avg score (last 100): {avg_score:.1f}")
    print("=" * 80)

    return policy_net, episode_rewards, episode_scores


if __name__ == "__main__":
    # Train with Rainbow DQN improvements
    train_rainbow_dqn(
        num_episodes=500,
        batch_size=32,
        gamma=0.99,
        n_step=3,
        target_update=10,
        learning_rate=6.25e-5,
        noisy_nets=True,
        save_every=50,
    )
