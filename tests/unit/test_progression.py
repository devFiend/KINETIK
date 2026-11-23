"""Unit tests for ProgressionManager, Ranks, and Achievements."""
import os
import tempfile
import pytest
from src.game.progression import ACHIEVEMENTS, RANKS, ProgressionManager
from src.storage.save_manager import SaveManager


def test_progression_rank_hierarchy():
    """Verify cumulative XP correctly maps to appropriate RankTier."""
    with tempfile.TemporaryDirectory() as temp_dir:
        save = SaveManager(os.path.join(temp_dir, "test.json"))
        prog = ProgressionManager(save)

        # 0 XP -> Awakening
        assert prog.current_rank.name == "Awakening"

        # 1600 XP -> Sensitive
        save.profile.total_xp = 1600
        assert prog.current_rank.name == "Sensitive"

        # 12000 XP -> Manipulator
        save.profile.total_xp = 12000
        assert prog.current_rank.name == "Manipulator"


def test_round_xp_and_achievement_unlock():
    """Verify round completion grants XP and unlocks achievements."""
    with tempfile.TemporaryDirectory() as temp_dir:
        save = SaveManager(os.path.join(temp_dir, "test.json"))
        prog = ProgressionManager(save)

        earned_xp, promoted = prog.record_round_results(
            final_score=15000,
            total_hits=10,
            max_combo=5.0
        )
        assert earned_xp > 1500
        assert promoted is True
        assert prog.profile.achievements.get("ACH_SHARPSHOOTER") is True
        assert prog.profile.achievements.get("ACH_COMBO_KING") is True
