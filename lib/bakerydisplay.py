import pifacecad
import multiprocessing
import threading
import time
import os.path

class BakeryDisplay:

    # Only use up to two devices
    # Without a USB hub, there cannot be any more on a Raspberry Pi
    MAX_DEVICES = 2

    # Number of seconds to require the button is pressed for
    PRESS_TIME = 5

    def __init__(self, disks, slist, write_function):
        # Callback function for writing to the device
        self.write_function = write_function

        # List of images available
        self.slist = slist

        # Watcher for disks & devices
        self.disks = disks
        # Number of devices present
        self.n_devices = 0
        self.device_state = [0]*self.MAX_DEVICES
        # Send updates to display of devices
        self.updates = False
        # Whether button is pressed or not
        self.is_pressed = False

        self.cad = pifacecad.PiFaceCAD()
        self.listener = pifacecad.SwitchEventListener(chip=self.cad)
        self.listener.register(4, pifacecad.IODIR_FALLING_EDGE, self.pressed)
        self.listener.register(4, pifacecad.IODIR_RISING_EDGE, self.released)
        self.listener.register(5, pifacecad.IODIR_FALLING_EDGE, self.select)
        self.listener.register(6, pifacecad.IODIR_FALLING_EDGE, self.prev)
        self.listener.register(7, pifacecad.IODIR_FALLING_EDGE, self.next)

        self.write_queue = multiprocessing.Queue()
        self.writer = threading.Thread( target = _lcd_writer,
                                        args = ( self.write_queue, ) )

        self.writer.start()

        self.part_block = []
        n = 0
        for i in range(4,-1,-1):
            n = n + (2**i)
            self.part_block.append( [n] * 8 )
        self.write_queue.put( { 'action': 'store',
                                'bitmap': 1,
                                'lines': self.part_block[4] } )

    def __del__(self):
        self.cad.lcd.backlight_off()

    def pressed(self, event):
        """Button has been pressed

        Start a counter so that writing only starts when the button has been
        pressed for five seconds.

        """
        if len(self.disks.disks) == 0:
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 0],
                                    'text': 'No disk present ' } )
            self.press_start = -1
        elif self.slist.current_full_path() == None:
            self.write_queue.put( { 'action': 'clear' } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 0],
                                    'text': 'No image' } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 1],
                                    'text': 'selected' } )
            self.press_start = -1
        else:
            self.press_start = time.time()
            self.is_pressed = True
            self.countdown = self.PRESS_TIME
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 0],
                                    'text': 'Write in {0} secs '.format(self.PRESS_TIME) } )

    def released(self, event):
        """Button has been released

        Only call the callback function if the button has been pressed for
        five seconds. Otherwise, do nothing.

        """
        self.is_pressed = False
        if self.press_start > 0 and time.time() > self.press_start + self.PRESS_TIME:
            self.write_queue.put( { 'action': 'clear' } )

            # Top line
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0,0],
                                    'text': 'Complete:  0.00%' } )

            # Second line
            self.progress_pointer=0
            self.write_queue.put( { 'action': 'store',
                                    'bitmap': 0,
                                    'lines': self.part_block[0] } )
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [0,1],
                                    'bitmap': 0 } )

            self.updates = False
            #self.write_function(self.write_queue)
            if not self.write_function( self.disks.device_name(0),
                                        self.slist.current_full_path() ):
                self.write_queue.put( { 'action': 'clear' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0, 0],
                                        'text': 'Write failed' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0, 1],
                                        'text': 'Try again' } )

            time.sleep(5)
            self.refresh()
            self.updates = True
        else:
            self.refresh()

    def progress(self, percent):
        """Display the progress

        Write the percentage progress and show a progress bar on the LCD.
        A percentage of -1 indicates completion.

        """
        if percent == -1:
            self.write_queue.put( { 'action': 'clear' } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0,0],
                                    'text': '    FINISHED    ' } )
        else:
            self.write_queue.put( { 'action': 'write',
                                    'pos': [10,0],
                                    'text': '{0:5.2f}'.format(percent) } )
            k = percent / 6.25    #    percent * 16 / 100
            l = int(k)            #    Number of complete blocks
            m = int((k - l) * 5)  #    Number of lines in partial block

            # Wrapped in an 'if' block to save a bit of time
            # Writing a character is slow - avoid if possible
            if self.progress_pointer < l:
                while self.progress_pointer < l:
                    self.write_queue.put( { 'action': 'bitmap',
                                            'pos': [self.progress_pointer,1],
                                            'bitmap': 1 } )
                    self.progress_pointer = self.progress_pointer + 1

                self.write_queue.put( { 'action': 'store',
                                        'bitmap': 0,
                                        'lines': self.part_block[m] } )
                self.write_queue.put( { 'action': 'bitmap',
                                        'pos': [self.progress_pointer,1],
                                        'bitmap': 0 } )
            else:
                # Don't need to re-write character. Just change the bitmap.
                self.write_queue.put( { 'action': 'store',
                                        'bitmap': 0,
                                        'lines': self.part_block[m] } )

    def refresh(self):
        """Refresh the screen for the menu"""
        self.write_queue.put( { 'action': 'clear' } )

        # Image name
        self.write_queue.put( { 'action': 'write',
                                'pos': [0,0],
                                'text': '{0}'.format(self.slist.current()) } )

        # Device
        self.devices_line(True)

    def devices_line(self, rewrite=False):
        """Display the devices line on the LCD"""
        if rewrite or self.n_devices != len(self.disks.devices):
            # Number of devices has changed
            self.n_devices = len(self.disks.devices)
            self.device_state = [0]*self.MAX_DEVICES
            for dev in range(self.MAX_DEVICES):
                name = self.disks.device_name(dev)
                if name == None:
                    # No device
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [dev*8,1],
                                            'text': ' '*8 } )
                else:
                    if self.disks.device_present(dev):
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'bitmap': 1 } )
                    else:
                        self.write_queue.put( { 'action': 'write',
                                                'pos': [dev*8,1],
                                                'text': ' ' } )
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [dev*8+1,1],
                                            'text': '{0: <6}'.format(os.path.basename(name)) } )
        else:
            for dev in range(self.MAX_DEVICES):
                if self.disks.device_present(dev):
                    if self.device_state[dev] == 0:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'bitmap': 1 } )
                        self.device_state[dev] = 1
                else:
                    if self.device_state[dev] == 1:
                        self.write_queue.put( { 'action': 'write',
                                                'pos': [dev*8,1],
                                                'text': ' ' } )
                        self.device_state[dev] = 0

    def menu(self):
        # TODO Use this to have an exit button
        self.finish = 0

        self.listener.activate()

        self.refresh()
        self.updates = True

        while self.finish == 0:
            if self.is_pressed:
                if (self.press_start > 0 and
                    self.countdown > 0 and
                    int(time.time() - self.press_start) > self.PRESS_TIME - self.countdown):
                    self.countdown = self.countdown - 1
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [9, 0],
                                            'text': str(self.countdown) } )

            if self.updates:
                self.devices_line()
                time.sleep(0.5)

    def prev(self, event):
        self.write_queue.put( { 'action': 'write',
                                'pos': [0,0],
                                'text': self.slist.prev() } )

    def next(self, event):
        self.write_queue.put( { 'action': 'write',
                                'pos': [0,0],
                                'text': self.slist.next() } )

    def select(self, event):
        self.slist.select()
        self.write_queue.put( { 'action': 'write',
                                'pos': [0,0],
                                'text': self.slist.current() } )

def _lcd_writer(queue):
    """Write to the LCD

    This function is run as a background thread with a queue to avoid
    conflicting display updates.

    """
    cad = pifacecad.PiFaceCAD()
    cad.lcd.backlight_on()
    cad.lcd.cursor_off()
    cad.lcd.blink_off()

    while True:
        message = queue.get()
        if message['action'] == 'finish':
            return
        elif message['action'] == 'write':
            cad.lcd.set_cursor(message['pos'][0], message['pos'][1])
            cad.lcd.write(message['text'])
        elif message['action'] == 'store':
            cad.lcd.store_custom_bitmap(message['bitmap'], message['lines'])
        elif message['action'] == 'bitmap':
            cad.lcd.set_cursor(message['pos'][0], message['pos'][1])
            cad.lcd.write_custom_bitmap( message['bitmap'] )
        elif message['action'] == 'clear':
            cad.lcd.clear()
