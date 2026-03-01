"""Saver automation conditions platform."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .time_elapsed import TimeElapsedCondition
from .compare_value import CompareValueCondition
from .compare_time import CompareTimeCondition

_LOGGER = logging.getLogger(__name__)


async def async_get_conditions(hass: HomeAssistant) -> dict[str, Any]:
    """Return condition classes for the Saver integration."""
    return {
        "time_elapsed": TimeElapsedCondition,
        "compare_value": CompareValueCondition,
        "compare_time": CompareTimeCondition,
    }
