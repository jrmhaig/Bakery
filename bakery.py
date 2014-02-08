#!/usr/bin/python3

import subprocess
import signal
import re
import configparser
import struct
import queue
import threading
import time
import pyudev
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
#XX#    # Uncompressed size of a gzip file is stored in the last 4 bytes
#XX#    fl = open(image, 'rb')
#XX#    fl.seek(-4, 2)
#XX#    r = fl.read()
#XX#    fl.close()
#XX#    size = struct.unpack('<I', r)[0]
#XX#
#XX#    print("Image:", image)
#XX#
#XX#    # Unzip process
#XX#    unzip = subprocess.Popen(['zcat', image], stdout=subprocess.PIPE)
#XX#
#XX#    # DD process
#XX#    # Output to a pipe to catch status updates
#XX#    dd = subprocess.Popen(['dd', 'of=' + device, 'bs=1M'], bufsize=1, stdin=unzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#XX#    dd_queue = queue.Queue()
#XX#    dd_thread = threading.Thread(target = read_pipe, args=(dd.stdout, dd_queue))
#XX#    dd_thread.daemon = True
#XX#    dd_thread.start()
#XX#
#XX#    print("unzip PID:", unzip.pid)
#XX#    print("dd PID   :", dd.pid)
#XX#    probe_sleep = 20
#XX#    next_probe = time.time()
#XX#    while unzip.poll() is None:
#XX#        if dd.poll() is not None:
#XX#            unzip.kill()
#XX#            return False
#XX#        if time.time() > next_probe:
#XX#            dd.send_signal(signal.SIGUSR1)
#XX#            next_probe = next_probe + probe_sleep
#XX#
#XX#        try:
#XX#            line = dd_queue.get(timeout = 0.1)
#XX#            m = re.search(r"(\d+) bytes", str(line))
#XX#            if m != None:
#XX#                percent = 100*int(m.group(1))/size
#XX#                display.progress(percent)
#XX#                print("Completed: " + str(percent) + "%")
#XX#                next_probe = time.time() + 5
#XX#        except:
#XX#            pass

    # Find partitions
    environment = {}
    pn = 1
    for partition in pyudev.Context().list_devices(subsystem='block', DEVTYPE='partition'):
        node = partition.device_node
        if re.search(r"{}".format(device), node):
            environment["PARTITION{}".format(pn)] = node
            pn = pn + 1

    subprocess.call(['/home/pi/test.sh'], env=environment)

    print("And finished")
    return True

display = BakeryDisplay(disks, images, write_image)

display.menu()
