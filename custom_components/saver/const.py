import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.components.light import ATTR_TRANSITION, VALID_TRANSITION

import voluptuous as vol

DOMAIN = 'saver'
NAME = 'Saver'

SAVER_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({})
    },
    extra=vol.ALLOW_EXTRA
)

CONF_DELETE_AFTER_RUN = 'delete_after_run'
CONF_RESTORE_SCRIPT = 'restore_script'
CONF_SCRIPT = 'script'
CONF_VALUE = 'value'
CONF_USE_CURRENT_TIME = 'use_current_time'
CONF_REGEX = 'regex'
CONF_ENTITY_ID_REGEX = CONF_ENTITY_ID + '_regex'

SERVICE_CLEAR = 'clear'
SERVICE_CLEAR_SCHEMA = vol.Schema({
})

SERVICE_DELETE = 'delete'
SERVICE_DELETE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids
})

SERVICE_DELETE_REGEX = 'delete_regex'
SERVICE_DELETE_REGEX_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID_REGEX): cv.string
})

SERVICE_DELETE_VARIABLE = 'delete_variable'
SERVICE_DELETE_VARIABLE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string
})

SERVICE_DELETE_VARIABLE_REGEX = 'delete_variable_regex'
SERVICE_DELETE_VARIABLE_REGEX_SCHEMA = vol.Schema({
    vol.Required(CONF_REGEX): cv.string
})

SERVICE_RESTORE_STATE = 'restore_state'
SERVICE_RESTORE_STATE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_DELETE_AFTER_RUN, default=True): cv.boolean,
    vol.Optional(ATTR_TRANSITION, default=None): vol.Any(VALID_TRANSITION, None),
})

SERVICE_SAVE_STATE = 'save_state'
SERVICE_SAVE_STATE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids
})

SERVICE_SET_VARIABLE = 'set_variable'


def _validate_set_variable(config):
    """Ensure either 'value' or 'use_current_time: true' is provided."""
    if CONF_VALUE not in config and not config.get(CONF_USE_CURRENT_TIME, False):
        raise vol.Invalid("Either 'value' or 'use_current_time: true' must be provided")
    return config


SERVICE_SET_VARIABLE_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_VALUE): cv.string,
        vol.Optional(CONF_USE_CURRENT_TIME, default=False): cv.boolean,
    }),
    _validate_set_variable,
)
