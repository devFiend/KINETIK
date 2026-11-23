"""Unit tests for SaveManager and local JSON persistence."""
import os
import tempfile
import pytest
from src.storage.save_manager import PlayerProfile, SaveManager


def test_save_manager_lifecycle():
    """Verify SaveManager saves and reloads profile with exact data retention."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = os.path.join(temp_dir, "test_save.json")
        manager = SaveManager(filepath=test_path)

        # Modify profile
        manager.profile.nickname = "GrandMaster"
        manager.profile.total_xp = 15200
        manager.profile.best_target_rush_score = 42500
        manager.profile.achievements["ACH_FIRST_FLING"] = True
        manager.save()

        # Reload from fresh instance
        reloaded = SaveManager(filepath=test_path)
        assert reloaded.profile.nickname == "GrandMaster"
        assert reloaded.profile.total_xp == 15200
        assert reloaded.profile.best_target_rush_score == 42500
        assert reloaded.profile.achievements["ACH_FIRST_FLING"] is True


def test_save_manager_corruption_recovery():
    """Verify SaveManager catches corrupt JSON, archives backup, and recovers with clean profile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = os.path.join(temp_dir, "corrupt_save.json")
        # Write corrupted syntax
        with open(test_path, "w") as f:
            f.write("INVALID_SYNTAX_{{[}")

        manager = SaveManager(filepath=test_path)
        assert manager.profile is not None
        assert manager.profile.total_xp == 0
        assert os.path.exists(test_path + ".bak")
