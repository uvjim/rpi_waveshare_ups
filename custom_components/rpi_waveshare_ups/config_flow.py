"""Provide UI for configuring the integration."""

# region #-- imports --#
import asyncio
import logging
from typing import Any

import smbus2 as smbus
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import UnitOfElectricCurrent, UnitOfTime
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_FLOW_NAME,
    CONF_HAT_ADDRESS,
    CONF_HAT_BUS,
    CONF_HAT_TYPE,
    CONF_MIN_CHARGING,
    CONF_TITLE_PLACEHOLDERS,
    CONF_UPDATE_INTERVAL,
    DEF_HAT_TYPE,
    DEF_MIN_CHARGING,
    DEF_UPDATE_INTERVAL,
    DOMAIN,
)
from .logger import Logger

# endregion

_LOGGER: logging.Logger = logging.getLogger(__name__)

STEP_FINAL: str = "final"
STEP_INIT: str = "init"
STEP_SELECT: str = "select"
STEP_USER: str = "user"


async def _async_build_schema_with_user_input(
    step: str,
    user_input: dict,
    **kwargs,
) -> vol.Schema:
    """Build the input and validation schema for the config UI.

    :param step: the step we're in for a configuration or installation of the integration
    :param user_input: the data that should be used as defaults
    :param kwargs: additional data for the function
    :return: the schema including necessary restrictions, defaults, pre-selections etc.
    """
    schema: vol.Schema = vol.Schema({})
    if step == STEP_INIT:
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=user_input.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL),
                ): selector.NumberSelector(
                    config=selector.NumberSelectorConfig(
                        min=2,
                        mode=selector.NumberSelectorMode.BOX,
                        step=1,
                        unit_of_measurement=UnitOfTime.SECONDS,
                    )
                ),
                vol.Required(
                    CONF_MIN_CHARGING,
                    default=user_input.get(CONF_MIN_CHARGING, DEF_MIN_CHARGING),
                ): selector.NumberSelector(
                    config=selector.NumberSelectorConfig(
                        max=0,
                        mode=selector.NumberSelectorMode.BOX,
                        step=1,
                        unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
                    )
                ),
            }
        )
    elif step == STEP_SELECT:
        addresses: list[str] = list(map(hex, kwargs.get("addresses", [])))
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_FLOW_NAME,
                    default=user_input.get(
                        CONF_FLOW_NAME, user_input.get(CONF_FLOW_NAME, "")
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_HAT_ADDRESS,
                    default=user_input.get(CONF_HAT_ADDRESS, addresses[0]),
                ): selector.SelectSelector(
                    config=selector.SelectSelectorConfig(
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        multiple=False,
                        options=addresses,
                    )
                ),
                vol.Required(
                    CONF_HAT_TYPE,
                    default=user_input.get(CONF_HAT_TYPE, DEF_HAT_TYPE),
                ): selector.SelectSelector(
                    config=selector.SelectSelectorConfig(
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        multiple=False,
                        options=[
                            "a",
                            "b",
                            "d",
                        ],
                        translation_key="hat_type",
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=user_input.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL),
                ): selector.NumberSelector(
                    config=selector.NumberSelectorConfig(
                        min=2,
                        mode=selector.NumberSelectorMode.BOX,
                        step=1,
                        unit_of_measurement=UnitOfTime.SECONDS,
                    )
                ),
            }
        )

    return schema


class RpiWaveshareUpsConfigFlow(ConfigFlow, domain=DOMAIN):
    """ConfigFlow for new integration configuration."""

    task_detect: Any = None
    VERSION: int = 1

    def __init__(self) -> None:
        """Initialise."""
        self._addresses: dict[str, int] = {}
        self._data: dict = {}
        self._errors: dict[str, str] = {}
        self._logger: Logger = Logger()
        self._options: dict = {}

    def _detect_i2c_addresses(self) -> None:
        """Detect which addresses are available on i2c."""
        _LOGGER.debug(self._logger.format("entered"))

        i2c_buses: list[int] = [1, 0]
        errors_buses: int = 0
        for i2c_bus_no in i2c_buses:
            try:
                with smbus.SMBus(bus=i2c_bus_no) as bus:
                    for device_addr in range(3, 128):
                        try:
                            bus.write_byte(device_addr, 0)
                            self._addresses[device_addr] = i2c_bus_no
                        except IOError:
                            pass
            except FileNotFoundError:
                errors_buses += 1

        if errors_buses == len(i2c_buses):
            _LOGGER.debug(self._logger.format("i2c doesn't seem to be enabled"))
            raise AbortFlow(
                description_placeholders={"error_msg": " Check if I2C is enabled."},
                reason="no_comms",
            )

        _LOGGER.debug(self._logger.format("exited"))

    async def _async_task_detect(self) -> None:
        """Detect the devices attached to i2c."""
        _LOGGER.debug(self._logger.format("entered"))
        self._detect_i2c_addresses()
        await asyncio.sleep(0.5)
        self.hass.async_create_task(
            self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
        )
        _LOGGER.debug(self._logger.format("exited"))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return RpiWaveshareUpsConfigFlowOptions(config_entry)

    async def async_step_final(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle final step."""
        _LOGGER.debug(self._logger.format("entered, user_input: %s"), user_input)

        self.context[CONF_TITLE_PLACEHOLDERS] = {  # set the name of the flow
            CONF_FLOW_NAME: self._options.pop(CONF_FLOW_NAME)
        }
        self._options[CONF_HAT_BUS] = self._addresses.get(
            int(self._options.get(CONF_HAT_ADDRESS), 0)
        )

        return self.async_create_entry(
            title=self.context.get(CONF_TITLE_PLACEHOLDERS, {}).get(CONF_FLOW_NAME),
            data=self._data,
            options=self._options,
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection."""
        _LOGGER.debug(self._logger.format("entered, user_input: %s"), user_input)

        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_final()

        if len(self._addresses) == 0:
            _LOGGER.debug(self._logger.format("no i2c devices found"))
            raise AbortFlow(
                description_placeholders={"error_msg": ""}, reason="no_comms"
            )

        return self.async_show_form(
            step_id=STEP_SELECT,
            data_schema=await _async_build_schema_with_user_input(
                STEP_SELECT, self._options, addresses=self._addresses
            ),
            errors=self._errors,
            last_step=True,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        _LOGGER.debug(self._logger.format("entered, user_input: %s"), user_input)

        existing_entries: list[ConfigEntry] = self.hass.config_entries.async_entries(
            domain=DOMAIN
        )
        if len(existing_entries) > 0:
            raise AbortFlow(reason="already_configured")

        if not self.task_detect:
            _LOGGER.debug(self._logger.format("creating detection task"))
            self.task_detect = self.hass.async_create_task(
                target=self._async_task_detect()
            )
            return self.async_show_progress(
                step_id="user", progress_action="task_detect"
            )

        _LOGGER.debug(self._logger.format("running detection task"))
        await self.task_detect
        _LOGGER.debug(self._logger.format("returned from detection task"))

        return self.async_show_progress_done(next_step_id=STEP_SELECT)


class RpiWaveshareUpsConfigFlowOptions(OptionsFlow):
    """OptionsFlow for an existing integration configuration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise options flow."""
        self._config_entry: ConfigEntry = config_entry
        self._errors: dict = {}
        self._options: dict = dict(self._config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """First step in the options flow."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        return self.async_show_form(
            step_id=STEP_INIT,
            data_schema=await _async_build_schema_with_user_input(
                STEP_INIT, self._options
            ),
            errors=self._errors,
            last_step=True,
        )
