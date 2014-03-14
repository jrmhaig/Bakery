import pifacecad
import multiprocessing
import threading
import time
import os.path
import socket
import subprocess
import re

class BakeryDisplay(list):

    # Only use up to two devices
    # Without a USB hub, there cannot be any more on a Raspberry Pi
    MAX_DEVICES = 5

    # Number of seconds to require the button is pressed for
    PRESS_TIME = 5

    # Bitmap IDs
    # First 5 bitmaps for the blocks for the progress bar
    BLOCK = range(5)
    FULL_BLOCK = 4
    # Unselected and selected indicator icons
    UNSELECTED = 5
    SELECTED = 6
    POINTER = 7

    # Start position of two lines in the main display
    IMG_X = 1
    INFO_X = 1

    # Buttons
    BUTTON_POINTER = 0
    BUTTON_SELECT_DISPLAY = 1
    BUTTON_SCROLL = 4
    BUTTON_WRITE = 5
    BUTTON_PREV = 6
    BUTTON_NEXT = 7

    # Displays
    DISPLAY_MAIN = 0
    DISPLAY_SYSTEM = 1
    DISPLAY_FIRST = DISPLAY_MAIN
    DISPLAY_LAST = DISPLAY_SYSTEM

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

        self.scroll = False

        self.display = self.DISPLAY_MAIN

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

        self.write_queue.put( { 'action': 'store',
                                'bitmap': self.POINTER,
                                'lines': [
                                           0,    #   
                                           8,    #    #
                                           12,   #    ##
                                           14,   #    ###
                                           12,   #    ##
                                           8,    #    #
                                           0,    #    
                                           0,    #
                                         ] } )
        self.pointer_pos = 0
        self.info_n = 0
        self.info_procs = [
                              self.devices_line,
                              self.ip_line,
                              self.cpu_temp,
                              self.post_scripts_line,
                            ]

    def __del__(self):
        self.cad.lcd.backlight_off()

    def pressed(self, event):
        """Button has been pressed

        Start a counter so that writing only starts when the button has been
        pressed for five seconds.

        """
        if self.disks.current().present == False:
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
            if self.write_function( self.disks.current().path(),
                                        self.slist.current(), self ):
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

    def switch_pointer(self, event):
        """Switch the pointer between lines"""
        self.write_queue.put( { 'action': 'write',
                                'pos': [0, self.pointer_pos],
                                'text': ' ' } )
        self.pointer_pos = 1 - self.pointer_pos
        self.write_queue.put( { 'action': 'bitmap',
                                'pos': [0, self.pointer_pos],
                                'bitmap': self.POINTER } )

    def switch_display(self, event):
        """Switch between displays"""
        self.display = self.display + 1
        if self.display > self.DISPLAY_LAST:
            self.display = self.DISPLAY_FIRST
        self.setup_controls()
        self.refresh()

    def setup_controls(self):
        """Set up the listeners for the buttons"""

        # Clear all listeners
        print("Clear listeners")
        self.listener.deregister()

        # Settings for all displays
        # Previous and next
        self.listener.register( self.BUTTON_PREV,
                                pifacecad.IODIR_FALLING_EDGE,
                                self.prev )
        self.listener.register( self.BUTTON_NEXT,
                                pifacecad.IODIR_FALLING_EDGE,
                                self.next )
        # Scroll display
        self.listener.register( self.BUTTON_SCROLL,
                                pifacecad.IODIR_FALLING_EDGE,
                                self.scroll_on )
        self.listener.register( self.BUTTON_SCROLL,
                                pifacecad.IODIR_RISING_EDGE,
                                self.scroll_off )
        # Switch through displays
        self.listener.register( self.BUTTON_SELECT_DISPLAY,
                                pifacecad.IODIR_FALLING_EDGE,
                                self.switch_display )

        if self.display == self.DISPLAY_MAIN:
            print("Setup main listeners")
            self.listener.register( self.BUTTON_WRITE,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.pressed )
            self.listener.register( self.BUTTON_WRITE,
                                    pifacecad.IODIR_RISING_EDGE,
                                    self.released )
            self.listener.register( self.BUTTON_POINTER,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_pointer )

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

        if self.display == self.DISPLAY_MAIN:
            # Pointer
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [0, self.pointer_pos],
                                    'bitmap': self.POINTER } )

            # Image name
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': self.slist.current().name } )

            # Device
            self.show_device(self.INFO_X, 1)
            #self.write_queue.put( { 'action': 'write',
            #                        'blank': 1,
            #                        'pos': [self.INFO_X,1],
            #                        'text': self.disks.current() } )

            ## Device
            #self.devices_line(True)
            ##self.info_line(True)
        else:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': "Status menu" } )
            self.info_line()

    def info_line(self, rewrite=False):
        """Write the second line of the screen"""
        self.info_procs[self.info_n](rewrite)

    def post_scripts_line(self, rewrite=False):
        """Display information about the post scripts"""
        n = len(self.slist.current().post_scripts())
        fmt = "{} post script"
        if n != 1:
            fmt = fmt + 's'
        self.write_queue.put( { 'action': 'write',
                                'pos': [self.INFO_X,1],
                                'text': fmt.format(n),
                                'blank': 1 } )

    def ip_line(self, rewrite=False):
        """Display the IP address"""
        ip_addr = subprocess.check_output("hostname --all-ip-addresses", shell=True).decode('utf-8')[:-1]
        if ip_addr == '':
            ip_addr = 'No IP address'
        self.write_queue.put( { 'action': 'write', 'pos': [self.INFO_X,1], 'text': ip_addr, 'blank': 1 } )

    def cpu_temp(self, rewrite=False):
        """Display the CPU temperature"""
        cpu_temp = subprocess.check_output("/opt/vc/bin/vcgencmd measure_temp", shell=True).decode('utf-8')[:-1]
        m = re.search(r"temp=(.+)",cpu_temp)
        if m == None or m.group(1) == '':
            message = 'Cannot get temperature'
        else:
            message = m.group(1)
        self.write_queue.put( { 'action': 'write', 'pos': [self.INFO_X,1], 'text': message, 'blank': 1 } )

    def devices_line(self, rewrite=False):
        """Display the devices line on the LCD"""
        if rewrite or self.n_devices != len(self.disks):
            # Number of devices has changed
            self.n_devices = len(self.disks)
            self.device_state = [0]*self.MAX_DEVICES
            for dev in range(self.MAX_DEVICES):
                #name = self.disks.device_name(dev)
                name = self.disks[dev]
                if name == None:
                    # No device
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [self.INFO_X + dev*7, 1],
                                            'text': ' '*8 } )
                else:
                    if self.disks.device_present(dev):
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [self.INFO_X + dev*7, 1],
                                                'bitmap': self.SELECTED} )
                    else:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [self.INFO_X + dev*7, 1],
                                                'bitmap': self.UNSELECTED} )
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [self.INFO_X + dev*7 + 1, 1],
                                            'text': '{0: <6}'.format(os.path.basename(str(name))) } )
        else:
            for dev in range(self.MAX_DEVICES):
                if self.disks.device_present(dev):
                    if self.device_state[dev] == 0:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [dev*8,1],
                                                'pos': [self.INFO_X + dev*7, 1],
                                                'bitmap': self.SELECTED } )
                        self.device_state[dev] = 1
                else:
                    if self.device_state[dev] == 1:
                        self.write_queue.put( { 'action': 'bitmap',
                                                'pos': [self.INFO_X + dev*7, 1],
                                                'bitmap': self.UNSELECTED } )
                        self.device_state[dev] = 0

    def menu(self):
        # TODO Use this to have an exit button
        self.finish = 0

        self.refresh()
        self.updates = True

        self.setup_controls()
        self.listener.activate()

        while self.finish == 0:
            if self.is_pressed and self.display == self.DISPLAY_MAIN:
                if (self.press_start > 0 and
                    self.countdown > 0 and
                    int(time.time() - self.press_start) > self.PRESS_TIME - self.countdown):
                    self.countdown = self.countdown - 1
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [9, 1],
                                            'text': str(self.countdown) } )

            elif self.scroll:
                self.write_queue.put( { 'action': 'scroll',
                                        'step': 1 } )
                time.sleep(0.3)

            elif self.updates and self.display == self.DISPLAY_MAIN:
                self.show_device(self.INFO_X, 1)
                #self.info_line()
                time.sleep(1)
            else:
                # Avoid burning the CPU
                time.sleep(0.2)

    def prev(self, event):
        print("In prev")
        print("Pointer:", self.pointer_pos)
        if self.pointer_pos == 0:
            img = self.slist.prev().name
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': img } )
        elif self.pointer_pos == 1:
            drive = self.disks.prev()
            self.show_device(self.IMG_X, 1)

    def next(self, event):
        print("In next")
        if self.pointer_pos == 0:
            img = self.slist.next().name
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': img } )
        elif self.pointer_pos == 1:
            drive = self.disks.next()
            self.show_device(self.IMG_X, 1)

    def show_device(self, x, y):
        if self.disks.current() == None:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [x, y],
                                    'text': '' } )
        else:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [x + 1, y],
                                    'text': self.disks.current() } )
            if self.disks.current() != None and self.disks.current().present:
                self.write_queue.put( { 'action': 'bitmap',
                                        'pos': [x, y],
                                        'bitmap': self.SELECTED} )
            else:
                self.write_queue.put( { 'action': 'bitmap',
                                        'pos': [x, y],
                                        'bitmap': self.UNSELECTED} )

    def scroll_on(self, event):
        self.scroll = True

    def scroll_off(self, event):
        self.scroll = False
        self.refresh()

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

        'action': 'scroll'        - Scroll a line
        'step': <int>             - Places to scroll

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
            m = ''
            if m != None:
                m = str(message['text'])
            text_len = len(m)
            if ( message['pos'][0] + text_len < line_length[message['pos'][1]]
                 and 'blank' in message and message['blank'] ):
                ln = line_length[message['pos'][1]] - message['pos'][0]
                line_length[message['pos'][1]] = message['pos'][0] + text_len 
            else:
                ln = text_len 
                new_ln = message['pos'][0] + len(m)
                if new_ln > line_length[message['pos'][1]]:
                   line_length[message['pos'][1]] = new_ln
            cad.lcd.write(('{:<' + str(ln) + '}').format(m))
        elif message['action'] == 'store':
            cad.lcd.store_custom_bitmap(message['bitmap'], message['lines'])
        elif message['action'] == 'bitmap':
            cad.lcd.set_cursor(message['pos'][0], message['pos'][1])
            cad.lcd.write_custom_bitmap( message['bitmap'] )
        elif message['action'] == 'clear':
            cad.lcd.clear()
        elif message['action'] == 'scroll':
            while message['step'] != 0:
                if message['step'] > 0:
                    cad.lcd.move_left()
                    message['step'] = message['step'] - 1
                elif message['step'] < 0:
                    cad.lcd.move_right()
                    message['step'] = message['step'] + 1
        else:
            # Avoid burning the CPU
            time.sleep(0.2)
