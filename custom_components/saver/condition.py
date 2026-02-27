"""Saver condition for Home Assistant automations."""
from __future__ import annotations

from datetime import datetime, date
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.condition import ConditionCheckerType
from homeassistant.helpers.template import _get_state_if_valid

from .const import (
    CONDITION_SCHEMA,
    CONF_OPERATOR,
    CONF_VALUE,
    CONF_VARIABLE,
    DOMAIN,
    OPERATOR_EQ,
    OPERATOR_GTE,
    OPERATOR_GT,
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_NEQ,
    OPERATOR_TIME_AFTER,
    OPERATOR_TIME_BEFORE,
)


def _parse_datetime(value: str) -> datetime | None:
    """Parse a time or datetime string into a full datetime object."""
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(value, fmt).time()
            return datetime.combine(date.today(), t)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _evaluate(stored_value: str, operator: str, compare_value: str) -> bool:
    """Evaluate a comparison between a stored value and a compare value."""
    if operator == OPERATOR_EQ:
        return str(stored_value) == compare_value
    if operator == OPERATOR_NEQ:
        return str(stored_value) != compare_value

    if operator in (OPERATOR_TIME_AFTER, OPERATOR_TIME_BEFORE):
        var_dt = _parse_datetime(str(stored_value))
        cmp_dt = _parse_datetime(compare_value)
        if var_dt is None or cmp_dt is None:
            return False
        if operator == OPERATOR_TIME_AFTER:
            return var_dt > cmp_dt
        return var_dt < cmp_dt

    # Numeric comparisons
    try:
        num_stored = float(stored_value)
        num_compare = float(compare_value)
    except (ValueError, TypeError):
        return False

    if operator == OPERATOR_GT:
        return num_stored > num_compare
    if operator == OPERATOR_LT:
        return num_stored < num_compare
    if operator == OPERATOR_GTE:
        return num_stored >= num_compare
    if operator == OPERATOR_LTE:
        return num_stored <= num_compare

    return False


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: dict[str, Any]
) -> ConditionCheckerType:
    """Create a condition checker from config."""
    variable = config[CONF_VARIABLE]
    operator = config[CONF_OPERATOR]
    value = config[CONF_VALUE]
    entity_id = f"{DOMAIN}.{DOMAIN}"

    @callback
    def check_condition(hass: HomeAssistant, variables: dict[str, Any] | None = None) -> bool:
        saver_state = _get_state_if_valid(hass, entity_id)
        if saver_state is None:
            return False
        variables_db = saver_state.attributes.get("variables", {})
        if variable not in variables_db:
            return False
        return _evaluate(variables_db[variable], operator, value)

    return check_condition
