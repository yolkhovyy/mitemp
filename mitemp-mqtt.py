#!/usr/bin/env python3
import argparse
import re
import getmac
import paho.mqtt.publish as publish

from btlewrap import BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

MAC_ADDRESS = r'(?i)[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'

def valid_mac(mac):
    """ Validates MAC address """
    regex_mac_address = re.compile(MAC_ADDRESS)
    if regex_mac_address.match(mac):
        return mac
    raise argparse.ArgumentTypeError('Invalid MAC address {}'.format(mac))

def mac_to_eui64(mac):
    """ Converts MAC address to EUI64 """
    if valid_mac(mac):
        eui64 = re.sub(r'[.:-]', '', mac).lower()
        eui64 = eui64[0:6] + 'fffe' + eui64[6:]
        eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]
        return eui64
    return None

MI_TEMP_V1 = r'(?i)58:2D:34:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'
MI_TEMP_V2 = r'(?i)4C:65:A8:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'

def valid_mitemp_mac(mac):
    """ Validates MiTemp MAC address """
    regex_v1 = re.compile(MI_TEMP_V1)
    regex_v2 = re.compile(MI_TEMP_V2)
    if regex_v1.match(mac) or regex_v2.match(mac):
        return mac
    raise argparse.ArgumentTypeError('Invalid MiTemp MAC address {}'.format(mac))

BACKEND = None

def get_backend(args):
    """ Returns Bluetooth backend """
    if args.backend == 'gatttool':
        backend = GatttoolBackend
    elif args.backend == 'bluepy':
        backend = BluepyBackend
    elif args.backend == 'pygatt':
        backend = PygattBackend
    else:
        raise Exception('unknown backend: {}'.format(args.backend))
    return backend

PARSER = argparse.ArgumentParser()
PARSER.add_argument('macs', type=valid_mitemp_mac, nargs="*")
PARSER.add_argument('-s', '--server', default='localhost')
PARSER.add_argument('-p', '--port', default=1883)
PARSER.add_argument('-b', '--backend', choices=['gatttool', 'bluepy', 'pygatt'], default='gatttool')
PARSER.add_argument('-d', '--devinfo', action='store_true')
PARSER.add_argument('-e', '--health', action='store_true')
PARSER.add_argument('-m', '--measurements', action='store_true')

ARGS = PARSER.parse_args()
BACKEND = get_backend(ARGS)

SELF_MAC = getmac.get_mac_address()
SELF_EUI64 = mac_to_eui64(valid_mac(SELF_MAC))
MQTT_CLIENT_ID = "mitemp-mqtt-" + SELF_EUI64

for mitemp_mac in ARGS.macs:
    mitemp_eui64 = mac_to_eui64(mitemp_mac)
    topic_device_info = 'OpenCH/Gw/{}/TeHu/{}/Evt/DeviceInfo'.format(SELF_EUI64, mitemp_eui64)
    topic_health = 'OpenCH/Gw/{}/TeHu/{}/Evt/Health'.format(SELF_EUI64, mitemp_eui64)
    topic_measurements = 'OpenCH/Gw/{}/TeHu/{}/Evt/Status'.format(SELF_EUI64, mitemp_eui64)
    
    poller = MiTempBtPoller(mitemp_mac, BACKEND)
    msgs = []

    try:
        if ARGS.devinfo:
            payload = '{{"name":"{}","firmware_version":"{}"}}' \
                .format( \
                    poller.name(), \
                    poller.firmware_version())
            msgs.append({'topic': topic_device_info, 'payload': payload})     

        if ARGS.health:
            payload = '{{"measurements":[{{"name":"battery","value":{},"units":"%"}}]}}' \
                .format( \
                    poller.parameter_value(MI_BATTERY))
            msgs.append({'topic': topic_health, 'payload': payload})     

        if ARGS.measurements:
            payload = '{{"measurements":[{{"name":"temperature","value":{},"units":"℃"}},{{"name":"humidity","value":{},"units":"%"}}]}}' \
                .format( \
                    poller.parameter_value(MI_TEMPERATURE), \
                    poller.parameter_value(MI_HUMIDITY))
            msgs.append({'topic': topic_measurements, 'payload': payload}) 

    except Exception as ex:
        print(mitemp_mac + ' mitemp sensor failure: ' + str(ex))

    if len(msgs) > 0:
        publish.multiple(msgs, hostname=ARGS.server, port=ARGS.port, client_id=MQTT_CLIENT_ID)
