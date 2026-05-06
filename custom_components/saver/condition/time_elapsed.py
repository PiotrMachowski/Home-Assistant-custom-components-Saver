"""Saver time_elapsed automation condition."""

import logging

import voluptuous as vol
from homeassistant.const import CONF_OPTIONS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.condition import Condition, ConditionChecker, ConditionConfig
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
        try:
            super().__init__(hass, config)
        except Exception:
            self._hass = hass
        self.config = config

    @classmethod
    async def async_validate_config(cls, hass: HomeAssistant, config: ConfigType) -> ConfigType:
        return CONDITION_SCHEMA(config)

    async def async_get_checker(self) -> ConditionChecker:
        if isinstance(self.config, dict):
            options = self.config.get(CONF_OPTIONS, {})
        else:
            options = self.config.options if hasattr(self.config, "options") else {}

        def checker(**kwargs) -> bool:
            try:
                from .. import SaverNamespace
                ns = SaverNamespace(self._hass, SAVER_ENTITY_ID)
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

        return checker
