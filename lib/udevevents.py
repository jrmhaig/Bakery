# Much of this is based on code found in the pifacecad library
# (Thanks, guys)
import multiprocessing
import threading
import pyudev

class UdevFunctionMap(object):
    """Map actions to callback functions"""
    def __init__(self, action, callback, settle_time=None):
        self.action = action
        self.callback = callback

    def __str__(self):
        s = "Action:  {action}\n"
        return s.format(action=self.action)

class UdevEventListener(object):
    """Listen for events on udev"""

    TERMINATE_SIGNAL = 1

    def __init__(self):
        self.function_maps = list()
        self.queue = multiprocessing.Queue()
        self.detector = multiprocessing.Process(
            target=watch_udev_events,
            args=(
                self.queue,))
        self.dispatcher = threading.Thread(
            target=handle_udev_events,
            args=(
                self.queue,
                event_matches_udev_function_map,
                self.function_maps,
                UdevEventListener.TERMINATE_SIGNAL))

    def register(self, action, callback):
        self.function_maps.append( UdevFunctionMap (action, callback) )

    def activate(self):
        self.detector.start()
        self.dispatcher.start()

    def deactivate(self):
        self.queue.put(self.TERMINATE_SIGNAL)
        self.dispatcher.join()
        self.detector.terminate()
        self.detector.join()

class UdevEvent(object):
    """A udev event"""
    def __init__(self, action, device):
        self.action = action
        self.device = device

    def __str__(self):
        s = "action: {action}\n" \
            "device: {device}"
        return s.format(action=self.action, device=self.device)

###########################################################################

def watch_udev_events(queue):
    """Watch for udev events"""
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block', 'disk')
    for action, device in monitor:
        if action == 'add' or action == 'remove':
            queue.put(UdevEvent(action, device.device_node))

def handle_udev_events(queue, event_matches_function_map,
                       function_maps, terminate_signal):
    """Handle udev events"""
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

def event_matches_udev_function_map(event, function_map):
    action_match = event.action == function_map.action
    return action_match

###########################################################################

devices = []

def add_device(event):
    if event.device in devices:
        print(event.device, 'is already in the list!')
    else:
        devices.append(event.device)

def remove_device(event):
    if event.device in devices:
        devices.remove(event.device)
    else:
        print(event.device, 'was not in the list!')
