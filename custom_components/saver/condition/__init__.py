"""Saver automation conditions platform."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .time_elapsed import TimeElapsedCondition
from .compare_value import CompareValueCondition
from .compare_time import CompareTimeCondition
from .const import (
    CONF_CONDITION_NAME_TIME_ELAPSED,
    CONF_CONDITION_NAME_COMPARE_VALUE,
    CONF_CONDITION_NAME_COMPARE_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_conditions(hass: HomeAssistant) -> dict[str, Any]:
    """Return condition classes for the Saver integration."""
    return {
        CONF_CONDITION_NAME_TIME_ELAPSED: TimeElapsedCondition,
        CONF_CONDITION_NAME_COMPARE_VALUE: CompareValueCondition,
        CONF_CONDITION_NAME_COMPARE_TIME: CompareTimeCondition,
    }
