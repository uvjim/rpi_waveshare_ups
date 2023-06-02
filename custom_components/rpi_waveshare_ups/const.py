"""Constants."""

# region #-- imports --#
from homeassistant.const import Platform

# endregion


CONF_COORDINATOR: str = "coordinator"
CONF_FLOW_NAME: str = "name"
CONF_HAT_ADDRESS: str = "hat_address"
CONF_HAT_BUS: str = "hat_bus"
CONF_HAT_TYPE: str = "hat_type"
CONF_MIN_CHARGING: str = "min_charging"
CONF_TITLE_PLACEHOLDERS: str = "title_placeholders"
CONF_UPDATE_INTERVAL: str = "update_interval"

DEF_HAT_TYPE: str = "a"
DEF_MIN_CHARGING: float = -100
DEF_UPDATE_INTERVAL: int = 10

DOMAIN: str = "rpi_waveshare_ups"

PLATFORMS: list[str] = [Platform.BINARY_SENSOR, Platform.SENSOR]
