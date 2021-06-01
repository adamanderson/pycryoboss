# pycryoboss

## Usage
Instantiate a client:
```
from client import CryobossClient
client = CryobossClient('192.168.1.3', 60880)
```
Get data from CryoBoss:
```
data = client.get_data()
```
Update the temperature PID setpoint:
```
client.set_pid(0.14)
```
Note that the following guardrails are in place for changing the PID setpoint:
* Without a voltage divider installed on the PID control unit input, do now allow setpoints above 0.15 K.
* Do not allow the setpoint to be increased more than 0.02 K above the current FAA temperature.
* Do not allow the setpoint to be increased if the magnet current is > 8 A or if the power supply voltage is > 14 V.
* Do not allow the setpoint to be increased if the temperature is increasing faster than 0.001 K per 10 sec.
* Always allow the setpoint to be decreased (this may not always be a good idea!).