"""Helper functions for the Adaptive Lighting custom components."""

from __future__ import annotations

import base64
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value between minimum and maximum."""
    return max(minimum, min(value, maximum))


def int_to_base36(num: int) -> str:
    """Convert an integer to its base-36 representation using numbers and uppercase letters.

    Base-36 encoding uses digits 0-9 and uppercase letters A-Z, providing a case-insensitive
    alphanumeric representation. The function takes an integer `num` as input and returns
    its base-36 representation as a string.

    Parameters
    ----------
    num
        The integer to convert to base-36.

    Returns
    -------
    str
        The base-36 representation of the input integer.

    Examples
    --------
    >>> num = 123456
    >>> base36_num = int_to_base36(num)
    >>> print(base36_num)
    '2N9'

    """
    alphanumeric_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if num == 0:
        return alphanumeric_chars[0]

    base36_str = ""
    base = len(alphanumeric_chars)

    while num:
        num, remainder = divmod(num, base)
        base36_str = alphanumeric_chars[remainder] + base36_str

    return base36_str


def short_hash(string: str, length: int = 4) -> str:
    """Create a hash of 'string' with length 'length'."""
    return base64.b32encode(string.encode()).decode("utf-8").zfill(length)[:length]


def remove_vowels(input_str: str, length: int = 4) -> str:
    """Remove vowels from a string and return a string of length 'length'."""
    vowels = "aeiouAEIOU"
    output_str = "".join([char for char in input_str if char not in vowels])
    return output_str.zfill(length)[:length]


def color_difference_redmean(
    rgb1: tuple[float, float, float],
    rgb2: tuple[float, float, float],
) -> float:
    """Distance between colors in RGB space (redmean metric).

    The maximal distance between (255, 255, 255) and (0, 0, 0) ≈ 765.

    Sources:
    - https://en.wikipedia.org/wiki/Color_difference#Euclidean
    - https://www.compuphase.com/cmetric.htm
    """
    r_hat = (rgb1[0] + rgb2[0]) / 2
    delta_r, delta_g, delta_b = (
        (col1 - col2) for col1, col2 in zip(rgb1, rgb2, strict=True)
    )
    red_term = (2 + r_hat / 256) * delta_r**2
    green_term = 4 * delta_g**2
    blue_term = (2 + (255 - r_hat) / 256) * delta_b**2
    return math.sqrt(red_term + green_term + blue_term)


def get_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Retrieve the friendly name of an entity."""
    state = hass.states.get(entity_id)
    if state and hasattr(state, "attributes"):
        attributes: dict[str, Any] = dict(getattr(state, "attributes", {}))
        return attributes.get("friendly_name", entity_id)
    return entity_id


# Tolerances used to decide whether a light reports its state in a scene.
SCENE_BRIGHTNESS_TOLERANCE = 3  # of 255
SCENE_XY_TOLERANCE = 0.01
SCENE_HUE_TOLERANCE = 3.0  # degrees
SCENE_SATURATION_TOLERANCE = 3.0  # percent
SCENE_MIRED_TOLERANCE = 5.0
SCENE_RGB_TOLERANCE = 5  # per channel

# Scene color mode -> (state attribute, comparison kind).
_SCENE_COLOR_ATTRIBUTES: dict[str, tuple[str, str]] = {
    "xy": ("xy_color", "xy"),
    "hs": ("hs_color", "hs"),
    "color_temp": ("color_temp_kelvin", "kelvin"),
    "rgb": ("rgb_color", "rgb"),
    "rgbw": ("rgbw_color", "rgb"),
    "rgbww": ("rgbww_color", "rgb"),
}
# Without a color mode, the first color that is set is used (like a scene does).
_SCENE_COLOR_FALLBACK_ORDER = ("hs", "color_temp", "rgb", "rgbw", "rgbww", "xy")


def _color_matches(kind: str, current: Any, target: Any) -> bool:
    if current is None:
        return False
    try:
        if kind == "xy":
            return all(
                abs(c - t) <= SCENE_XY_TOLERANCE
                for c, t in zip(current, target, strict=True)
            )
        if kind == "hs":
            hue_diff = abs(current[0] - target[0]) % 360
            hue_diff = min(hue_diff, 360 - hue_diff)
            return (
                hue_diff <= SCENE_HUE_TOLERANCE
                and abs(current[1] - target[1]) <= SCENE_SATURATION_TOLERANCE
            )
        if kind == "kelvin":
            return (
                abs(1_000_000 / current - 1_000_000 / target) <= SCENE_MIRED_TOLERANCE
            )
        return all(
            abs(c - t) <= SCENE_RGB_TOLERANCE
            for c, t in zip(current, target, strict=True)
        )
    except (TypeError, ValueError, ZeroDivisionError):
        return False


def scene_state_matches(
    current_state: str,
    current_attributes: Mapping[str, Any],
    target_state: str,
    target_attributes: Mapping[str, Any],
) -> bool:
    """Whether a light's reported state matches its (stored) state in a scene.

    Compares on/off, brightness and the scene's color (in the scene's color
    mode), with small tolerances for rounding by the light or integration.
    """
    if current_state != target_state:
        return False
    if target_state != "on":
        return True
    target_brightness = target_attributes.get("brightness")
    if target_brightness is not None:
        current_brightness = current_attributes.get("brightness")
        if (
            current_brightness is None
            or abs(current_brightness - target_brightness) > SCENE_BRIGHTNESS_TOLERANCE
        ):
            return False
    color_mode = target_attributes.get("color_mode")
    if color_mode in _SCENE_COLOR_ATTRIBUTES:
        modes = (color_mode,)
    elif color_mode in (None, "unknown"):
        modes = _SCENE_COLOR_FALLBACK_ORDER
    else:  # onoff, brightness, white: no color to compare
        return True
    for mode in modes:
        attribute, kind = _SCENE_COLOR_ATTRIBUTES[mode]
        target = target_attributes.get(attribute)
        if target is not None:
            return _color_matches(kind, current_attributes.get(attribute), target)
    return True
