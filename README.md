# Simple MQTT bridge for Xiaomi Mi Temperature and Humidity Sensor with Bleutooth LE and the LCD display

This application lets you read sensor data from a Xiaomi Mi BluetoothLE Temperature and Humidity sensor and publish the readings on MQTT.

## Functionality 
It supports reading the different measurements from the sensor
- temperature
- humidity
- battery level

To use this application you will need a Bluetooth Low Energy dongle attached to your computer. You will also need a
Xiaomi Mi Temperature and Humidity sensor. 

## Dependecies
This application depends on the following library:
https://github.com/ratcashdev/mitemp.git

Library installation:
```bash
$ pip3 install git+https://github.com/ratcashdev/mitemp.git
```

## crontab
```
*/15 * * * * python3 /home/pi/mitemp/mitemp-mqtt.py 58:2D:34:xx:xx:xx -m -e -s mqtt-server
```
