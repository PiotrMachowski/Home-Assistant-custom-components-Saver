"""Saver automation trigger platform (new class-based API).

Exposes a ``Trigger`` subclass via ``async_get_triggers``. Home Assistant's
automation engine instantiates the class with a :class:`TriggerConfig` and
invokes :meth:`async_attach_runner`, which schedules a point-in-time callback
based on the datetime stored in a Saver variable.

YAML usage::

    triggers:
      - trigger: saver.compare_time
        options:
          variable: my_var
          offset: 0
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_OPTIONS
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.helpers.trigger import Trigger, TriggerActionRunner, TriggerConfig
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import CONF_VARIABLE, SAVER_ENTITY_ID, ATTR_VARIABLES
from .utils import parse_datetime_with_kind

_LOGGER = logging.getLogger(__name__)

CONF_OFFSET = "offset"

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VARIABLE): cv.string,
        vol.Optional(CONF_OFFSET, default=0): vol.Coerce(float),
    }
)


class CompareTimeTrigger(Trigger):
    """Fires when the datetime stored in a Saver variable is reached."""

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        super().__init__(hass, config)
        self._config = config

    @classmethod
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate the specific (options/target) portion of the config."""
        if CONF_OPTIONS not in config:
            raise vol.Invalid("'options' block is required for saver.compare_time")
        config = dict(config)
        config[CONF_OPTIONS] = OPTIONS_SCHEMA(config[CONF_OPTIONS])
        return config

    async def async_attach_runner(
        self, run_action: TriggerActionRunner
    ) -> CALLBACK_TYPE:
        """Schedule a point-in-time callback and re-arm on variable changes."""
        hass = self._hass
        options: dict[str, Any] = dict(self._config.options or {})
        variable: str = options[CONF_VARIABLE]
        offset: float = float(options.get(CONF_OFFSET, 0) or 0)
        saver_entity_id = SAVER_ENTITY_ID

        unsub_point: list[CALLBACK_TYPE | None] = [None]
        last_target: list[datetime | None] = [None]

        def _variable_value() -> Any:
            state = hass.states.get(saver_entity_id)
            if state is None:
                return None
            variables = state.attributes.get(ATTR_VARIABLES) or {}
            return variables.get(variable)

        def _next_target() -> tuple[datetime | None, str | None]:
            val = _variable_value()
            if val is None:
                return None, None
            dt, kind = parse_datetime_with_kind(str(val))
            if dt is None:
                return None, None
            target = dt + timedelta(seconds=offset)
            now = dt_util.now()
            if target > now:
                return target, kind
            if kind in ("time", "date"):
                while target <= now:
                    target += timedelta(days=1)
                return target, kind
            return None, kind

        @callback
        def _schedule(*_: Any) -> None:
            target, _kind = _next_target()
            if target is None:
                if unsub_point[0]:
                    unsub_point[0]()
                    unsub_point[0] = None
                last_target[0] = None
                _LOGGER.debug(
                    "saver.compare_time: no future target for variable %r", variable
                )
                return
            if last_target[0] == target and unsub_point[0] is not None:
                return
            if unsub_point[0]:
                unsub_point[0]()
                unsub_point[0] = None
            last_target[0] = target
            _LOGGER.debug(
                "saver.compare_time: scheduling variable %r at %s (offset=%s)",
                variable,
                target,
                offset,
            )
            unsub_point[0] = async_track_point_in_time(hass, _fire, target)

        @callback
        def _fire(now: datetime) -> None:
            unsub_point[0] = None
            _LOGGER.debug(
                "saver.compare_time: firing for variable %r at %s", variable, now
            )
            run_action(
                {
                    "variable": variable,
                    "offset": offset,
                    "fired_at": now,
                },
                f"Saver variable '{variable}' time reached",
            )
            _schedule()

        @callback
        def _state_listener(event: Any) -> None:
            _schedule()

        unsub_state = async_track_state_change_event(
            hass, [saver_entity_id], _state_listener
        )
        _schedule()

        @callback
        def _remove() -> None:
            unsub_state()
            if unsub_point[0]:
                unsub_point[0]()
                unsub_point[0] = None

        return _remove


async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
    """Return the Saver trigger registry."""
    return {"compare_time": CompareTimeTrigger}
