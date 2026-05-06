"""Saver automation conditions platform."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .compare_time import CompareTimeCondition
from .compare_value import CompareValueCondition
from .time_elapsed import TimeElapsedCondition
from ..const import (
    CONDITION_NAME_TIME_ELAPSED,
    CONDITION_NAME_COMPARE_VALUE,
    CONDITION_NAME_COMPARE_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_conditions(hass: HomeAssistant) -> dict[str, Any]:
    """Return condition classes for the Saver integration."""
    return {
        CONDITION_NAME_TIME_ELAPSED: TimeElapsedCondition,
        CONDITION_NAME_COMPARE_VALUE: CompareValueCondition,
        CONDITION_NAME_COMPARE_TIME: CompareTimeCondition,
    }
