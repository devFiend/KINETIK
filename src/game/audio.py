"""Procedural audio synthesizer generating dynamic sound effects in memory via NumPy."""
import math
from typing import Optional
import numpy as np
import pygame


class ProceduralAudioEngine:
    """
    Generates dynamic 16-bit PCM sound effects procedurally in memory.
    Requires zero external audio asset files.
    """

    def __init__(self, sample_rate: int = 44100, volume: float = 0.7):
        self.sample_rate = sample_rate
        self.volume = max(0.0, min(1.0, volume))
        self.muted = False
        self._initialized = False

        self._grab_sound: Optional[pygame.mixer.Sound] = None
        self._push_sound: Optional[pygame.mixer.Sound] = None
        self._impact_sound: Optional[pygame.mixer.Sound] = None

        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            self._initialized = True
            self._synthesize_effects()
        except Exception as e:
            print(f"[AudioEngine WARNING] Could not initialize mixer: {e}")
            self._initialized = False

    def _synthesize_effects(self) -> None:
        """Synthesize base sound effect waveforms."""
        # 1. Grab Chime: Rising double frequency (440Hz -> 880Hz, 0.12s)
        duration = 0.12
        t = np.linspace(0.0, duration, int(self.sample_rate * duration), endpoint=False)
        freq = np.linspace(440.0, 880.0, len(t))
        envelope = np.sin(np.pi * t / duration)  # Smooth bell envelope
        wave = (np.sin(2.0 * np.pi * freq * t) * envelope * 0.4 * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        self._grab_sound = pygame.sndarray.make_sound(stereo)

        # 2. Push Boom: Low frequency bass drop with noise (160Hz -> 40Hz, 0.25s)
        duration = 0.25
        t = np.linspace(0.0, duration, int(self.sample_rate * duration), endpoint=False)
        freq = np.linspace(160.0, 40.0, len(t))
        noise = np.random.uniform(-0.1, 0.1, len(t))
        envelope = np.exp(-12.0 * t)  # Exponential decay
        wave = ((np.sin(2.0 * np.pi * freq * t) + noise) * envelope * 0.6 * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        self._push_sound = pygame.sndarray.make_sound(stereo)

        # 3. Impact Thud: Sharp click followed by damped resonant thud (0.15s)
        duration = 0.15
        t = np.linspace(0.0, duration, int(self.sample_rate * duration), endpoint=False)
        envelope = np.exp(-22.0 * t)
        wave = (np.sin(2.0 * np.pi * 120.0 * t) * envelope * 0.5 * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        self._impact_sound = pygame.sndarray.make_sound(stereo)

    def toggle_mute(self) -> bool:
        """Toggle mute state."""
        self.muted = not self.muted
        return self.muted

    def play_grab(self) -> None:
        if self._initialized and not self.muted and self._grab_sound:
            self._grab_sound.set_volume(self.volume * 0.7)
            self._grab_sound.play()

    def play_push(self) -> None:
        if self._initialized and not self.muted and self._push_sound:
            self._push_sound.set_volume(self.volume)
            self._push_sound.play()

    def play_impact(self, impulse: float) -> None:
        """Play impact sound scaled by collision energy."""
        if self._initialized and not self.muted and self._impact_sound:
            # Scale volume from 0.2 to 1.0 based on impulse (50..800)
            vol_scale = min(1.0, max(0.2, (impulse - 50.0) / 750.0))
            self._impact_sound.set_volume(self.volume * vol_scale)
            self._impact_sound.play()

    def play_throw(self, speed: float) -> None:
        """Synthesize dynamic whoosh pitch-scaled to throw velocity."""
        if not self._initialized or self.muted:
            return

        try:
            duration = 0.18
            t = np.linspace(0.0, duration, int(self.sample_rate * duration), endpoint=False)
            freq = np.linspace(250.0 + speed * 0.15, 100.0, len(t))
            noise = np.random.uniform(-0.15, 0.15, len(t))
            envelope = np.sin(np.pi * t / duration)
            wave = ((np.sin(2.0 * np.pi * freq * t) + noise) * envelope * 0.4 * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(self.volume * min(1.0, speed / 1500.0))
            sound.play()
        except Exception:
            pass
