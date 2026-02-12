# HS2 Electrical Ground Support Equipment (EGSE)

The EGSE repository contains scripts for validating the functionality of HS-2's electrical system. To use the repository, first clone it and install the required dependencies:

```
pip install -r requirements.txt
```
---
## Project Goals

- Programmatically control a **DP800 Series Power Supply and a KEL103 electronic load**
- Execute time-based charge-discharge schedules (e.g. CC or CP profiles)
- Collect and log battery data (voltage, current, power, charge state)
- Implement safety cutoffs for low-voltage conditions
- Generate CSV outputs
- Run on a **Raspberry Pi**

## Hardware Overview

- **Electronic Load:** KEL103  
- **Programmable Power Supply:** DP800 Series PS  
- **Interface:** USB or RS-232  
- **Controller:** Raspberry Pi

## Software Overview

- **Language:** Python
- **Primary Libraries** [`py-kelctl`](https://pypi.org/project/py-kelctl/), [`pyvisa`](https://pypi.org/project/PyVISA/)
- **Data Format:** CSV

The `py-kelctl` package provides a high-level Python interface to the KEL103, allowing control of:
- Constant Current (CC)
- Constant Power (CP)
- Load enable/disable
- Voltage, current, and power measurements

Using this library avoids implementing low-level serial commands from scratch.

The `pyvisa` package provides a high-level Python interface for RIGOL SCPI communication, allowing control of:
- Voltage/current commands
- PS Protection limits
- PS enable/disable
- Voltage, current, and power measurements

Using this library avoids implementing low-level SCPI commands from scratch.

---

# Simulated Loading

To simulate a load on the battery pack, first connect your laptop/PC to the KEL103 E-load and the DP800 Series PS via USB, and connect
the positive battery pack terminal to the positive Power Supply and Eload terminals followed by the corresponding negative connections. 
For ground protection, please place a diode on the PS positive power lead connecting to the battery, ensuring the anode is directed 
towards the PS and the cathode flowing to the battery pack.

Use 'lsusb' on linux terminal to find the RIGOL USB ID, followed by 'ls /dev/ | grep "tty" to find the USB associated with the connected
Eload. Update these values in the last two lines of 'CircuitController/runCycles.py'

```
python3 -m CircuitController/runCycles.py
```

(On a non-Windows machine, `COM4` should be replaced with the serial port for that machine. On Linux, this may be `/dev/ttyACM0` or `/dev/ttyUSB0`)

# Simulated Charging

Coming soon...

# Verifying Inhibits

Coming soon...

# Verifying CDH Functionality

Coming soon...