"""Unit tests for ProceduralAudioEngine."""
import os
import pygame
import pytest
from src.game.audio import ProceduralAudioEngine


def test_audio_engine_mute_toggle():
    """Verify audio engine initializes and toggles mute cleanly."""
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    engine = ProceduralAudioEngine()

    assert engine.muted is False
    assert engine.toggle_mute() is True
    assert engine.muted is True
    assert engine.toggle_mute() is False
    assert engine.muted is False


def test_audio_engine_procedural_calls():
    """Verify calling audio triggers executes without raising exceptions."""
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    engine = ProceduralAudioEngine()

    engine.play_grab()
    engine.play_push()
    engine.play_impact(350.0)
    engine.play_throw(1200.0)
