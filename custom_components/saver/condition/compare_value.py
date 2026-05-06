"""Saver compare_value automation condition."""

import logging

import voluptuous as vol
from homeassistant.const import CONF_OPTIONS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.condition import Condition, ConditionChecker, ConditionConfig
from homeassistant.helpers.typing import ConfigType

from ..const import (
    CONF_VARIABLE,
    CONF_COMPARISON,
    CONF_VALUE,
    CMP_EQ,
    CMP_NEQ,
    CMP_GT,
    CMP_LT,
    CMP_GTE,
    CMP_LTE,
    SAVER_ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)

CONDITION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPTIONS): vol.Schema({
            vol.Required(CONF_VARIABLE): cv.string,
            vol.Required(CONF_COMPARISON): vol.In([CMP_EQ, CMP_NEQ, CMP_GT, CMP_LT, CMP_GTE, CMP_LTE]),
            vol.Required(CONF_VALUE): cv.string,
        }),
    }
)

_CMP_METHODS = {
    CMP_EQ: "cmp_eq",
    CMP_NEQ: "cmp_neq",
    CMP_GT: "cmp_gt",
    CMP_LT: "cmp_lt",
    CMP_GTE: "cmp_gte",
    CMP_LTE: "cmp_lte",
}


class CompareValueCondition(Condition):
    """Compare a stored variable against a value using standard operators."""

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
                comparison = options.get(CONF_COMPARISON)
                value = options.get(CONF_VALUE)
                method_name = _CMP_METHODS.get(comparison)
                if method_name is None:
                    return False
                result = getattr(ns, method_name)(variable, value)
                return bool(result) if result is not None else False
            except Exception as e:
                _LOGGER.error("Error evaluating compare_value: %s", e, exc_info=True)
                return False

        return checker
