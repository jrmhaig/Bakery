from lib.sdimages import *
from lib.iface import *
import configparser
from time import sleep

#pfd = pifacedigitalio.PiFaceDigital()

#def find_buttons(n):
#    """ Detect which buttons are pressed
#
#    The inputs value is a byte representing each input as bits. This is split
#    into a list of 8 flags.
#
#    """
#    btns = []
#    for i in range(7, -1, -1):
#        if ( 2**i <= n ):
#            btns.append(1)
#            n = n - 2**i
#        else:
#            btns.append(0)
#    btns.reverse()
#    return btns

#def error():
#    """ Report an error
#
#    An error is represented by a flashing '10101010' pattern on the LEDs
#
#    """
#    while True:
#        pfd.output_port.value = 0xAA
#        sleep(1)
#        pfd.output_port.value = 0x00
#        sleep(1)

#def write_image_list():
#    """ Write out the list of images
#
#    If a formatted USB drive is inserted then create a file containing a list
#    of the images available. If a drive isn't inserted then nothing happens.
#
#    TODO: Write to the USB drive rather than a file in the /tmp directory.
#
#    """
#    f = open('/tmp/image_list.txt', 'w')
#    f.write("76543210\n")
#    for i in range(8):
#        line = '0'*(7-i) + '1' + '0'*i + ': '
#        try:
#            line = line + ls[i] + "\n"
#        except:
#            line = line + '----' + "\n"
#        f.write(line)
#    f.close()

config = configparser.ConfigParser()
config.read('baker.cfg')

dirs = config.get('images', 'source')

sdi = SdImages(*[dirs])

iface = ITools.hw_connect( sdi )

iface.loop()

#ls = sdi.list()
#max = len(ls)
#if max>8:
#    # No more than 8 images
#    iface.error()
#
#image = 0
#
#while True:
#    print("Image: ", ls[image])
#    pfd.output_port.value = 2**image
#
#    # Wait until the button has been released since last time
#    event = pfd.input_port.value
#    while event != 0:
#        event = pfd.input_port.value
#        sleep(0.001)
#
#    # Wait for a button to be pressed
#    while event == 0:
#        event = pfd.input_port.value
#
#    buttons = find_buttons(event)
#
#    if buttons[0]:
#        # S1 - Next image
#        image = image + 1
#        if image == max:
#            image = 0
#    if buttons[1]:
#        # S2 - Previous image
#        image = image - 1
#        if image == -1:
#            image = max - 1
#    if buttons[2]:
#        # S3 - Write image
#        # TODO
#        print("S3 pressed")
#    if buttons[3]:
#        # S4 - Write image list
#        write_image_list()
