"""Tests for the Adaptive Lighting helpers."""

import pytest
from homeassistant.components.adaptive_lighting.helpers import scene_state_matches

XY_SCENE = {"brightness": 54, "color_mode": "xy", "xy_color": (0.595, 0.254)}


@pytest.mark.parametrize(
    ("state", "attributes", "matches"),
    [
        ("on", {"brightness": 54, "xy_color": (0.595, 0.254)}, True),
        ("on", {"brightness": 57, "xy_color": (0.6, 0.26)}, True),  # tolerances
        ("on", {"brightness": 138, "xy_color": (0.595, 0.254)}, False),
        ("on", {"brightness": 54, "xy_color": (0.529, 0.251)}, False),
        ("on", {"brightness": 54}, False),  # no color reported
        ("off", {}, False),
    ],
)
def test_scene_state_matches_xy(state, attributes, matches):
    """Brightness ±3 and xy ±0.01 count as matching the scene."""
    assert scene_state_matches(state, attributes, "on", XY_SCENE) is matches


def test_scene_state_matches_other_color_modes():
    """Each color mode compares its own attribute; without one, the first set."""
    hs_scene = {"brightness": 100, "color_mode": "hs", "hs_color": (359.0, 80.0)}
    assert scene_state_matches(
        "on",
        {"brightness": 100, "hs_color": (1.0, 82.0)},
        "on",
        hs_scene,
    )
    assert not scene_state_matches(
        "on",
        {"brightness": 100, "hs_color": (10.0, 80.0)},
        "on",
        hs_scene,
    )
    ct_scene = {"color_mode": "color_temp", "color_temp_kelvin": 2200}
    assert scene_state_matches("on", {"color_temp_kelvin": 2210}, "on", ct_scene)
    assert not scene_state_matches("on", {"color_temp_kelvin": 2700}, "on", ct_scene)
    rgb_scene = {"color_mode": "rgb", "rgb_color": (255, 22, 120)}
    assert scene_state_matches("on", {"rgb_color": (252, 25, 118)}, "on", rgb_scene)
    assert not scene_state_matches("on", {"rgb_color": (255, 76, 150)}, "on", rgb_scene)
    # Brightness-only lights and scenes without a color.
    assert scene_state_matches(
        "on",
        {"brightness": 10},
        "on",
        {"brightness": 10, "color_mode": "brightness"},
    )
    assert scene_state_matches("on", {"brightness": 11}, "on", {"brightness": 10})
    # Off in the scene only needs the light to be off.
    assert scene_state_matches("off", {}, "off", {"brightness": 10})
    assert not scene_state_matches("on", {"brightness": 10}, "off", {})
