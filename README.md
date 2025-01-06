# MachineEye

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
import time

ser = serial.Serial('/dev/ttyAMA0', baudrate = 115200)
ser.close()

def screenPrint(text):
    ser.open()
    string = "T" + text + '\n'
    ser.write(string.encode('utf-8'))
    ser.close()

def gyroRead():
    ser.open()
    ser.write(b'G\n')

    val = ser.read_until().decode('utf-8')
    ser.close()
    return [round(int(n)/32767, 4) for n in val.split(" ")]


print(gyroRead())

print(gyroRead())

screenPrint("HELLO WORLD LENGTH TEST LENGTH TEST LENGTH TEST")

print(gyroRead())

```
`screenPrint(text)` prints `text` to the screen.

`gyroRead()` returns the accelerometer values, in units of G, in the form of `[x, y, z]`.

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

## Audio
Follow [this](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test) Adafruit tutorial to enable the i2s microphone, basically:

Edit the config file
```
sudo vi /boot/firmware/config.txt
```

Include the line[^1]
```
dtoverlay=googlevoicehat-soundcard
```

Reboot the Raspberry Pi
```
sudo reboot now
```

After that, check that `arecord -l` should list at least one audio device.

And then install [PyAudio](https://pypi.org/project/PyAudio/), [wave](https://docs.python.org/3/library/wave.html) and dependencies[^2]:
```
sudo apt-get install libasound-dev
sudo apt install python3-pyaudio
pip install wave
```

You can then run `audioTest.py`

[^1]: You might need to enable i2s at this step too 
[^2]: If the Pi is stuck connecting to the server, try disabling IPV6 with `sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1`

## PCB
The Gerber files for the 2 PCBs are available in the repository.
# Main PCB
![image](https://github.com/user-attachments/assets/96d62aed-9f64-471a-b109-d972d2fe5510)
![image](https://github.com/user-attachments/assets/b8ff2b6c-30d2-43d2-899a-3b29f449454f)

# Screen PCB
![image](https://github.com/user-attachments/assets/3c6bd3d3-f7e3-4fdd-b70b-1c893211f370)
![image](https://github.com/user-attachments/assets/df059964-da9c-4219-9013-34a18471b725)




# DEPRECIATED

## Wiring Diagram
The ESP32 communicates with the Raspberry Pi via hardware UART, here's the wiring diagram:
![wiring_uart](https://github.com/user-attachments/assets/9a67fa81-a5c6-4b69-893c-6a5d640088a3)
RX (receive) and TX (transmit) are flipped on both devices.

Here's the wiring diagram to the screen, with this [blog post](https://newscrewdriver.com/2022/09/23/formlabs-form-1-oled-pinout/) as the reference
![wiring_screen](https://github.com/user-attachments/assets/93e0ca3d-0a1d-45fe-8a0a-78bb18b68ae9)

