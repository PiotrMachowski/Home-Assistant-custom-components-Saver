import json
import logging
import regex
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.template import _get_state_if_valid, Template, TemplateEnvironment

from .const import *

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = SAVER_SCHEMA


def setup(hass, config) -> bool:
    if DOMAIN not in config:
        return True
    return setup_entry(hass, config)


async def async_setup_entry(hass, config_entry):
    result = await hass.async_add_executor_job(setup_entry, hass, config_entry)
    return result


class SaverVariableTemplate:
    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._hass = hass
        self._entity_id = entity_id

    def __call__(self, variable: str) -> Any:
        saver_state = _get_state_if_valid(self._hass, self._entity_id)
        if saver_state is None:
            return None
        variables = saver_state.attributes["variables"]
        if variable in variables:
            return variables[variable]
        return None

    def __repr__(self) -> str:
        return "<template SaverVariable>"


class SaverEntityTemplate:
    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._hass = hass
        self._entity_id = entity_id

    def __call__(self, entity_id: str, attribute: str | None = None) -> Any:
        saver_state = _get_state_if_valid(self._hass, self._entity_id)
        if saver_state is None:
            return None
        entities = saver_state.attributes["entities"]
        if entity_id not in entities:
            return None
        state = entities[entity_id]
        state_val = state["state"] if isinstance(state, dict) else state.state
        attrs = state["attributes"] if isinstance(state, dict) else state.attributes
        if attribute is None:
            return state_val
        if attribute not in attrs:
            return None
        return attrs[attribute]

    def __repr__(self) -> str:
        return "<template SaverEntityTemplate>"


def setup_templates(hass: HomeAssistant) -> None:
    def is_safe_callable(self: TemplateEnvironment, obj) -> bool:
        # noinspection PyUnresolvedReferences
        return (isinstance(obj, (SaverVariableTemplate, SaverEntityTemplate))
                or self.saver_original_is_safe_callable(obj))

    def patch_environment(env: TemplateEnvironment) -> None:
        env.globals["saver_variable"] = SaverVariableTemplate(hass, f"{DOMAIN}.{DOMAIN}")
        env.globals["saver_entity"] = SaverEntityTemplate(hass, f"{DOMAIN}.{DOMAIN}")

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
        value = data[CONF_VALUE]
        saver_entity.set_variable(name, value)
        hass.bus.fire('event_saver_saved_variable', {'variable': name, 'value': value})

    hass.services.register(DOMAIN, SERVICE_CLEAR, clear, SERVICE_CLEAR_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE, delete, SERVICE_DELETE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE_VARIABLE, delete_variable, SERVICE_DELETE_VARIABLE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_DELETE_VARIABLE_REGEX, delete_variable_regex, SERVICE_DELETE_VARIABLE_REGEX_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_RESTORE_STATE, restore_state, SERVICE_RESTORE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SAVE_STATE, save_state, SERVICE_SAVE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SET_VARIABLE, set_variable, SERVICE_SET_VARIABLE_SCHEMA)

    return True


class SaverEntity(RestoreEntity):

    def __init__(self) -> None:
        self._entities_db = {}
        self._variables_db = {}
        self._attr_unique_id = f"{DOMAIN}.{DOMAIN}"

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
            tmp.pop(entity_id)
        self._entities_db = tmp
        self.schedule_update_ha_state()

    def delete_variable(self, variable: str) -> None:
        tmp = {**self._variables_db}
        tmp.pop(variable)
        self._variables_db = tmp
        self.schedule_update_ha_state()

    def delete_variable_regex(self, variable_regex: str) -> list[str]:
        variables = [variable for variable in self._variables_db if regex.match(variable_regex, variable)]
        tmp = {**self._variables_db}
        for variable in variables:
            tmp.pop(variable)
        self._variables_db = tmp
        self.schedule_update_ha_state()
        return variables

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
        self._variables_db = {**self._variables_db, variable: value}
        self.schedule_update_ha_state()

    @property
    def state_attributes(self) -> dict[str, Any]:
        return {
            "entities": self._entities_db,
            "variables": self._variables_db
        }

    @property
    def state(self) -> int:
        return len(self._entities_db) + len(self._variables_db)

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        if (
            state is not None
            and state.attributes is not None
            and "variables" in state.attributes and not isinstance(state.attributes["entities"], list)
            and "entities" in state.attributes and not isinstance(state.attributes["variables"], list)
        ):
            self._variables_db = state.attributes["variables"]
            self._entities_db = state.attributes["entities"]

    @staticmethod
    def convert_to_scene_params(saved_state: Any) -> dict[str, Any]:
        state = saved_state["state"] if isinstance(saved_state, dict) else saved_state.state
        attrs = saved_state["attributes"] if isinstance(saved_state, dict) else saved_state.attributes
        return {
            "state": state,
            **{attr_key: json.loads(json.dumps(attr_val)) for attr_key, attr_val in attrs.items()},
        }
