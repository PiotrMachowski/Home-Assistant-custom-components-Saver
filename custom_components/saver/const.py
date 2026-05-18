import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.components.light import ATTR_TRANSITION, VALID_TRANSITION

import voluptuous as vol

DOMAIN = "saver"
NAME = "Saver"

SAVER_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({})
    },
    extra=vol.ALLOW_EXTRA
)

SAVER_ENTITY_ID = f"{DOMAIN}.{DOMAIN}"
ATTR_VARIABLES = "variables"
ATTR_ENTITIES = "entities"

CONF_DELETE_AFTER_RUN = "delete_after_run"
CONF_RESTORE_SCRIPT = "restore_script"
CONF_SCRIPT = "script"
CONF_VALUE = "value"
CONF_VALUE_ENTITY = "value_entity"
CONF_USE_CURRENT_TIME = "use_current_time"
CONF_REGEX = "regex"
CONF_ENTITY_ID_REGEX = CONF_ENTITY_ID + "_regex"

SERVICE_CLEAR = "clear"
SERVICE_CLEAR_SCHEMA = vol.Schema({
})

SERVICE_DELETE = "delete"
SERVICE_DELETE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids
})

SERVICE_DELETE_REGEX = "delete_regex"
SERVICE_DELETE_REGEX_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID_REGEX): cv.string
})

SERVICE_DELETE_VARIABLE = "delete_variable"
SERVICE_DELETE_VARIABLE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string
})

SERVICE_DELETE_VARIABLE_REGEX = "delete_variable_regex"
SERVICE_DELETE_VARIABLE_REGEX_SCHEMA = vol.Schema({
    vol.Required(CONF_REGEX): cv.string
})

SERVICE_RESTORE_STATE = "restore_state"
SERVICE_RESTORE_STATE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_DELETE_AFTER_RUN, default=True): cv.boolean,
    vol.Optional(ATTR_TRANSITION, default=None): vol.Any(VALID_TRANSITION, None),
})

SERVICE_SAVE_STATE = "save_state"
SERVICE_SAVE_STATE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_ids
})
SERVICE_SET_VARIABLE = "set_variable"

def _validate_set_variable(config):
    """Ensure exactly one of 'value', 'value_entity' or 'use_current_time' is provided."""
    sources = sum([
        CONF_VALUE in config,
        CONF_VALUE_ENTITY in config,
        config.get(CONF_USE_CURRENT_TIME, False),
        ])
    if sources == 0:
        raise vol.Invalid(
            "One of 'value', 'value_entity' or 'use_current_time: true' must be provided")
    if sources > 1:
        raise vol.Invalid(
            "Only one of 'value', 'value_entity' or 'use_current_time: true' can be used")
    return config


SERVICE_SET_VARIABLE_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_VALUE): cv.string,
        vol.Optional(CONF_VALUE_ENTITY): cv.entity_id,
        vol.Optional(CONF_USE_CURRENT_TIME, default=False): cv.boolean,
    }),
    _validate_set_variable,
)

# Condition-related constants
CONF_VARIABLE = "variable"
CONF_COMPARISON = "comparison"
CONF_COMPARE_TO = "compare_to"
CONF_ABOVE = "above"
CONF_BELOW = "below"

CONDITION_NAME_TIME_ELAPSED = "time_elapsed"
CONDITION_NAME_COMPARE_VALUE = "compare_value"
CONDITION_NAME_COMPARE_TIME = "compare_time"

CMP_EQ = "eq"
CMP_NEQ = "neq"
CMP_GT = "gt"
CMP_LT = "lt"
CMP_GTE = "gte"
CMP_LTE = "lte"

CMP_TIME_AFTER = "after"
CMP_TIME_BEFORE = "before"
CMP_TIME_AFTER_NOW = "after_now"

IGNORED_ATTRIBUTES = ["last_triggered"]
