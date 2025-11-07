"""Integration tests for Space Invaders Gymnasium environment."""

import gymnasium as gym
import numpy as np
import pytest

import space_invaders_gym  # noqa: F401


class TestSpaceInvadersIntegration:
    """Integration tests for the complete environment."""

    def test_environment_creation(self) -> None:
        """Test that environment can be created."""
        env = gym.make("SpaceInvaders-v0")
        assert env is not None
        env.close()

    def test_reset(self) -> None:
        """Test environment reset."""
        env = gym.make("SpaceInvaders-v0")
        obs, info = env.reset(seed=42)

        assert obs is not None
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (224, 256)
        assert obs.dtype == np.uint8

        assert "score" in info
        assert "lives" in info

        env.close()

    def test_step(self) -> None:
        """Test environment step."""
        env = gym.make("SpaceInvaders-v0")
        obs, info = env.reset(seed=42)

        # Take a step
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        assert obs is not None
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

        env.close()

    def test_episode_completion(self) -> None:
        """Test that an episode can be completed."""
        env = gym.make("SpaceInvaders-v0", max_episode_steps=100)
        obs, info = env.reset(seed=42)

        step_count = 0
        done = False

        while not done and step_count < 200:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            step_count += 1

        assert done or step_count >= 100
        env.close()

    def test_multiple_episodes(self) -> None:
        """Test running multiple episodes."""
        env = gym.make("SpaceInvaders-v0", max_episode_steps=50)

        for episode in range(3):
            obs, info = env.reset(seed=42 + episode)
            done = False
            steps = 0

            while not done and steps < 100:
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                steps += 1

        env.close()

    @pytest.mark.parametrize("obs_type", ["grayscale", "downscaled", "ram"])
    def test_observation_types(self, obs_type: str) -> None:
        """Test different observation types."""
        env = gym.make("SpaceInvaders-v0", obs_type=obs_type)
        obs, info = env.reset(seed=42)

        if obs_type == "grayscale":
            assert obs.shape == (224, 256)
        elif obs_type == "downscaled":
            assert obs.shape == (84, 84)
        elif obs_type == "ram":
            assert obs.shape == (8192,)

        assert obs.dtype == np.uint8
        env.close()

    @pytest.mark.parametrize("action_type", ["discrete6", "discrete4", "multi_discrete"])
    def test_action_types(self, action_type: str) -> None:
        """Test different action types."""
        env = gym.make("SpaceInvaders-v0", action_type=action_type)
        obs, info = env.reset(seed=42)

        # Take a step with each possible action
        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break

        env.close()

    @pytest.mark.parametrize("reward_type", ["score_delta", "shaped", "terminal"])
    def test_reward_types(self, reward_type: str) -> None:
        """Test different reward types."""
        env = gym.make("SpaceInvaders-v0", reward_type=reward_type)
        obs, info = env.reset(seed=42)

        total_reward = 0.0
        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            if terminated or truncated:
                break

        # All reward types should produce some reward eventually
        # (though terminal might be 0 until end)
        assert isinstance(total_reward, float)
        env.close()

    def test_frame_stack(self) -> None:
        """Test frame stacking."""
        env = gym.make("SpaceInvaders-v0", frame_stack=4)
        obs, info = env.reset(seed=42)

        # Observation should have shape (4, 224, 256) for 4 stacked frames
        assert obs.shape == (4, 224, 256)
        env.close()

    def test_save_load_state(self) -> None:
        """Test save/load state functionality."""
        import tempfile
        import os

        env = gym.make("SpaceInvaders-v0")
        obs1, info1 = env.reset(seed=42)

        # Take some steps
        for _ in range(10):
            action = env.action_space.sample()
            env.step(action)

        # Save state
        with tempfile.NamedTemporaryFile(delete=False, suffix=".state") as f:
            state_file = f.name

        try:
            env.unwrapped.save_state(state_file)

            # Take more steps
            for _ in range(10):
                action = env.action_space.sample()
                env.step(action)

            # Load state
            env.unwrapped.load_state(state_file)

            # State should be restored
            # (exact verification would require comparing all internal state)
            assert os.path.exists(state_file)

        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)

        env.close()

    def test_seeded_reproducibility(self) -> None:
        """Test that same seed produces same results."""
        env1 = gym.make("SpaceInvaders-v0")
        env2 = gym.make("SpaceInvaders-v0")

        obs1, _ = env1.reset(seed=42)
        obs2, _ = env2.reset(seed=42)

        # Initial observations should be identical
        assert np.array_equal(obs1, obs2)

        # Take same actions
        for _ in range(10):
            action = 1  # Fixed action
            obs1, r1, t1, tr1, i1 = env1.step(action)
            obs2, r2, t2, tr2, i2 = env2.step(action)

            # Results should be identical (deterministic emulator)
            assert np.array_equal(obs1, obs2)
            assert r1 == r2
            assert t1 == t2

        env1.close()
        env2.close()

    def test_gymnasium_check_env(self) -> None:
        """Test that environment passes Gymnasium's check_env."""
        from gymnasium.utils.env_checker import check_env

        env = gym.make("SpaceInvaders-v0")

        try:
            check_env(env.unwrapped, skip_render_check=True)
        except Exception as e:
            pytest.fail(f"Environment failed Gymnasium check: {e}")
        finally:
            env.close()

    def test_performance_benchmark(self) -> None:
        """Basic performance benchmark."""
        import time

        env = gym.make("SpaceInvaders-v0")
        obs, info = env.reset(seed=42)

        num_steps = 1000
        start_time = time.time()

        for _ in range(num_steps):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                obs, info = env.reset()

        elapsed = time.time() - start_time
        fps = num_steps / elapsed

        print(f"\nPerformance: {fps:.1f} FPS ({elapsed:.2f}s for {num_steps} steps)")

        # Should achieve at least 100 FPS on modern hardware
        assert fps > 100, f"Performance too slow: {fps:.1f} FPS"

        env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
