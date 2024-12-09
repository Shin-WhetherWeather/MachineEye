# MachineEye

## Wiring Diagram
The ESP32 communicates with the Raspberry Pi via hardware UART, here's the wiring diagram:
![wiring_uart](https://github.com/user-attachments/assets/9a67fa81-a5c6-4b69-893c-6a5d640088a3)

## Enable hardware UART on the Raspberry Pi
Enable hardware UART via the Raspberry Pi Configuration
![image](https://github.com/user-attachments/assets/fe54d104-5028-4c19-a6c7-4ead5176033b)
I run Pi OS headless so if this did not work try navigating to `/boot/firmware/config.txt` and include/uncomment the line `dtparam=uart0=on`

Alternatively, try running `sudo raspi-config` > `Interface Options` > `Serial Port`

Do not allow login shell through serial but enable the serial port hardware
```
The serial login shell is disabled
The serial interface is enabled 
```

## Python Code
The serial communication can be done through [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html) but can be done with any serial libraries.

Install pyserial `sudo pip install pyserial`

Example code `serialTest.py`
```python
import serial

ser = serial.Serial('/dev/ttyAMA0', baudrate = 115200)
ser.write(b"Hello from Pi5!\n")
ser.close()
```
You should see the new text on the screen after running `python3 serialTest.py`!

## Debugging
The serial port is assigned to `/dev/ttyAMA0` on my device, if it does not work try running `dmesg | grep tty` on the command line and you should see something like this:
```
...
107d001000.serial: ttyAMA10 at MMIO 0x107d001000 (irq = 15, base_baud = 0) is a PL011 rev2
107d50c000.serial: ttyS0 at MMIO 0x107d50c000 (irq = 33, base_baud = 6000000) is a Broadcom BCM7271 UART
serial serial0: tty port ttyS0 registered
1f00030000.serial: ttyAMA0 at MMIO 0x1f00030000 (irq = 125, base_baud = 0) is a PL011 AXI
...
```
Try replacing `ttyAMA0` with the different listed devices.


`SSD1305_test_basic.ino` is an Arduino sketch for the ESP32.




