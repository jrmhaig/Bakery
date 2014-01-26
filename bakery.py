#!/usr/bin/python3

import subprocess
import signal
import re
import configparser
import struct
import queue
import threading
import time
from lib.bakerydisplay import *
from lib.selectlist import *
from lib.diskdetector import *

config_files = [
                '/etc/bakery.cfg',
                'conf/bakery.cfg'
               ]

config = configparser.ConfigParser()
config.read( config_files )
dirs = config.get('images', 'source')

images = disk_image_list(dirs)

disks = DiskEventListener()
disks.activate()

def read_pipe(out, queue):
    for line in iter(out.readline, b''):
        queue.put(str(line))
    out.close()

def write_image(device, image):
    # Uncompressed size of a gzip file is stored in the last 4 bytes
    fl = open(image, 'rb')
    fl.seek(-4, 2)
    r = fl.read()
    fl.close()
    size = struct.unpack('<I', r)[0]

    print("Image:", image)

    # Unzip process
    unzip = subprocess.Popen(['zcat', image], stdout=subprocess.PIPE)

    # DD process
    # Output to a pipe to catch status updates
    dd = subprocess.Popen(['dd', 'of=' + device, 'bs=1M'], bufsize=1, stdin=unzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    dd_queue = queue.Queue()
    dd_thread = threading.Thread(target = read_pipe, args=(dd.stdout, dd_queue))
    dd_thread.daemon = True
    dd_thread.start()

    print("unzip PID:", unzip.pid)
    print("dd PID   :", dd.pid)
    probe_sleep = 20
    next_probe = time.time()
    while unzip.poll() is None:
        if dd.poll() is not None:
            unzip.kill()
            return False
        if time.time() > next_probe:
            dd.send_signal(signal.SIGUSR1)
            next_probe = next_probe + probe_sleep

        try:
            line = dd_queue.get(timeout = 0.1)
            m = re.search(r"(\d+) bytes", str(line))
            if m != None:
                percent = 100*int(m.group(1))/size
                display.progress(percent)
                print("Completed: " + str(percent) + "%")
                next_probe = time.time() + 5
        except:
            pass

    display.progress(-1)
    print("And finished")
    return True

display = BakeryDisplay(disks, images, write_image)

display.menu()
