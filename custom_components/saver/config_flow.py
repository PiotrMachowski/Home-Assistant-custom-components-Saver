from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class SaverFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._async_abort_entries_match()
        if user_input is not None:
            return self.async_create_entry(title="Saver", data=user_input)
        return self.async_show_form(step_id="user", last_step=True)

    async_step_import = async_step_user
