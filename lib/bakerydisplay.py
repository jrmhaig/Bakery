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

    # Bitmap IDs
    # First 5 bitmaps for the blocks for the progress bar
    BLOCK = range(5)
    FULL_BLOCK = 4
    # Unselected and selected indicator icons
    UNSELECTED = 5
    SELECTED = 6

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

        # Store bitmaps for the partial blocks that make up the progree bar.
        # Each one contains 8 lines of the same number:
        #   BLOCK[0]  '#    ' = 16
        #   BLOCK[1]  '##   ' = 24
        #   BLOCK[2]  '###  ' = 28
        #   BLOCK[3]  '#### ' = 30
        #   BLOCK[4]  '#####' = 31 
        n = 0
        for j in range(5):
            n = n + ( 2 ** ( 4 - j ) )
            self.write_queue.put( { 'action': 'store',
                                    'bitmap': self.BLOCK[j],
                                    'lines': [n]*8 } )

        self.write_queue.put( { 'action': 'store',
                                'bitmap': self.UNSELECTED,
                                'lines': [
                                           31,   #   #####
                                           17,   #   #   #
                                           17,   #   #   #
                                           17,   #   #   #
                                           17,   #   #   #
                                           17,   #   #   #
                                           17,   #   #   #
                                           31,   #   #####
                                         ] } )

        self.write_queue.put( { 'action': 'store',
                                'bitmap': self.SELECTED,
                                'lines': [
                                           31,   #   #####
                                           17,   #   #   #
                                           21,   #   # # #
                                           21,   #   # # #
                                           21,   #   # # #
                                           21,   #   # # #
                                           17,   #   #   #
                                           31,   #   #####
                                         ] } )

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
        else:
            self.press_start = time.time()
            self.is_pressed = True
            self.countdown = self.PRESS_TIME
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 1],
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

            self.updates = False

            start_time = time.time()
            #if self.write_function( self.disks.device_name(0),
            #                            self.slist.selected_image_file() ):
            if self.write_function( self.disks.device_name(0),
                                        self.slist.get_image(), self ):
                self.write_queue.put( { 'action': 'clear' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0,0],
                                        'text': '    FINISHED    ' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0,1],
                                        'text': '{0} seconds'.format(int(time.time() - start_time)) } )
            else:
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

        """
        self.write_queue.put( { 'action': 'write',
                                'pos': [10,0],
                                'text': '{0:5.2f}'.format(percent) } )
        k = percent / 6.25    #    percent * 16 / 100
        l = int(k)            #    Number of complete blocks
        m = int((k - l) * 6)  #    Number of lines in partial block

        while self.progress_pointer < l:
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [self.progress_pointer, 1],
                                    'bitmap': self.FULL_BLOCK } )
            self.progress_pointer = self.progress_pointer + 1

        if m > 0:
            # m == 0 => empty block
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [self.progress_pointer, 1],
                                    'bitmap': self.BLOCK[m-1] } )

    def refresh(self):
        """Refresh the screen for the menu"""
        self.write_queue.put( { 'action': 'clear' } )

        # Image name
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [0,0],
                                'text': self.slist.current() } )

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
                                                'bitmap': self.SELECTED} )
                    else:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'bitmap': self.UNSELECTED} )
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [dev*8+1,1],
                                            'text': '{0: <6}'.format(os.path.basename(name)) } )
        else:
            for dev in range(self.MAX_DEVICES):
                if self.disks.device_present(dev):
                    if self.device_state[dev] == 0:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'bitmap': self.SELECTED } )
                        self.device_state[dev] = 1
                else:
                    if self.device_state[dev] == 1:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'bitmap': self.UNSELECTED } )
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
                                            'pos': [9, 1],
                                            'text': str(self.countdown) } )

            if self.updates:
                self.devices_line()
                time.sleep(0.5)

    def prev(self, event):
        img = self.slist.prev()
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [0,0],
                                'text': img } )

    def next(self, event):
        img = self.slist.next()
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [0,0],
                                'text': img } )

    def select(self, event):
        self.slist.select()
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [0,0],
                                'text': self.slist.current() } )

def _lcd_writer(queue):
    """Write to the LCD

    This function is run as a background thread with a queue to avoid
    conflicting display updates.

    Messages passed to the queue are hashes containing:

        'action': 'clear'         - Clear the screen

        'action': 'write'         - Write message
        'pos': [ <int>, <int> ]   - Position to start text
        'test': <string>          - Message to write
        'blank': 0/1              - 1 = Clear to end of line (optional)

        'action': 'store'         - Store bitmap
        'bitmap': <int>           - Bitmap id
        'lines': [ <int> * 8 ]    - Array of lines to make up bitmap

        'action': 'bitmap'        - Write a bitmap
        'pos': [ <int>, <int> ]   - Position to print bitmap
        'bitmap': <int>           - Bitmap id

        'action': 'finish'        - End

    """
    cad = pifacecad.PiFaceCAD()
    cad.lcd.backlight_on()
    cad.lcd.cursor_off()
    cad.lcd.blink_off()
    line_length = [0, 0]

    while True:
        message = queue.get()
        if message['action'] == 'finish':
            return
        elif message['action'] == 'write':
            cad.lcd.set_cursor(message['pos'][0], message['pos'][1])
            text_len = len(message['text'])
            if ( message['pos'][0] + text_len < line_length[message['pos'][1]]
                 and 'blank' in message and message['blank'] ):
                ln = line_length[message['pos'][1]] - message['pos'][0]
                line_length[message['pos'][1]] = message['pos'][0] + text_len 
            else:
                ln = text_len 
                new_ln = message['pos'][0] + len(message['text'])
                if new_ln > line_length[message['pos'][1]]:
                   line_length[message['pos'][1]] = new_ln
            cad.lcd.write(('{:<' + str(ln) + '}').format(message['text']))
        elif message['action'] == 'store':
            cad.lcd.store_custom_bitmap(message['bitmap'], message['lines'])
        elif message['action'] == 'bitmap':
            cad.lcd.set_cursor(message['pos'][0], message['pos'][1])
            cad.lcd.write_custom_bitmap( message['bitmap'] )
        elif message['action'] == 'clear':
            cad.lcd.clear()
