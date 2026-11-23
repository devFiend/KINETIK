"""Telekinetic Rank hierarchy, XP calculations, and persistent achievements."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from src.storage.save_manager import PlayerProfile, SaveManager


@dataclass
class RankTier:
    """Definition of a telekinetic rank tier."""
    rank_id: int
    name: str
    required_xp: int
    perk: str


# Official Telekinetic Rank Progression Hierarchy
RANKS: List[RankTier] = [
    RankTier(1, "Awakening", 0, "Default Telekinesis & Free Play access"),
    RankTier(2, "Sensitive", 1500, "Violet Flux tether theme"),
    RankTier(3, "Initiate", 4500, "The Stack game mode + Tungsten heavy prop"),
    RankTier(4, "Manipulator", 10000, "Force Push shockwave unlocked"),
    RankTier(5, "Adept", 20000, "Emerald Matrix tether + Chaos mode"),
    RankTier(6, "Master", 35000, "Stasis Hover ability + Antimatter prop"),
    RankTier(7, "Ascendant", 60000, "Solar Flare golden particle trails"),
    RankTier(8, "Singularity", 100000, "Cosmic Black Hole tether + 'Mind Unleashed' title"),
]


@dataclass
class Achievement:
    """Milestone achievement."""
    code: str
    title: str
    description: str
    badge_icon: str


ACHIEVEMENTS: Dict[str, Achievement] = {
    "ACH_FIRST_FLING": Achievement("ACH_FIRST_FLING", "First Spark", "Perform your very first telekinetic throw.", "⚡"),
    "ACH_SHARPSHOOTER": Achievement("ACH_SHARPSHOOTER", "Kinetic Marksman", "Hit 8 or more target drones in a single round.", "🎯"),
    "ACH_COMBO_KING": Achievement("ACH_COMBO_KING", "Flow State", "Achieve maximum 5.0x combo multiplier.", "👑"),
    "ACH_MACH_FLING": Achievement("ACH_MACH_FLING", "Mach Fling", "Throw an object with speed exceeding 1800 px/s.", "🚀"),
    "ACH_INITIATE": Achievement("ACH_INITIATE", "True Initiate", "Promoted to Rank III: Initiate.", "💠"),
}


class ProgressionManager:
    """
    Manages XP accumulation, rank promotions, and real-time achievement unlocks.
    """

    def __init__(self, save_manager: SaveManager):
        self.save_manager = save_manager
        self.profile: PlayerProfile = save_manager.profile
        self.recent_unlocks: List[str] = []
        self._sync_current_rank()

    @property
    def current_rank(self) -> RankTier:
        """Get the active RankTier based on total cumulative XP."""
        current = RANKS[0]
        for rank in RANKS:
            if self.profile.total_xp >= rank.required_xp:
                current = rank
            else:
                break
        return current

    @property
    def next_rank(self) -> Optional[RankTier]:
        """Get the next achievable RankTier, or None if at max rank."""
        for rank in RANKS:
            if self.profile.total_xp < rank.required_xp:
                return rank
        return None

    @property
    def rank_progress_fraction(self) -> float:
        """Normalized progress [0.0, 1.0] towards next rank tier."""
        curr = self.current_rank
        nxt = self.next_rank
        if nxt is None:
            return 1.0
        range_xp = nxt.required_xp - curr.required_xp
        earned_in_tier = self.profile.total_xp - curr.required_xp
        return max(0.0, min(1.0, earned_in_tier / range_xp))

    def _sync_current_rank(self) -> None:
        self.profile.current_rank = self.current_rank.name

    def calculate_round_xp(self, final_score: int, total_hits: int, max_combo: float) -> int:
        """
        XP Formula:
        XP = floor(Score / 10) + (Hits * 20) + floor(MaxCombo * 50)
        """
        base_xp = final_score // 10
        hit_bonus = total_hits * 20
        combo_bonus = int(max_combo * 50)
        return base_xp + hit_bonus + combo_bonus

    def record_round_results(self, final_score: int, total_hits: int, max_combo: float) -> Tuple[int, bool]:
        """
        Commit round results, calculate XP, evaluate rank promotion, and save.
        Returns:
            (earned_xp, promoted_to_new_rank)
        """
        earned_xp = self.calculate_round_xp(final_score, total_hits, max_combo)
        prior_rank_id = self.current_rank.rank_id

        self.profile.total_xp += earned_xp

        # Update high score records
        if final_score > self.profile.best_target_rush_score:
            self.profile.best_target_rush_score = final_score
        if max_combo > self.profile.max_combo_ever:
            self.profile.max_combo_ever = max_combo

        # Check rank promotion
        self._sync_current_rank()
        promoted = self.current_rank.rank_id > prior_rank_id

        if promoted:
            self.recent_unlocks.append(f"PROMOTION: Rank {self.current_rank.name}! ({self.current_rank.perk})")
            if self.current_rank.rank_id >= 3:
                self.unlock_achievement("ACH_INITIATE")

        # Evaluate round achievements
        if total_hits >= 8:
            self.unlock_achievement("ACH_SHARPSHOOTER")
        if max_combo >= 5.0:
            self.unlock_achievement("ACH_COMBO_KING")

        self.save_manager.save(self.profile)
        return earned_xp, promoted

    def unlock_achievement(self, code: str) -> bool:
        """Unlock an achievement milestone if not already achieved."""
        if code not in ACHIEVEMENTS:
            return False

        if not self.profile.achievements.get(code, False):
            self.profile.achievements[code] = True
            ach = ACHIEVEMENTS[code]
            self.recent_unlocks.append(f"{ach.badge_icon} UNLOCKED: {ach.title}!")
            self.save_manager.save(self.profile)
            return True
        return False
