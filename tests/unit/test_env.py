"""Baseline environment and sanity verification tests."""
import os
import sys
import pytest


def test_python_version():
    """Verify runtime meets minimum Python 3.12 requirement."""
    assert sys.version_info >= (3, 12), f"Requires Python 3.12+, found: {sys.version}"


def test_core_imports():
    """Verify core scientific and gaming libraries import cleanly."""
    import numpy as np
    assert np is not None

    import pygame
    assert pygame is not None

    import pymunk
    assert pymunk is not None

    import cv2
    assert cv2 is not None

    import mediapipe
    assert mediapipe is not None


def test_config_constants():
    """Verify baseline configuration parameters are initialized within sane bounds."""
    from src.config import (
        TARGET_FPS,
        PINCH_ENTER_THRESHOLD,
        PINCH_EXIT_THRESHOLD,
        COLOR_BACKGROUND,
        MAX_RELEASE_VELOCITY
    )
    assert TARGET_FPS in (30, 60, 120)
    assert PINCH_ENTER_THRESHOLD < PINCH_EXIT_THRESHOLD, "Enter threshold must be tighter than exit for hysteresis"
    assert len(COLOR_BACKGROUND) == 3
    assert MAX_RELEASE_VELOCITY > 0
