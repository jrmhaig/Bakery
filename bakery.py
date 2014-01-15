import subprocess
import signal
import re
from lib.bakerydisplay import *
from lib.selectlist import *
from time import sleep
from struct import unpack

images = disk_image_list('/home/pi/images')

def write_image(display):
    image = str(images.current_full_path())
    if image == None:
        display.cad.lcd.clear()
        display.cad.lcd.write('No image selected')
        return 0

    print("Image:", image)
    # Uncompressed size of a gzip file is stored in the last 4 bytes
    fl = open(image, 'rb')
    fl.seek(-4, 2)
    r = fl.read()
    fl.close()
    size = unpack('<I', r)[0]

    print("Image:", image)
    unzip = subprocess.Popen(['zcat', image], stdout=subprocess.PIPE)
    dd = subprocess.Popen(['dd', 'of=/dev/sda', 'bs=1M'], stdin=unzip.stdout, stderr=subprocess.PIPE)
    print("unzip PID:", unzip.pid)
    print("dd PID   :", dd.pid)
    i = 0
    dd.send_signal(signal.SIGUSR1)
    while unzip.poll() is None:
        for line in dd.stderr:
            #print("Line:", line)
            #print("Line:", str(line))
            m = re.search(r"(\d+) bytes", str(line))
            if m != None:
                percent = 100*int(m.group(1))/size
                display.progress(percent)
                print("Completed: " + str(percent) + "%")
                break
        #print(dd.communicate())
        #print("Still working:", i)
        i=i+1
        sleep(3)
        dd.send_signal(signal.SIGUSR1)

    display.progress(-1)
    print("And finished")

display = BakeryDisplay(write_image)

display.menu(images)
