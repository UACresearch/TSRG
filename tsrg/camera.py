"""Angle/field-of-view helpers for the audited square-crop target schema.

These are independent implementations of standard camera geometry, not a copy
of Puffin or GeoCalib source code. All output angles are in degrees.
"""
import math


def radians_to_degrees(angle_rad: float) -> float:
    if not math.isfinite(angle_rad):
        raise ValueError("angle_rad must be finite")
    return math.degrees(angle_rad)


def original_hfov_to_square_vfov_deg(horizontal_fov_rad: float, width: int, height: int) -> float:
    """Convert full-image horizontal FoV to the FoV of a centered square crop.

    Pinhole-camera assumption, no post-crop resizing distortion. Width and
    height are the *original* image dimensions, before the center-square crop.
    """
    if not math.isfinite(horizontal_fov_rad) or not 0 < horizontal_fov_rad < math.pi:
        raise ValueError("horizontal_fov_rad must lie strictly between 0 and pi")
    if isinstance(width, bool) or isinstance(height, bool) or not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integer dimensions")
    square_to_original_width = min(width, height) / width
    square_vfov_rad = 2.0 * math.atan(square_to_original_width * math.tan(horizontal_fov_rad / 2.0))
    return math.degrees(square_vfov_rad)
