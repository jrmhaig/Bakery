from lib.sdimages import *
# configparser for Python 3
import ConfigParser
import pifacedigitalio
from time import sleep

pfd = pifacedigitalio.PiFaceDigital()

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

def error():
    while True:
        pfd.output_port.value = 0xAA
        sleep(1)
        pfd.output_port.value = 0x00
        sleep(1)

# configparser.ConfigParser for Python 3
config = ConfigParser.ConfigParser()
config.read('baker.cfg')

dirs = config.get('images', 'source')

sdi = SdImages([dirs])

ls = sdi.list()
max = len(ls)
if max>8:
    # No more than 8 images
    error()

image = 0

while True:
    print("Image: ", ls[image])
    pfd.output_port.value = 2**image

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
        # S1 - Next image
        image = image + 1
        if image == max:
            image = 0
    if buttons[1]:
        # S2 - Previous image
        image = image - 1
        if image == -1:
            image = max - 1
    if buttons[2]:
        # S3 - Write image
        # TODO
        print("S3 pressed")
