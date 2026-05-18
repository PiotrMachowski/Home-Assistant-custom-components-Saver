import json
import logging
import regex
from datetime import datetime
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.template import Template, TemplateEnvironment
from homeassistant.util import dt as dt_util
try:
    from homeassistant.helpers.template.states import _get_state_if_valid
except ImportError:
    # For HA before 2026.5
    from homeassistant.helpers.template import _get_state_if_valid


from .const import *
from .utils import parse_datetime

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = SAVER_SCHEMA

_NAMESPACE_SAFE_ATTRS = frozenset({
    "variable", "entity",
    "cmp_eq", "cmp_neq", "cmp_gt", "cmp_lt", "cmp_gte", "cmp_lte",
    "cmp_time_after", "cmp_time_before", "cmp_time_after_now",
    "time_elapsed",
})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Saver integration (component level, required for condition platform)."""
    if hass.data.get(DOMAIN, {}).get("setup_done"):
        return True
    if DOMAIN in config:
        await hass.async_add_executor_job(setup_entry, hass, config)
        hass.data.setdefault(DOMAIN, {})["setup_done"] = True
    try:
        from . import condition  # noqa: F401
    except Exception as err:
        _LOGGER.error("Failed to load Saver condition platform: %s", err, exc_info=True)
    return True


async def async_setup_entry(hass, config_entry):
    if hass.data.get(DOMAIN, {}).get("setup_done"):
        return True
    result = await hass.async_add_executor_job(setup_entry, hass, config_entry)
    hass.data.setdefault(DOMAIN, {})["setup_done"] = True
    return result


class SaverNamespace:
    """Namespace object exposed as `saver` in Jinja2 templates."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._hass = hass
        self._entity_id = entity_id

    def _get_variables(self) -> dict[str, Any] | None:
        saver_state = _get_state_if_valid(self._hass, self._entity_id)
        if saver_state is None:
            return None
        return saver_state.attributes.get(ATTR_VARIABLES)

    def _get_entities(self) -> dict[str, Any] | None:
        saver_state = _get_state_if_valid(self._hass, self._entity_id)
        if saver_state is None:
            return None
        return saver_state.attributes.get(ATTR_ENTITIES)

    # -- existing accessors --

    def variable(self, variable: str) -> Any:
        variables = self._get_variables()
        if variables is None or variable not in variables:
            return None
        return variables[variable]

    def entity(self, entity_id: str, attribute: str | None = None) -> Any:
        entities = self._get_entities()
        if entities is None or entity_id not in entities:
            return None
        state = entities[entity_id]
        state_val = state["state"] if isinstance(state, dict) else state.state
        attrs = state["attributes"] if isinstance(state, dict) else state.attributes
        if attribute is None:
            return state_val
        if attribute not in attrs:
            return None
        return attrs[attribute]

    # -- time comparisons (full datetime including date) --

    def cmp_time_after(self, variable: str, compare_to: str) -> bool | None:
        """True if saved variable datetime is after compare_to."""
        var_dt, cmp_dt = self._resolve_time_pair(variable, compare_to)
        if var_dt is None or cmp_dt is None:
            return None
        return var_dt > cmp_dt

    def cmp_time_before(self, variable: str, compare_to: str) -> bool | None:
        """True if saved variable datetime is before compare_to."""
        var_dt, cmp_dt = self._resolve_time_pair(variable, compare_to)
        if var_dt is None or cmp_dt is None:
            return None
        return var_dt < cmp_dt

    def cmp_time_after_now(self, variable: str) -> bool | None:
        """True if saved variable datetime is after the current datetime."""
        val = self.variable(variable)
        if val is None:
            return None
        var_dt = parse_datetime(str(val))
        if var_dt is None:
            return None
        return var_dt > dt_util.now()

    def _resolve_time_pair(self, variable: str, compare_to: str) -> tuple[datetime | None, datetime | None]:
        val = self.variable(variable)
        if val is None:
            return None, None
        var_dt = parse_datetime(str(val))
        cmp_dt = parse_datetime(compare_to)
        return var_dt, cmp_dt

    # -- general comparisons --

    def cmp_eq(self, variable: str, value: str) -> bool | None:
        val = self.variable(variable)
        return str(val) == value if val is not None else None

    def cmp_neq(self, variable: str, value: str) -> bool | None:
        val = self.variable(variable)
        return str(val) != value if val is not None else None

    def cmp_gt(self, variable: str, value: str) -> bool | None:
        return self._numeric_cmp(variable, value, lambda a, b: a > b)

    def cmp_lt(self, variable: str, value: str) -> bool | None:
        return self._numeric_cmp(variable, value, lambda a, b: a < b)

    def cmp_gte(self, variable: str, value: str) -> bool | None:
        return self._numeric_cmp(variable, value, lambda a, b: a >= b)

    def cmp_lte(self, variable: str, value: str) -> bool | None:
        return self._numeric_cmp(variable, value, lambda a, b: a <= b)

    def _numeric_cmp(self, variable: str, value: str, op: Callable[[float, float], bool]) -> bool | None:
        val = self.variable(variable)
        if val is None:
            return None
        try:
            return op(float(val), float(value))
        except (ValueError, TypeError):
            return None

    # -- elapsed time --

    def time_elapsed(self, variable: str) -> float | None:
        """Seconds elapsed since the time stored in the variable."""
        val = self.variable(variable)
        if val is None:
            return None
        dt = parse_datetime(str(val))
        if dt is None:
            return None
        return (dt_util.now() - dt).total_seconds()

    def __repr__(self) -> str:
        return "<template SaverNamespace>"


class SaverVariableTemplate:
    """Legacy wrapper for backwards compatibility."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._namespace = SaverNamespace(hass, entity_id)

    def __call__(self, variable: str) -> Any:
        return self._namespace.variable(variable)

    def __repr__(self) -> str:
        return "<template SaverVariable>"


class SaverEntityTemplate:
    """Legacy wrapper for backwards compatibility."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._namespace = SaverNamespace(hass, entity_id)

    def __call__(self, entity_id: str, attribute: str | None = None) -> Any:
        return self._namespace.entity(entity_id, attribute)

    def __repr__(self) -> str:
        return "<template SaverEntityTemplate>"


def setup_templates(hass: HomeAssistant) -> None:
    def is_safe_callable(self: TemplateEnvironment, obj) -> bool:
        # noinspection PyUnresolvedReferences
        return (isinstance(obj, (SaverVariableTemplate, SaverEntityTemplate, SaverNamespace))
                or self.saver_original_is_safe_callable(obj))

    def is_safe_attribute(self: TemplateEnvironment, obj, attr, value) -> bool:
        if isinstance(obj, SaverNamespace):
            return attr in _NAMESPACE_SAFE_ATTRS
        # noinspection PyUnresolvedReferences
        return self.saver_original_is_safe_attribute(obj, attr, value)

    def patch_environment(env: TemplateEnvironment) -> None:
        saver_ns = SaverNamespace(hass, SAVER_ENTITY_ID)
        env.globals["saver"] = saver_ns
        # Legacy aliases for backwards compatibility
        env.globals["saver_variable"] = SaverVariableTemplate(hass, SAVER_ENTITY_ID)
        env.globals["saver_entity"] = SaverEntityTemplate(hass, SAVER_ENTITY_ID)

    def patched_init(
        self: TemplateEnvironment,
        hass_param: HomeAssistant | None,
        limited: bool | None = False,
        strict: bool | None = False,
        log_fn: Callable[[int, str], None] | None = None,
    ) -> None:
        # noinspection PyUnresolvedReferences
        self.saver_original__init__(hass_param, limited, strict, log_fn)
        patch_environment(self)

    if not hasattr(TemplateEnvironment, 'saver_original__init__'):
        TemplateEnvironment.saver_original__init__ = TemplateEnvironment.__init__
        TemplateEnvironment.__init__ = patched_init

    if not hasattr(TemplateEnvironment, 'saver_original_is_safe_callable'):
        TemplateEnvironment.saver_original_is_safe_callable = TemplateEnvironment.is_safe_callable
        TemplateEnvironment.is_safe_callable = is_safe_callable

    if not hasattr(TemplateEnvironment, 'saver_original_is_safe_attribute'):
        TemplateEnvironment.saver_original_is_safe_attribute = TemplateEnvironment.is_safe_attribute
        TemplateEnvironment.is_safe_attribute = is_safe_attribute

    tpl = Template("", hass)
    tpl._strict = False
    tpl._limited = False
    patch_environment(tpl._env)
    tpl._strict = True
    tpl._limited = False
    patch_environment(tpl._env)


def setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    saver_entity = SaverEntity()
    component.add_entities([saver_entity])
    setup_templates(hass)

    def clear(_call: ServiceCall) -> None:
        saver_entity.clear()
        hass.bus.fire('event_saver_cleared')

    def delete(call: ServiceCall) -> None:
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        saver_entity.delete(entity_id)
        hass.bus.fire('event_saver_deleted_entity', {'entity_id': entity_id})

    def delete_regex(call: ServiceCall) -> None:
        data = call.data
        entity_id_regex = data[CONF_ENTITY_ID_REGEX]
        entities = saver_entity.delete_regex(entity_id_regex)
        hass.bus.fire('event_saver_deleted_entity_by_regex', {'entity_id_regex': entity_id_regex, 'entities': entities})

    def delete_variable(call: ServiceCall) -> None:
        data = call.data
        variable = data[CONF_NAME]
        saver_entity.delete_variable(variable)
        hass.bus.fire('event_saver_deleted_variable', {'variable': variable})

    def delete_variable_regex(call: ServiceCall) -> None:
        data = call.data
        variable_regex = data[CONF_REGEX]
        variables = saver_entity.delete_variable_regex(variable_regex)
        hass.bus.fire('event_saver_deleted_variable_by_regex', {'regex': variable_regex, 'variables': variables})

    def restore_state(call: ServiceCall) -> None:
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        should_delete = data[CONF_DELETE_AFTER_RUN]
        transition = data.get(ATTR_TRANSITION, None)
        saver_entity.restore(entity_id, should_delete, transition)
        hass.bus.fire('event_saver_restored', {'entity_id': entity_id})

    def save_state(call: ServiceCall) -> None:
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        saver_entity.save(entity_id)
        hass.bus.fire('event_saver_saved_entity', {'entity_id': entity_id})

    def set_variable(call) -> None:
        data = call.data
        name = data[CONF_NAME]
        if data.get(CONF_USE_CURRENT_TIME, False):
            value = dt_util.now().isoformat()
        elif CONF_VALUE_ENTITY in data:
            state = hass.states.get(data[CONF_VALUE_ENTITY])
            value = state.state if state is not None else None
        else:
            value = data[CONF_VALUE]
        saver_entity.set_variable(name, value)
        hass.bus.fire('event_saver_saved_variable', {'variable': name, 'value': value})

    hass.services.register(DOMAIN, SERVICE_CLEAR, clear, SERVICE_CLEAR_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE, delete, SERVICE_DELETE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE_REGEX, delete_regex, SERVICE_DELETE_REGEX_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE_VARIABLE, delete_variable, SERVICE_DELETE_VARIABLE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE_VARIABLE_REGEX, delete_variable_regex, SERVICE_DELETE_VARIABLE_REGEX_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_RESTORE_STATE, restore_state, SERVICE_RESTORE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SAVE_STATE, save_state, SERVICE_SAVE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SET_VARIABLE, set_variable, SERVICE_SET_VARIABLE_SCHEMA)

    return True


class SaverEntity(RestoreEntity):
    _attr_translation_key: str = DOMAIN

    def __init__(self) -> None:
        self._entities_db = {}
        self._variables_db = {}
        self._attr_unique_id = SAVER_ENTITY_ID

    @property
    def name(self) -> str:
        return NAME

    def clear(self) -> None:
        self._entities_db = {}
        self._variables_db = {}
        self.schedule_update_ha_state()

    def delete(self, entity_ids: list[str]) -> None:
        tmp = {**self._entities_db}
        for entity_id in entity_ids:
            if entity_id in tmp:
                tmp.pop(entity_id)
        self._entities_db = tmp
        self.schedule_update_ha_state()

    def delete_regex(self, entity_id_regex: str) -> list[str]:
        entity_ids = [variable for variable in self._entities_db if regex.match(entity_id_regex, variable)]
        self.delete(entity_ids)
        return entity_ids

    def delete_variable(self, variable: str) -> None:
        self._delete_variables([variable])

    def delete_variable_regex(self, variable_regex: str) -> list[str]:
        variables = [variable for variable in self._variables_db if regex.match(variable_regex, variable)]
        self._delete_variables(variables)
        return variables

    def _delete_variables(self, variables: list[str]) -> None:
        tmp = {**self._variables_db}
        for variable in variables:
            if variable in tmp:
                tmp.pop(variable)
        self._variables_db = tmp
        self.schedule_update_ha_state()

    def restore(self, entity_ids: list[str], delete: bool, transition: float | None) -> None:
        entity_ids = [entity_id for entity_id in entity_ids if entity_id in self._entities_db]
        entities_data = {
            entity_id: self.convert_to_scene_params(
                self._entities_db[entity_id]
            )
            for entity_id in entity_ids
        }
        if delete:
            tmp = {**self._entities_db}
            for entity_id in entity_ids:
                tmp.pop(entity_id)
            self._entities_db = tmp
        data: dict[str, Any] = { "entities": entities_data }
        if transition is not None:
            data["transition"] = transition
        self.hass.services.call("scene", "apply", data)

    def save(self, entity_ids: list[str]) -> None:
        self._entities_db = {**self._entities_db}
        for entity_id in entity_ids:
            self._entities_db[entity_id] = self.hass.states.get(entity_id)
        self.schedule_update_ha_state()

    def set_variable(self, variable: str, value: Any) -> None:
        self._variables_db = {
            **self._variables_db,
            variable: value,
        }
        self.schedule_update_ha_state()

    @property
    def state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_ENTITIES: self._entities_db,
            ATTR_VARIABLES: self._variables_db
        }

    @property
    def state(self) -> int:
        return len(self._entities_db) + len(self._variables_db)

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        if (
            state is not None
            and state.attributes is not None
            and ATTR_VARIABLES in state.attributes and not isinstance(state.attributes[ATTR_VARIABLES], list)
            and ATTR_ENTITIES in state.attributes and not isinstance(state.attributes[ATTR_ENTITIES], list)
        ):
            self._variables_db = state.attributes[ATTR_VARIABLES]
            self._entities_db = state.attributes[ATTR_ENTITIES]

    @staticmethod
    def convert_to_scene_params(saved_state: Any) -> dict[str, Any]:
        state = saved_state["state"] if isinstance(saved_state, dict) else saved_state.state
        attrs = saved_state["attributes"] if isinstance(saved_state, dict) else saved_state.attributes
        return {
            "state": state,
            **{
                attr_key: json.loads(json.dumps(attr_val))
                for attr_key, attr_val in attrs.items()
                if attr_key not in IGNORED_ATTRIBUTES
            },
        }
