# Waveshare UPS for Raspberry Pi

Home Assistant integration for the Waveshare UPS for Raspberry Pi.

## Description

This integration can be used to get information over i2c for the
Waveshare UPS for the Raspberry Pi.

### Entities Provided

#### Binary Sensors

* Battery State - whether the battery is charging or not.

#### Sensors

* Battery Level - percentage of power left in the battery
* Current
* Load Voltage - the voltage on V- (load side)
* Power
* PSU Voltage - Load Voltage + Shunt Voltage
* Shunt Voltage - voltage between V+ and V- across the shunt

## Setup

### <a id="ManualAdd"></a>`Add Integration` button

Clicking the `Add Integration` button will cause the integration to start
looking for available devices on i2c.

![Initial Setup Screen](images/step_user.png)

Once the detection process has finished the following information will be
required.

![Selection Screen](images/step_select.png)

* Name - friendly name for the configuration entry
* Address of the HAT - if only a single address was found it will be selected.
If multiple addresses are found the first is selected and you'll need to pick
the correct one to use.
* Version of the HAT - defaults to B. You should pick the version that you have.
* Update interval - defaults to 10s. Defines how often to query the UPS.

On successful set up the following screen will be seen detailing the device.

![Final Setup Screen](images/setup_finish.png)

## Configurable Options

It is possible to configure the following options for the integration.

![Configure Options](images/config_options.png)

* Update interval - defaults to 10s. Defines how often to query the UPS.
