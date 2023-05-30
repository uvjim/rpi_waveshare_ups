# pylint: disable=invalid-name
"""Library interacting with the INA219 device."""

# Originally provided here:
# https://github.com/waveshare/UPS-Power-Module/blob/master/ups_display/ina219.py

# region #-- imports --#
from enum import Enum
from typing import Sequence

import smbus2 as smbus

# endregion


class Registers(Enum):
    """Register addresses."""

    CONFIG = 0x00  # Config Register (R/W)
    SHUNTVOLTAGE = 0x01  # SHUNT VOLTAGE REGISTER (R)
    BUSVOLTAGE = 0x02  # BUS VOLTAGE REGISTER (R)
    POWER = 0x03  # POWER REGISTER (R)
    CURRENT = 0x04  # CURRENT REGISTER (R)
    CALIBRATION = 0x05  # CALIBRATION REGISTER (R/W)


class BusVoltageRange(Enum):
    """Constants for ``bus_voltage_range``."""

    RANGE_16V = 0x00  # set bus voltage range to 16V
    RANGE_32V = 0x01  # set bus voltage range to 32V (default)


class Gain(Enum):
    """Constants for ``gain``."""

    DIV_1_40MV = 0x00  # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV = 0x01  # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV = 0x02  # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV = 0x03  # shunt prog. gain set to /8, 320 mV range


class ADCResolution(Enum):
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``."""

    ADCRES_9BIT_1S = 0x00  # 9bit,   1 sample,     84us
    ADCRES_10BIT_1S = 0x01  # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S = 0x02  # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S = 0x03  # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S = 0x09  # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S = 0x0A  # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S = 0x0B  # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S = 0x0C  # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S = 0x0D  # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S = 0x0E  # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S = 0x0F  # 12bit, 128 samples, 68.10ms


class Mode(Enum):
    """Constants for ``mode``."""

    POWERDOW = 0x00  # power down
    SVOLT_TRIGGERED = 0x01  # shunt voltage triggered
    BVOLT_TRIGGERED = 0x02  # bus voltage triggered
    SANDBVOLT_TRIGGERED = 0x03  # shunt and bus voltage triggered
    ADCOFF = 0x04  # ADC off
    SVOLT_CONTINUOUS = 0x05  # shunt voltage continuous
    BVOLT_CONTINUOUS = 0x06  # bus voltage continuous
    SANDBVOLT_CONTINUOUS = 0x07  # shunt and bus voltage continuous


class INA219:
    """Interact with INA219."""

    def __init__(self, i2c_bus: int = 1, addr: int = 0x40) -> None:
        """Initialise."""
        self.bus: smbus.SMBus = smbus.SMBus(i2c_bus)
        self.addr: int = addr

        # Set chip to known config values to start
        self._cal_value: int | None = None
        self._current_lsb: float | None = None
        self._power_lsb: float | None = None

        self.set_calibration_32v_2a()

    def read(self, address: int) -> int:
        """Read block data from i2c."""
        data: list[int] = self.bus.read_i2c_block_data(self.addr, address, 2)
        return (data[0] * 256) + data[1]

    def write(self, address: int, data: Sequence[int]) -> None:
        """Write block data to i2c."""
        temp: Sequence[int] = [0, 0]
        temp[1] = data & 0xFF
        temp[0] = (data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr, address, temp)

    def set_calibration_32v_2a(self) -> None:
        """Configure to INA219 to be able to measure up to 32V and 2A of current. Counter overflow occurs at 3.2A.

        ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 32V             (Assumes 32V, can also be set to 16V)
        # VSHUNT_MAX = 0.32          (Assumes Gain 8, 320mV, can also be 0.16, 0.08, 0.04)
        # RSHUNT = 0.1               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 3.2A

        # 2. Determine max expected current
        # MaxExpected_I = 2.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.000061              (61uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0,000488              (488uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.0001 (100uA per bit)
        self._current_lsb = 0.1  # Current LSB = 100uA per bit

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 4096 (0x1000)

        self._cal_value = 4096

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = 0.002  # Power LSB = 2mW per bit

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 3.2767A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.32V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 3.2 * 32V
        # MaximumPower = 102.4W

        # Set Calibration register to 'Cal' calculated above
        self.write(Registers.CALIBRATION, self._cal_value)

        # Set Config register to take into account the settings above
        bus_adc_resolution: int = ADCResolution.ADCRES_12BIT_32S
        bus_voltage_range = BusVoltageRange.RANGE_32V
        gain = Gain.DIV_8_320MV
        mode = Mode.SANDBVOLT_CONTINUOUS
        shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S

        config: Sequence[int] = (
            bus_voltage_range << 13
            | gain << 11
            | bus_adc_resolution << 7
            | shunt_adc_resolution << 3
            | mode
        )

        self.write(Registers.CONFIG, config)

    def get_shunt_voltage_mv(self) -> float:
        """Get the voltage between V+ and V- across the shunt."""
        self.write(Registers.CALIBRATION, self._cal_value)
        value = self.read(Registers.SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def get_bus_voltage_v(self) -> float:
        """Get the voltage on V- (load side)."""
        self.write(Registers.CALIBRATION, self._cal_value)
        self.read(Registers.BUSVOLTAGE)
        return (self.read(Registers.BUSVOLTAGE) >> 3) * 0.004

    def get_current_ma(self) -> float:
        """Get the current in mA."""
        value = self.read(Registers.CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def get_power_w(self) -> float:
        """Get the power in W."""
        self.write(Registers.CALIBRATION, self._cal_value)
        value = self.read(Registers.POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb
