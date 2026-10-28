"""Home Assistant test helpers, across HA versions.

Home Assistant's own test helpers (`tests.common`, `tests.components.*`) moved
into the `pytest_homeassistant` package (`core/packages/pytest-home-assistant`)
in newer versions. Import them from wherever the checked-out core has them.
"""

try:
    from tests.common import (
        MockConfigEntry,
        async_fire_time_changed,
        async_mock_service,
        mock_area_registry,
    )
    from tests.components.diagnostics import get_diagnostics_for_config_entry
except ImportError:  # HA with the `pytest_homeassistant` package
    from pytest_homeassistant.common import (
        MockConfigEntry,
        async_fire_time_changed,
        async_mock_service,
        mock_area_registry,
    )
    from pytest_homeassistant.components.diagnostics import (
        get_diagnostics_for_config_entry,
    )

__all__ = [
    "MockConfigEntry",
    "async_fire_time_changed",
    "async_mock_service",
    "get_diagnostics_for_config_entry",
    "mock_area_registry",
]
