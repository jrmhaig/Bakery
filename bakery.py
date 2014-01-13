import subprocess
import signal
import re
from lib.bakerydisplay import *
from time import sleep

image = '/home/pi/images/wheezy-raspbian.img.gz'
# Can get this with gunzip -l $FILE
size = 2962227200

def write_image(display):
    unzip = subprocess.Popen(['zcat', image], stdout=subprocess.PIPE)
    dd = subprocess.Popen(['dd', 'of=/dev/sda', 'bs=1M'], stdin=unzip.stdout, stderr=subprocess.PIPE)
    print("unzip PID:", unzip.pid)
    print("dd PID   :", dd.pid)
    i = 0
    sleep(5)
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
        dd.send_signal(signal.SIGUSR1)
        sleep(10)

    display.progress(-1)
    print("And finished")

display = BakeryDisplay(write_image)

while True:
    pass
