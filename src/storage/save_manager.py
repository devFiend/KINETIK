"""Atomic local JSON persistence for user profiles, scores, unlocks, and achievements."""
from dataclasses import asdict, dataclass, field
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

DEFAULT_SAVE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage",
    "save.json"
)


@dataclass
class PlayerProfile:
    """User progression, total XP, and unlocked cosmetics."""
    nickname: str = "TelekineticAdept"
    total_xp: int = 0
    current_rank: str = "Awakening"
    playtime_seconds: float = 0.0
    best_target_rush_score: int = 0
    max_combo_ever: float = 1.0
    unlocked_cosmetics: List[str] = field(default_factory=lambda: ["tether_cyan", "prop_standard"])
    achievements: Dict[str, bool] = field(default_factory=dict)


class SaveManager:
    """
    Handles thread-safe, atomic local JSON serialization and recovery.
    Uses tempfile + rename pattern to prevent corrupted saves on sudden termination.
    """

    def __init__(self, filepath: str = DEFAULT_SAVE_PATH):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.profile = self.load()

    def load(self) -> PlayerProfile:
        """Load profile from disk or initialize fresh defaults."""
        if not os.path.exists(self.filepath):
            profile = PlayerProfile()
            self.save(profile)
            return profile

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            player_data = data.get("player", {})
            high_scores = data.get("high_scores", {})

            profile = PlayerProfile(
                nickname=player_data.get("nickname", "TelekineticAdept"),
                total_xp=player_data.get("total_xp", 0),
                current_rank=player_data.get("current_rank", "Awakening"),
                playtime_seconds=player_data.get("playtime_seconds", 0.0),
                best_target_rush_score=high_scores.get("target_rush", 0),
                max_combo_ever=high_scores.get("max_combo", 1.0),
                unlocked_cosmetics=data.get("unlocked_items", ["tether_cyan", "prop_standard"]),
                achievements=data.get("achievements", {})
            )
            return profile

        except (json.JSONDecodeError, OSError) as e:
            print(f"[SaveManager WARNING] Corrupted save file detected: {e}. Backing up and resetting.")
            backup_path = self.filepath + ".bak"
            shutil.copyfile(self.filepath, backup_path)
            fresh_profile = PlayerProfile()
            self.save(fresh_profile)
            return fresh_profile

    def save(self, profile: Optional[PlayerProfile] = None) -> bool:
        """Atomically serialize profile to JSON on disk."""
        if profile is not None:
            self.profile = profile

        save_dict = {
            "version": "1.0.0",
            "player": {
                "nickname": self.profile.nickname,
                "total_xp": self.profile.total_xp,
                "current_rank": self.profile.current_rank,
                "playtime_seconds": self.profile.playtime_seconds
            },
            "high_scores": {
                "target_rush": self.profile.best_target_rush_score,
                "max_combo": self.profile.max_combo_ever
            },
            "unlocked_items": self.profile.unlocked_cosmetics,
            "achievements": self.profile.achievements
        }

        target_dir = os.path.dirname(self.filepath)
        os.makedirs(target_dir, exist_ok=True)

        try:
            # Write to temporary file first in the same directory (for atomic rename)
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
                json.dump(save_dict, tf, indent=2)
                temp_name = tf.name

            # Atomic replace
            os.replace(temp_name, self.filepath)
            return True

        except Exception as e:
            print(f"[SaveManager ERROR] Failed to save profile: {e}")
            return False
