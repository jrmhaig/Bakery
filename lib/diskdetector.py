# Much of this is based on code found in the pifacecad library
# (Thanks, guys)
import multiprocessing
import threading
from time import sleep
from subprocess import call

class DiskFunctionMap(object):
    """Map actions to callback functions"""
    def __init__(self, action, callback):
        self.action = action
        self.callback = callback

    def __str__(self):
        s = "Action:  {action}\n"
        return s.format(action=self.action)

class DiskEventListener(object):
    """Listen for disk events"""

    TERMINATE_SIGNAL = 1

    def __init__(self):
        self.function_maps = list()
        self.queue = multiprocessing.Queue()
        self.watching = [ '/dev/sda' ]
        self.detector = multiprocessing.Process(
            target=watch_disk_events,
            args=(self.queue, self.watching))
        self.dispatcher = threading.Thread(
            target=handle_events,
            args=(
                self.queue,
                event_matches_function_map,
                self.function_maps,
                DiskEventListener.TERMINATE_SIGNAL))
        self.devices = []
        self.register('add', self.add_device)
        self.register('remove', self.remove_device)

    def register(self, action, callback):
        self.function_maps.append( DiskFunctionMap (action, callback) )

    def activate(self):
        self.detector.start()
        self.dispatcher.start()

    def deactivate(self):
        self.queue.put(self.TERMINATE_SIGNAL)
        self.dispatcher.join()
        self.detector.terminate()
        self.detector.join()

    def add_device(self, event):
        if event.device in self.devices:
            self.error(event.device + ' is already in the list!')
        else:
            self.devices.append(event.device)

    def remove_device(self, event):
        if event.device in self.devices:
            self.devices.remove(event.device)
        else:
            self.error(event.device + ' is not in the list!')

class DiskEvent(object):
    """A disk event"""
    def __init__(self, action, device):
        self.action = action
        self.device = device

    def __str__(self):
        s = "action: {action}\n" \
            "device: {device}"
        return s.format(action=self.action, device=self.device)

###########################################################################

def watch_disk_events(queue, watching):
    """Watch for new disks

    A USB-SD adapter may appear in /dev even if there is no SD present. This
    function uses fdisk to check if a card has been inserted.

    """
    on = 0
    actions = [ 'remove', 'add' ]
    while True:
        # TODO Fix the hard-wired path
        for dev in watching:
            if on != call(["/home/pi/Bakery/probe.sh", dev]):
                on = 1 - on
                queue.put(DiskEvent(actions[on], dev))
        sleep(1)

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

