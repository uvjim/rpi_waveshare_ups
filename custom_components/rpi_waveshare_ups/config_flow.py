"""Provide UI for configuring the integration."""

# region #-- imports --#
import logging

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import AbortFlow, FlowResult

from .const import DOMAIN
from .ina219.INA219 import INA219
from .logger import Logger

# endregion

_LOGGER: logging.Logger = logging.getLogger(__name__)

STEP_USER: str = "user"
STEP_FINAL: str = "final"


class RpiWaveshareUpsConfigFlow(ConfigFlow, domain=DOMAIN):
    """ConfigFlow for new integration configuration."""

    def __init__(self) -> None:
        """Initialise."""
        self._errors: dict[str, str] = {}
        self._logger: Logger = Logger()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initiated by the user."""
        _LOGGER.debug(self._logger.format("entered, user_input: %s"), user_input)

        if user_input is None:
            try:  # attempt to connect to UPS
                _ = INA219(addr=0x42)
            except FileNotFoundError:
                raise AbortFlow(reason="no_i2c") from None
        else:
            return await self.async_step_final()

        return self.async_show_form(
            step_id=STEP_USER,
            data_schema={},
            errors=self._errors,
            last_step=False,
        )

    async def async_step_final(self, user_input=None) -> FlowResult:
        """Handle final step."""
        _LOGGER.debug(self._logger.format("entered, user_input: %s"), user_input)

        _LOGGER.debug(self._logger.format("exited"))
