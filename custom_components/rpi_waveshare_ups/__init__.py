"""RPi Waveshare UPS Integration."""

# region #-- imports --#
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_COORDINATOR,
    CONF_HAT_ADDRESS,
    CONF_HAT_BUS,
    CONF_HAT_TYPE,
    CONF_UPDATE_INTERVAL,
    DEF_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .ina219.INA219_AB import INA219_AB
from .ina219.INA219_D import INA219_D
from .logger import Logger

# endregion

_LOGGER = logging.getLogger(__name__)


class UPS:
    """Represenation of the UPS device."""

    def __enter__(self):
        """Enter magic method."""
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Exit magic method."""
        self._close()

    def __init__(self, i2c_bus: int, i2c_address: int, is_model_d: bool) -> None:
        """Initialise."""
        _LOGGER.debug("init with is_model_d: %s", is_model_d)
        self._is_model_d = is_model_d
        self._current: float | None = None
        self._ina219: INA219_D | INA219_AB = INA219_D(addr=i2c_address, i2c_bus=i2c_bus) if is_model_d else INA219_AB(addr=i2c_address, i2c_bus=i2c_bus)
        self._load_voltage: float | None = None
        self._power: float | None = None
        self._shunt_voltage: float | None = None
        self.gather_details()

    def _close(self) -> None:
        """Close the bus connection."""
        self._ina219.bus.close()

    def gather_details(self) -> None:
        """Retrieve the required details for the UPS."""
        self._current = -self._ina219.get_current_ma()
        self._load_voltage = self._ina219.get_bus_voltage_v()
        self._power = self._ina219.get_power_w()
        self._shunt_voltage = self._ina219.get_shunt_voltage_mv() / 1000

    @property
    def battery_percentage(self) -> float:
        """Get the battery percentage."""
        ret: float = ((self._load_voltage - 3) / 1.2 * 100) if self._is_model_d else ((self._load_voltage - 6) / 2.4 * 100)
        ret = min(ret, 100)
        ret = max(ret, 0)

        return ret

    @property
    def current(self) -> float:
        """Get the current in mA."""
        return self._current

    @property
    def load_voltage(self) -> float:
        """Get the load voltage (voltage on V-)."""
        return self._load_voltage

    @property
    def power(self) -> float:
        """Get the power in W."""
        return self._power

    @property
    def shunt_voltage(self) -> float:
        """Get the shunt voltage (voltage between V+ and V- across the shunt)."""
        return self._shunt_voltage


class UPSEntity(CoordinatorEntity):
    """Representation of a UPS entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{self._config_entry.options.get(CONF_HAT_BUS)}"
                    f"::{self._config_entry.options.get(CONF_HAT_ADDRESS)}",
                )
            },
            manufacturer="Waveshare",
            model=f"Model {self._config_entry.options.get(CONF_HAT_TYPE, '').upper()}",
            name=self._config_entry.title,
        )


async def _async_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """React to options being updated."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Initialise the ConfigEntry."""
    log_formatter = Logger(unique_id=config_entry.unique_id)
    _LOGGER.debug(log_formatter.format("entered"))

    # region #-- initialise memory storage --#
    hass.data.setdefault(DOMAIN, {})
    # endregion

    # region #-- setup the coordinator --#
    async def _async_data_coordinator_update() -> UPS:
        with UPS(
            i2c_bus=config_entry.options.get(CONF_HAT_BUS),
            i2c_address=int(config_entry.options.get(CONF_HAT_ADDRESS), 0),
            is_model_d=(config_entry.options.get(CONF_HAT_TYPE, 'A').upper() == 'D'),
        ) as ups_data:
            pass

        return ups_data

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_data_coordinator_update,
        update_interval=timedelta(
            seconds=config_entry.options.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL)
        ),
    )
    hass.data[DOMAIN][CONF_COORDINATOR] = coordinator
    await coordinator.async_config_entry_first_refresh()
    # endregion

    # region #-- setup the platforms --#
    _LOGGER.debug(log_formatter.format("setting up platforms: %s"), PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    # endregion

    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    _LOGGER.debug(log_formatter.format("exited"))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)
    return unloaded
