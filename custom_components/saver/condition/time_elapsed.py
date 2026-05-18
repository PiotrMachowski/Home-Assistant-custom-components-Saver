"""Saver time_elapsed automation condition."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_OPTIONS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.condition import Condition, ConditionConfig
from homeassistant.helpers.typing import ConfigType

from ..const import CONF_VARIABLE, CONF_ABOVE, CONF_BELOW, SAVER_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

CONDITION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPTIONS): vol.All(
            vol.Schema({
                vol.Required(CONF_VARIABLE): cv.string,
                vol.Optional(CONF_ABOVE): vol.Coerce(float),
                vol.Optional(CONF_BELOW): vol.Coerce(float),
            }),
            cv.has_at_least_one_key(CONF_ABOVE, CONF_BELOW),
        ),
    }
)


class TimeElapsedCondition(Condition):
    """Check if elapsed time since a stored variable exceeds or falls below a threshold."""

    def __init__(self, hass: HomeAssistant, config: ConditionConfig) -> None:
        super().__init__(hass, config)
        self._config = config

    @classmethod
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        return CONDITION_SCHEMA(config)

    def _options(self) -> dict[str, Any]:
        if isinstance(self._config, dict):
            return self._config.get(CONF_OPTIONS, {}) or {}
        return getattr(self._config, "options", None) or {}

    def _async_check(self, **kwargs: Any) -> bool | None:
        try:
            from .. import SaverNamespace

            ns = SaverNamespace(self._hass, SAVER_ENTITY_ID)
            options = self._options()
            variable = options.get(CONF_VARIABLE)
            elapsed = ns.time_elapsed(variable)
            if elapsed is None:
                return False
            if CONF_ABOVE in options and elapsed <= options[CONF_ABOVE]:
                return False
            if CONF_BELOW in options and elapsed >= options[CONF_BELOW]:
                return False
            return True
        except Exception as e:
            _LOGGER.error("Error evaluating time_elapsed: %s", e, exc_info=True)
            return False
