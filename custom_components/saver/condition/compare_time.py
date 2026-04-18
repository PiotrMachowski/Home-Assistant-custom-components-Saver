"""Saver compare_time automation condition."""
import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.condition import Condition, ConditionChecker
from homeassistant.helpers.typing import ConfigType

from ..const import (
    CONF_VARIABLE, CONF_COMPARISON, CONF_COMPARE_TO, DOMAIN,
    CMP_TIME_AFTER, CMP_TIME_BEFORE, CMP_TIME_AFTER_NOW,
)

_LOGGER = logging.getLogger(__name__)

CONF_OPTIONS = "options"

CONDITION_SCHEMA = vol.Schema(
    {
        vol.Required("condition"): cv.string,
        vol.Required(CONF_OPTIONS): vol.Schema({
            vol.Required(CONF_VARIABLE): cv.string,
            vol.Required(CONF_COMPARISON): vol.In([CMP_TIME_AFTER, CMP_TIME_BEFORE, CMP_TIME_AFTER_NOW]),
            vol.Optional(CONF_COMPARE_TO): cv.string,
        }),
        vol.Optional("alias"): cv.string,
        vol.Optional("enabled"): cv.boolean,
    }
)


def _validate_compare_to(config: dict) -> dict:
    """Ensure compare_to is present when comparison is not after_now."""
    options = config.get(CONF_OPTIONS, {})
    comparison = options.get(CONF_COMPARISON)
    if comparison != CMP_TIME_AFTER_NOW and CONF_COMPARE_TO not in options:
        raise vol.Invalid(f"'compare_to' is required when comparison is '{comparison}'")
    return config


class CompareTimeCondition(Condition):
    """Compare a stored datetime variable against another time or the current time."""

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        try:
            super().__init__(hass, config)
        except Exception:
            self._hass = hass
        self.config = config

    @classmethod
    async def async_validate_config(cls, hass: HomeAssistant, config: ConfigType) -> ConfigType:
        validated = CONDITION_SCHEMA(config)
        return _validate_compare_to(validated)

    @classmethod
    async def async_validate_complete_config(cls, hass: HomeAssistant, complete_config: ConfigType) -> ConfigType:
        return await cls.async_validate_config(hass, complete_config)

    async def async_get_checker(self) -> ConditionChecker:
        if isinstance(self.config, dict):
            options = self.config.get(CONF_OPTIONS, {})
        else:
            options = self.config.options if hasattr(self.config, "options") else {}

        def checker(**kwargs) -> bool:
            try:
                from .. import SaverNamespace
                ns = SaverNamespace(self._hass, f"{DOMAIN}.{DOMAIN}")
                variable = options.get(CONF_VARIABLE)
                comparison = options.get(CONF_COMPARISON)
                compare_to = options.get(CONF_COMPARE_TO)

                if comparison == CMP_TIME_AFTER_NOW:
                    result = ns.cmp_time_after_now(variable)
                elif comparison == CMP_TIME_AFTER:
                    result = ns.cmp_time_after(variable, compare_to)
                elif comparison == CMP_TIME_BEFORE:
                    result = ns.cmp_time_before(variable, compare_to)
                else:
                    return False
                return bool(result) if result is not None else False
            except Exception as e:
                _LOGGER.error("Error evaluating compare_time: %s", e, exc_info=True)
                return False

        return checker
