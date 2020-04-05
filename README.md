# MicroPython-WaterSensor

This simple project uses a NodeMCU - Aka Espressif ESP8266 - and cheap chinese water flow sensor YF-B1 and MicroPython.

My sensor supports multiple sensors, uses Wifi and MQTT to publish status updates.

## Install MicroPython

I will quickly cover the steps for ESP8266. For more information, refer to the official documentation at https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html.

### Install ESPTOOL

`esptool` is used to flash the NodeMCU/ESP8266 with the MicroPython firmware. For this project, no need to rebuild MicroPython.

```
pip install --user esptool
```

### Erase the NodeMCU flash
First, the flash needs to be erased (on my Mac, the usb-serial port is `/dev/cu.SLAB_USBtoUART`):
```
esptool.py --port /dev/cu.SLAB_USBtoUART erase_flash
```

### Download the Firmware from MicroPython website.

http://micropython.org/download

### Flash the firmware
```
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 esp8266-20170108-v1.8.7.bin
```

At this stage, you should have a working MicroPython ESP8266 board. You can attach to the Python shell using `screen` for example:

```
/dev/ttyUSB0 115200
```

## Upload the software
The software is composed of 2 files, `boot.py` and `main.py`, similarly as Arduino sketch composed of `setup()` and `loop()` functions.

To upload the software, you need `ampy`.

```
pip install adafruit-ampy
```

Using `ampy`, you can interact with the board. Keep in mind that as any serial port, it cannot be accessed by multiple software at the same time (eg. `screen`).

As explained in the documentation, `MicroPython` formats the flash as `FAT` and hosts software.

To list files on the FAT partition:
```
ampy --port /dev/cu.SLAB_USBtoUART --baud 115200 ls
```

### Use my program

To use my program, you will need to upload `main.py` and `config.json`.

```
{
    "wifi": {
        "SSID" : "MyIoTSSID",
        "PSK" : "SuperSecretKey"
    },
    "mqtt": {
        "broker" : "mqttbroker",
        "client" : "wtr-sens",
        "prefix" : "wtr/",
        "t_status" : "status",
        "t_cons" : "consumption"
    },
    "pulsesPerLitre" : 2500,
    "sensors": [
        { "name": "hot", "pin": 14 },
        { "name": "cold", "pin": 15 }
    ],
    "statusLed": 16
}
```

Upload the two files:
```
ampy --port /dev/cu.SLAB_USBtoUART --baud 115200 put main.py
ampy --port /dev/cu.SLAB_USBtoUART --baud 115200 put config.json
```

The sensor regularly saves its state to the flash to be able to resume on power failure.

If you want to monitor the sensor, use screen. To soft reboot and reload the software, you can issue a `CTRL+D`.
