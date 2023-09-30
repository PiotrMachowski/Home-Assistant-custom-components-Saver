import logging
from typing import Any, Callable, Sequence

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.script import Script, SCRIPT_MODE_PARALLEL
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

    def execute(call: ServiceCall) -> None:
        data = call.data
        script = data[CONF_SCRIPT]
        saver_entity.execute(script)
        hass.bus.fire('event_saver_executed', {'script': script})

    def restore_state(call: ServiceCall) -> None:
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        restore_script = data[CONF_RESTORE_SCRIPT]
        should_delete = data[CONF_DELETE_AFTER_RUN]
        saver_entity.restore(entity_id, restore_script, should_delete)
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
    hass.services.register(DOMAIN, SERVICE_EXECUTE, execute, SERVICE_EXECUTE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_RESTORE_STATE, restore_state, SERVICE_RESTORE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SAVE_STATE, save_state, SERVICE_SAVE_STATE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_SET_VARIABLE, set_variable, SERVICE_SET_VARIABLE_SCHEMA)

    return True


class SaverEntity(RestoreEntity):

    def __init__(self) -> None:
        self._entities_db = {}
        self._variables_db = {}

    @property
    def name(self) -> str:
        return DOMAIN

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

    def execute(self, script: Sequence[dict[str, Any]]) -> None:
        script = Script(self.hass, script, self.name, DOMAIN, script_mode=SCRIPT_MODE_PARALLEL)
        variables = {}
        variables.update(self._variables_db)
        for entity_id in self._entities_db:
            variables.update(SaverEntity.convert_to_variables(self._entities_db[entity_id], entity_id))
        script.run(variables=variables, context=Context())
        self.schedule_update_ha_state()

    def restore(self, entity_id: str, restore_script: Sequence[dict[str, Any]], delete: bool) -> None:
        if entity_id not in self._entities_db:
            return
        old = self._entities_db[entity_id]
        variables = SaverEntity.convert_to_variables(old)
        if delete:
            tmp = {**self._entities_db}
            tmp.pop(entity_id)
            self._entities_db = tmp
        script = Script(self.hass, restore_script, self.name, DOMAIN, script_mode=SCRIPT_MODE_PARALLEL)
        script.run(variables=variables, context=Context())
        self.schedule_update_ha_state()

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
    def convert_to_variables(state: Any, entity_id: str | None = None) -> dict:
        prefix = ""
        state_val = state["state"] if isinstance(state, dict) else state.state
        attrs = state["attributes"] if isinstance(state, dict) else state.attributes
        if entity_id is not None:
            prefix = f"{entity_id}_".replace(".", "_")
        variables = {f"{prefix}state": state_val}
        for attr in attrs:
            variables[f"{prefix}attr_{attr}"] = attrs[attr]
        return variables
