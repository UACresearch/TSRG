"""Frozen R20 routing independent of model inference and data loading."""
from dataclasses import dataclass
import math

SPECIALIST_CATEGORIES = frozenset(("event", "heritage"))
BASE_CATEGORIES = frozenset(("natural", "purpose_built"))
ALL_CATEGORIES = SPECIALIST_CATEGORIES | BASE_CATEGORIES


@dataclass(frozen=True)
class CameraPrediction:
    roll_deg: float
    pitch_deg: float
    square_vfov_deg: float


def m2_par_prediction(category: str, m0: CameraPrediction, specialist_pitch_deg: float | None = None) -> CameraPrediction:
    """R20: use specialist *pitch only* in event/heritage; preserve M0 others."""
    if not isinstance(category, str):
        raise TypeError("category must be a string")
    category = category.strip().lower()
    if category not in ALL_CATEGORIES:
        raise ValueError(f"unknown category: {category!r}")
    if category in SPECIALIST_CATEGORIES:
        if specialist_pitch_deg is None or not math.isfinite(specialist_pitch_deg):
            raise ValueError("finite specialist pitch is required for this category")
        pitch = specialist_pitch_deg
    else:
        pitch = m0.pitch_deg
    return CameraPrediction(roll_deg=m0.roll_deg, pitch_deg=pitch, square_vfov_deg=m0.square_vfov_deg)
