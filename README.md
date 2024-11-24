[![GitHub Release][badge_github_release_version]][github_release_link]
![GitHub Downloads (latest release)][badge_github_release_downloads]
[![GitHub Pre-release][badge_github_prerelease_version]][github_prerelease_link]
![GitHub Downloads (pre-release)][badge_github_prerelease_downloads]

# Waveshare UPS for Raspberry Pi

Home Assistant integration for the Waveshare UPS for Raspberry Pi.

# Disclaimer

I have no real knowledge of how the HAT works or necessarily what the numbers mean.
The integration was only created so that I could create an automation to safely shut
the Pi down in the event of an extended power outage.

# Description

This integration can be used to get information over i2c for the
Waveshare UPS for the Raspberry Pi.
The integration assumes that you have followed the instructions for
enabling i2c on your Raspberry Pi. These instructions will differ
depending on how you are running Home Assistant.

If you are running Home Assistant OS see
[here](https://www.home-assistant.io/common-tasks/os/#enable-i2c).

If you are running Raspberry Pi OS see
[here](https://www.raspberrypi.com/documentation/computers/configuration.html).

# Installation

The integration can be installed using [HACS](https://hacs.xyz/).  The
integrations is not available in the default repositories, so you will need to
add the URL of this repository as a custom repository to HACS (see
[here](https://hacs.xyz/docs/faq/custom_repositories)).

Alternatively you can use the button below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=uvjim&repository=rpi_waveshare_ups&category=Integration)

# Entities Provided

## Binary Sensors

| Name | Enabled by default | Additional Information | Comments |
|---|:---:|---|---|
| Battery State | ✔️ | Whether the battery is charging or not | This is based on the current being >= the minimum charging value |

## Sensors

| Name | Enabled by default | Additional Information | Comments |
|---|:---:|---|---|
| Battery Level | ✔️ | Percentage of power left in the battery |  |
| Current | ✔️ |  |  |
| Load Voltage | ✔️ | Voltage on V- (load side) |  |
| Power | ✔️ |  |  |
| PSU Voltage | ✔️ | Load Voltage + Shunt Voltage |  |
| Shunt Voltage | ✔️ | Voltage between V+ and V- across the shunt |  |

# Setup

Clicking the `Add Integration` button, in `Settings -> Device & Services`, will
cause the integration to start looking for available devices on i2c.

![Initial Setup Screen](images/step_user.png)

Once the detection process has finished the following information will be
required.

![Selection Screen](images/step_select.png)

* __Name__ - friendly name for the configuration entry
* __Address of the HAT__ - if only a single address was found it will be
selected. If multiple addresses are found the first is selected and you'll
need to pick the correct one to use.
* __Version of the HAT__ - defaults to B. You should pick the version that you
have.
* __Update interval__ - defaults to 10s. Defines how often to query the UPS.

On successful set up the following screen will be seen detailing the device.

![Final Setup Screen](images/setup_finish.png)

# Configurable Options

It is possible to configure the following options for the integration.

![Configure Options](images/config_options.png)

* __Update interval__ - defaults to 10s. Defines how often to query the UPS.
* __Mimimum current value for charging__ - defaults to -100mA. In my usage I've
found that whilst the documentation for the HAT states a negative current
means that the Pi is being powered by the batteries it can drop below 0 on
normal use. This value allows you to mitigate this.

[badge_github_release_version]: https://img.shields.io/github/v/release/uvjim/rpi_waveshare_ups?display_name=release&style=for-the-badge&logoSize=auto
[badge_github_release_downloads]: https://img.shields.io/github/downloads/uvjim/rpi_waveshare_ups/latest/total?style=for-the-badge&label=downloads%40release
[badge_github_prerelease_version]: https://img.shields.io/github/v/release/uvjim/rpi_waveshare_ups?include_prereleases&display_name=release&style=for-the-badge&logoSize=auto&label=pre-release
[badge_github_prerelease_downloads]: https://img.shields.io/github/downloads-pre/uvjim/rpi_waveshare_ups/latest/total?style=for-the-badge&label=downloads%40pre-release
[github_release_link]: https://github.com/uvjim/rpi_waveshare_ups/releases/latest
[github_prerelease_link]: https://github.com/uvjim/rpi_waveshare_ups/releases
