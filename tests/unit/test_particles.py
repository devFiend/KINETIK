"""Unit tests for ParticlePool."""
import pytest
from src.rendering.particles import ParticlePool


def test_particle_pool_initialization():
    """Verify particle pool pre-allocates requested number of particles."""
    pool = ParticlePool(pool_size=100)
    assert len(pool.particles) == 100
    assert all(not p.active for p in pool.particles)


def test_particle_pool_burst_emission():
    """Verify emit_burst activates requested count of particles."""
    pool = ParticlePool(pool_size=100)
    pool.emit_burst(x=200.0, y=200.0, count=20)

    active_count = sum(1 for p in pool.particles if p.active)
    assert active_count == 20


def test_particle_pool_update_and_expiration():
    """Verify particles expire and become inactive when lifetime reaches 0."""
    pool = ParticlePool(pool_size=50)
    pool.emit_burst(x=100.0, y=100.0, count=10)

    # Step simulation past maximum particle lifetime (0.6s)
    pool.update(0.7)
    active_count = sum(1 for p in pool.particles if p.active)
    assert active_count == 0
