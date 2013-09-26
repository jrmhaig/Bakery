from lib.sdimages import *
import configparser
import pifacedigitalio
from time import sleep

def find_buttons(n):
    btns = []
    for i in range(7, -1, -1):
        if ( 2**i <= n ):
            btns.append(1)
            n = n - 2**i
        else:
            btns.append(0)
    btns.reverse()
    return btns

config = configparser.ConfigParser()
config.read('baker.cfg')

dirs = config.get('images', 'source')
print(dirs)

sdi = SdImages([dirs])

ls = sdi.list()

pfd = pifacedigitalio.PiFaceDigital()

while True:
    # Wait until the button has been released since last time
    event = pfd.input_port.value
    while event != 0:
        event = pfd.input_port.value
        sleep(0.001)

    # Wait for a button to be pressed
    while event == 0:
        event = pfd.input_port.value

    buttons = find_buttons(event)

    if buttons[0]:
        # S1 - Previous image
        # TODO
        print("S1 pressed")
    if buttons[1]:
        # S2 - Next image
        # TODO
        print("S2 pressed")
    if buttons[2]:
        # S3 - Write image
        # TODO
        print("S3 pressed")
