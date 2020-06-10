import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.core import Context

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.script import Script
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.const import CONF_ENTITY_ID

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'saver'
CONF_RESTORE_SCRIPT = 'restore_script'

SERVICE_SAVE_ATTRIBUTE = 'save_state'
SERVICE_SAVE_ATTRIBUTE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id
})

SERVICE_RESTORE_ATTRIBUTE = 'restore_state'
SERVICE_RESTORE_ATTRIBUTE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_RESTORE_SCRIPT): cv.SCRIPT_SCHEMA
})


def setup(hass, config):
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    saver_entity = SaverEntity(config[DOMAIN])
    component.add_entities([saver_entity])

    def save_state(call):
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        saver_entity.save(entity_id)

    def restore_state(call):
        data = call.data
        entity_id = data[CONF_ENTITY_ID]
        restore_script = data[CONF_RESTORE_SCRIPT]
        saver_entity.restore(entity_id, restore_script)

    hass.services.register(DOMAIN, SERVICE_SAVE_ATTRIBUTE, save_state, SERVICE_SAVE_ATTRIBUTE_SCHEMA)
    hass.services.register(DOMAIN, SERVICE_RESTORE_ATTRIBUTE, restore_state, SERVICE_RESTORE_ATTRIBUTE_SCHEMA)

    return True


class SaverEntity(Entity):

    def __init__(self, hass):
        self._hass = hass
        self._db = {}

    @property
    def name(self):
        return DOMAIN

    def save(self, entity_id):
        self._db[entity_id] = self.hass.states.get(entity_id)
        self.schedule_update_ha_state()

    def restore(self, entity_id, restore_script):
        if entity_id not in self._db:
            return
        old = self._db[entity_id]
        variables = SaverEntity.convert_to_variables(old)
        self._db.pop(entity_id)
        script = Script(self.hass, restore_script)
        script.run(variables=variables, context=Context())
        self.schedule_update_ha_state()

    @property
    def state_attributes(self):
        return {"entities": self._db}

    @property
    def state(self):
        return len(self._db)

    @staticmethod
    def convert_to_variables(state):
        variables = {"state": state.state}
        for attr in state.attributes:
            variables[f"attributes_{attr}"] = state.attributes[attr]
        return variables
