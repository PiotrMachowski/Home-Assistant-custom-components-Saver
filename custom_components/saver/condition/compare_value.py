"""Saver compare_value automation condition."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_OPTIONS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.condition import Condition, ConditionConfig
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
