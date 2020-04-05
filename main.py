# This is your main script.
import machine
import network
import time
from umqtt.simple import MQTTClient
import json
import sys

# ------------------------------------------------------------------
# CONSTANTS

CONFIG_FILE = 'config.json'

# ------------------------------------------------------------------
# Global Variables

sta_if = None       # Wifi Interface
settings = None     # Json File Parsed
sensors = {}        # List of water sensors
led = None          # Status led pin

mqtt_client = None

last_update_status = 0
last_update_pulses = 0
last_update_litres = 0

# ------------------------------------------------------------------

'''
Loading JSON Configuration File
'''
def loadConfigFile():
    global CONFIG_FILE, settings
    try:
        f = open(CONFIG_FILE,'r')
        settings = json.load(f)
        f.close()
    except OSError:
        return False

# ------------------------------------------------------------------

'''
Connect to Wifi
'''
def connectWifi():
    global sta_if, settings
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(settings['wifi']['SSID'], settings['wifi']['PSK'])

    while True:
        print("Connecting...")
        time.sleep(1)
        if sta_if.isconnected():
            print("Connected!")
            print(sta_if.ifconfig())
            break

# ------------------------------------------------------------------

'''
Connect broker
'''
def connectMqtt():
    global settings, mqtt_client
    mqtt_client = MQTTClient(settings['mqtt']['client'], settings['mqtt']['broker'])
    mqtt_client.connect()

    mqtt_client.publish(settings['mqtt']['prefix'] + settings['mqtt']['t_status'], 'water sensor up')

    print("MQTT Connected!")

# ------------------------------------------------------------------

'''
Setup pins (GPIO)
'''
def setupPins():
    global settings, sensors, led

    for sensor in settings['sensors']:

        s = machine.Pin(sensor['pin'], machine.Pin.IN)

        sensors[str(sensor['pin'])] = {}
        sensors[str(sensor['pin'])]['name'] = sensor['name']
        sensors[str(sensor['pin'])]['m3'] = 0
        sensors[str(sensor['pin'])]['pulses'] = 0
        sensors[str(sensor['pin'])]['litres'] = 0

        s.irq(trigger=machine.Pin.IRQ_FALLING, handler=water_tick_handler)
    
    if 'statusLed' in settings:
        led = machine.Pin(settings['statusLed'], machine.Pin.OUT)

# ------------------------------------------------------------------

'''
Status led toggling
'''
def toggleLed():
    global led
    if led is not None:
        led.value(led.value()^1)

# ------------------------------------------------------------------

def water_tick_handler(p):
    global sensors
    id = str(p)[4:-1]
    sensors[id]['pulses'] += 1
    if sensors[id]['pulses'] == settings['pulsesPerLitre']:
        sensors[id]['pulses'] = 0
        sensors[id]['litres'] += 1
    if sensors[id]['litres'] == 1000:
        sensors[id]['litres'] = 0
        sensors[id]['m3'] += 1

    toggleLed()

# ------------------------------------------------------------------

def send_mqtt_volume_update():
    global sensors, settings, mqtt_client

    print("[+] Status update")

    for s_id in sensors:
        strValue = str(sensors[s_id]['m3']) + '.' \
            "{:03d}".format(sensors[s_id]['litres']) + \
            "{:03d}".format(int(sensors[s_id]['pulses'] / settings['pulsesPerLitre'] * 1000))

        sName = sensors[s_id]['name']
        sPulses = str(sensors[s_id]['pulses'])

        mqtt_client.publish( \
            settings['mqtt']['prefix'] + sName + '/' + settings['mqtt']['t_cons'], \
            '{ "value": ' + strValue + \
            ', "pulses": ' + sPulses + ' }' \
        )

# ------------------------------------------------------------------

def save():
    global sensors
    print("[+] Saving State")

    f = open('state.json','w')
    json.dump(sensors, f)
    f.close()

# ------------------------------------------------------------------

def restore():
    global sensors
    try:
        f = open('state.json','r')
        print("[+] Restoring State")
        sensors = json.load(f)
        f.close()
    except OSError:
        return False


# ------------------------------------------------------------------
# Main Program

if loadConfigFile() == False:
    print("[!] Missing " + CONFIG_FILE + " configuration file. Exiting.")
    sys.exit()

setupPins()
restore()
connectWifi()
connectMqtt()

while True:
    #toggleLed()
    time.sleep(1)
    if time.time() % 5 == 0:
        send_mqtt_volume_update()
    
    if time.time() % 60 == 0:
        save()

