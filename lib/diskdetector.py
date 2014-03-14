# Much of this is based on code found in the pifacecad library
# (Thanks, guys)
import multiprocessing
import threading
import pyudev
import sys
import time
import subprocess
import lib.utils as utils

class DiskFunctionMap(object):
    """Map actions to callback functions"""
    def __init__(self, action, callback):
        self.action = action
        self.callback = callback

    def __str__(self):
        s = "Action:  {action}\n"
        return s.format(action=self.action)

class DiskEventListener(utils.SelectList):
    """Listen for disk events"""

    TERMINATE_SIGNAL = 1

    def __init__(self):
        utils.SelectList.__init__(self)
        self.function_maps = list()
        self.queue = multiprocessing.Queue()

        # Get list of mounted devices
        self.context = pyudev.Context()
        #self.devices = []
        for device in self.context.list_devices(subsystem='block', DEVTYPE='disk'):
            major = device['MAJOR']
            if major == '8' or major == '3':
                self.append(utils.Drive(device.device_node, device['ID_MODEL']))

        self.set_disk_detector()
        self.device_detector = multiprocessing.Process(
            target=watch_device_events,
            args=(self.queue, self.context))
        self.dispatcher = threading.Thread(
            target=handle_events,
            args=(
                self.queue,
                event_matches_function_map,
                self.function_maps,
                DiskEventListener.TERMINATE_SIGNAL))
        #self.disks = []
        self.register('add_disk', self.add_disk)
        self.register('remove_disk', self.remove_disk)
        self.register('add_device', self.add_device)
        self.register('remove_device', self.remove_device)

    def set_disk_detector(self):
        restart = 0
        try:
            self.disk_detector.terminate()
            self.disk_detector.join()
            restart = 1
        except AttributeError:
            pass

        self.disk_detector = multiprocessing.Process(
            target=watch_disk_events,
            args=(self.queue, [ d.path for d in self ]))
            #args=(self.queue, self.devices))

        if restart:
            self.disk_detector.start()

    def register(self, action, callback):
        self.function_maps.append( DiskFunctionMap (action, callback) )

    def activate(self):
        self.disk_detector.start()
        self.device_detector.start()
        self.dispatcher.start()

    def deactivate(self):
        self.queue.put(self.TERMINATE_SIGNAL)
        self.dispatcher.join()
        self.disk_detector.terminate()
        self.disk_detector.terminate()
        self.disk_detector.join()
        self.disk_detector.join()

    def add_disk(self, event):
        d = self.find(event.device)
        if d != None:
            d.present = True

    def remove_disk(self, event):
        d = self.find(event.device)
        if d != None:
            d.present = False

    def add_device(self, event):
        if self.find(event.device):
            print(event.device + ' is already in the list!')
            sys.exit(1)
        else:
            self.append(utils.Drive(event.device, event.model))
            self.set_disk_detector()

    def remove_device(self, event):
        d = self.find(event.device)
        if d != None:
            self.remove(d)
            if self.pointer <= len(self):
                self.pointer = 0
            self.set_disk_detector()
        else:
            print(event.device + ' is not in the list!')
            sys.exit(1)

    def find(self, dev):
        for d in self:
            if dev == d.path:
                return d
        return None

    #def device_name(self, n):
    #    try:
    #        return self.devices[n]
    #    except:
    #        return None

    def device_present(self, n):
        if n < len(self):
            return self[n].present
        else:
            return False

    #def active_device(self):
    #    for i, d in enumerate(self.devices):
    #        if self.device_present(i):
    #            return d
    #
    #    return None

class DeviceEvent(object):
    """A device event"""
    def __init__(self, action, device, model = None):
        self.action = action
        self.device = device
        self.model = model

    def __str__(self):
        s = "action: {action}\n" \
            "device: {device}"
        return s.format(action=self.action, device=self.device)

###########################################################################

def watch_device_events(queue, context):
    """Watch for new devices

    Detect when a new USB device has been added. In the case of an SD card
    reader, for example, this may appear even when an actual card is not
    present. The function watch_disk_events will then check existing devices
    for the actual disk.

    """

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block', 'disk')
    for action, device in monitor:
        if action == 'add' or action == 'remove':
            queue.put(DeviceEvent(action + "_device", device.device_node, device['ID_MODEL']))

def watch_disk_events(queue, devices):
    """Watch for new disks

    A USB-SD adapter may appear in /dev even if there is no SD present. This
    function uses fdisk to check if a card has been inserted.

    """
    on = [0]*len(devices)
    actions = [ 'remove_disk', 'add_disk' ]
    while True:
        for i in range(len(devices)):
            probe = subprocess.Popen(['fdisk', '-l', devices[i]], stdout=subprocess.PIPE)
            count = 0
            for line in probe.stdout:
                # Maybe use this output later?
                count += 1
            if ( on[i] == 0 and count > 0 ) or ( on[i] == 1 and count == 0 ):
                on[i] = 1 - on[i]
                queue.put(DeviceEvent(actions[on[i]], devices[i]))
        time.sleep(1)

def handle_events(queue, event_matches_function_map,
                       function_maps, terminate_signal):
    """Handle events"""
    while True:
        event = queue.get()

        if event == terminate_signal:
            return

        functions = map(
            lambda fm: fm.callback
            if event_matches_function_map(event, fm) else None,
            function_maps)
        functions = filter(lambda f: f is not None, functions)

        for function in functions:
            function(event)

def event_matches_function_map(event, function_map):
    action_match = event.action == function_map.action
    return action_match

