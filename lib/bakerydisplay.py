import pifacecad
import pifacecad.tools
import multiprocessing
import threading
import time
import os.path
import socket
import subprocess
import re
import lib.utils as utils
import distutils.dir_util

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
    BUTTON_COPY_Y = 1
    BUTTON_COPY_N = 2
    BUTTON_SCROLL = 3
    BUTTON_WRITE = 4     # For main view
    BUTTON_SCAN = 4      # For load view
    BUTTON_EXECUTE = 4   # For system view
    BUTTON_INFO = 5
    BUTTON_PREV = 6
    BUTTON_NEXT = 7

    # Displays
    DISPLAY_MAIN = 0
    DISPLAY_LOAD = 1
    DISPLAY_DELETE = 2
    DISPLAY_SYSTEM = 3
    DISPLAY_LOAD_YN = 98
    DISPLAY_WRITING = 99
    DISPLAY_FIRST = DISPLAY_MAIN
    DISPLAY_LAST = DISPLAY_SYSTEM

    def __init__(self, disks, source_dir, write_function):
        # Callback function for writing to the device
        self.write_function = write_function
        self.source_dir = source_dir

        self.disks = disks
        self.images = utils.disk_image_list(self.source_dir)
        self.main_lines = [
            {
              'source': self.images,
              'info': [ 'name', 'n_post_scripts', 'n_variables' ],
              'x': 1,
            },
            {
              'source': disks,
              'info': [ 'model', 'node_path' ],
              'x': 2,
            }
          ]
        self.pointer_pos = 0
        self.info_n = 0

        self.load_line = {
            'source': disks,
            'info': [ 'model', 'node_path' ],
            'x': 1
          }

        self.delete_line = {
            'source': self.images,
            'info': [ 'name', 'n_post_scripts', 'n_variables' ],
            'x': 1
          }

        self.system_data = [
            self.ip_address,
            self.cpu_temp,
            self.storage_total,
            self.storage_used,
            self.storage_free,
            self.shutdown,
            self.reboot,
          ]
        self.system_n = 0


        # Send updates to display of devices
        self.updates = False
        # Whether button is pressed or not
        self.is_pressed = False

        self.cad = pifacecad.PiFaceCAD()
        self.listener = pifacecad.SwitchEventListener(chip=self.cad)

        self.scroll = False

        self.display = self.DISPLAY_FIRST

        self.write_queue = multiprocessing.Queue()
        self.writer = threading.Thread( target = _lcd_writer,
                                        args = ( self.write_queue, self.cad ) )

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

    def __del__(self):
        self.cad.lcd.backlight_off()

    def pressed(self, event):
        """Button has been pressed

        Start a counter so that writing only starts when the button has been
        pressed for five seconds.

        """
        if self.main_lines[1]['source'].current().present == False:
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 0],
                                    'text': 'No disk present ' } )
            self.press_start = -1
            time.sleep(3)
            self.refresh()
        else:
            self.press_start = time.time()
            self.is_pressed = True
            self.countdown = self.PRESS_TIME
            self.counter_pos = [ 9, 1 ]
            self.write_queue.put( { 'action': 'clear queue' } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 1],
                                    'text': 'Write in {0} secs '.format(self.PRESS_TIME) } )

    def released(self, event):
        """Button has been released

        Only call the callback function if the button has been pressed for
        five seconds. Otherwise, do nothing.

        """
        if not self.is_pressed:
            # Got here by cosmic rays, or some such.
            return None
        self.is_pressed = False
        if self.press_start > 0 and time.time() > self.press_start + self.PRESS_TIME:
            self.write_queue.put( { 'action': 'clear' } )

            # Keep track of progress
            self.progress_pointer=0

            self.updates = False

            start_time = time.time()

            # Turn off listeners while writing
            self.display == self.DISPLAY_WRITING
            self.setup_controls()

            if self.write_function( self.main_lines[1]['source'].current().path,
                                    self.main_lines[0]['source'].current(), self ):
                self.write_queue.put( { 'action': 'clear' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0,0],
                                        'text': '    FINISHED    ' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0,1],
                                        'text': '{0} seconds'.format(int(time.time() - start_time)) } )
                print("Time:", time.time() - start_time)
            else:
                self.write_queue.put( { 'action': 'clear' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0, 0],
                                        'text': 'Write failed' } )
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0, 1],
                                        'text': 'Try again' } )

            time.sleep(5)

            # Turn listeners back on
            self.display == self.DISPLAY_FIRST
            self.setup_controls()

            self.updates = True

        self.refresh()

    def system_pressed(self, event):
        """Button has been pressed

        System actions

        """
        if self.system_action:
            self.press_start = time.time()
            self.is_pressed = True
            self.countdown = self.PRESS_TIME
            self.counter_pos = [ 3, 1 ]
            self.write_queue.put( { 'action': 'clear queue' } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 0],
                                    'blank': 1,
                                    'text': self.system_action } )
            self.write_queue.put( { 'action': 'write',
                                    'pos': [0, 1],
                                    'blank': 1,
                                    'text': 'in {0} secs '.format(self.PRESS_TIME) } )

    def system_released(self, event):
        """Button has been released

        Only call the system action if the button has been pressed for
        five seconds. Otherwise, do nothing.

        """
        if not self.is_pressed:
            # Got here by cosmic rays, or some such.
            return None
        self.is_pressed = False
        if self.press_start > 0 and time.time() > self.press_start + self.PRESS_TIME:
            if self.system_action == 'Shutdown':
                subprocess.call(['shutdown', '-h', 'now'])
            elif self.system_action == 'Reboot':
                subprocess.call(['shutdown', '-r', 'now'])

        self.refresh()

    def switch_pointer(self, event):
        """Switch the pointer between lines"""
        self.write_queue.put( { 'action': 'write',
                                'pos': [0, self.pointer_pos],
                                'text': ' ' } )
        self.pointer_pos = 1 - self.pointer_pos
        if self.info_n > 0:
            self.info_n = 0
            self.refresh()
        else:
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [0, self.pointer_pos],
                                    'bitmap': self.POINTER } )

    def show_info(self, event):
        """Display information"""
        self.info_n += 1
        if self.info_n >= len(self.main_lines[self.pointer_pos]['info']):
            self.info_n=0
        line = self.main_lines[self.pointer_pos]
        key = line['info'][self.info_n]
        self.write_queue.put( { 'action': 'write',
                                'pos': [line['x'], self.pointer_pos ],
                                'text': line['source'].current().info(key),
                                'blank': 1 } )

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
        self.listener.deregister()

        # Settings for all displays
        # Scroll display
        self.listener.register( self.BUTTON_SCROLL,
                                pifacecad.IODIR_FALLING_EDGE,
                                self.scroll_on )
        self.listener.register( self.BUTTON_SCROLL,
                                pifacecad.IODIR_RISING_EDGE,
                                self.scroll_off )

        if self.display == self.DISPLAY_MAIN:
            # Previous and next
            self.listener.register( self.BUTTON_PREV,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.main_prev )
            self.listener.register( self.BUTTON_NEXT,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.main_next )
            # Write image
            self.listener.register( self.BUTTON_WRITE,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.pressed )
            self.listener.register( self.BUTTON_WRITE,
                                    pifacecad.IODIR_RISING_EDGE,
                                    self.released )

            # Move pointer between lines
            self.listener.register( self.BUTTON_POINTER,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_pointer )

            # Show further information
            self.listener.register( self.BUTTON_INFO,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.show_info )

            # Switch through displays
            self.listener.register( self.BUTTON_SELECT_DISPLAY,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_display )

        elif self.display == self.DISPLAY_LOAD:
            # Previous and next
            self.listener.register( self.BUTTON_PREV,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.load_prev )
            self.listener.register( self.BUTTON_NEXT,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.load_next )
            # Scan partitions
            self.listener.register( self.BUTTON_SCAN,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.scan_device )

            # Switch through displays
            self.listener.register( self.BUTTON_SELECT_DISPLAY,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_display )

        elif self.display == self.DISPLAY_DELETE:
            # Previous and next
            self.listener.register( self.BUTTON_PREV,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.delete_prev )
            self.listener.register( self.BUTTON_NEXT,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.delete_next )

            # Switch through displays
            self.listener.register( self.BUTTON_SELECT_DISPLAY,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_display )

        elif self.display == self.DISPLAY_LOAD_YN:
            print("Setting listeners")
            # Copy or pass on an image
            self.listener.register( self.BUTTON_COPY_Y,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.copy_image )
            self.listener.register( self.BUTTON_COPY_N,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.pass_image )
            # Scan partitions
            self.listener.register( self.BUTTON_SCAN,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.scan_device )
            print(self.listener.pin_function_maps)

        elif self.display == self.DISPLAY_SYSTEM:
            # Previous and next
            self.listener.register( self.BUTTON_PREV,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.system_prev )
            self.listener.register( self.BUTTON_NEXT,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.system_next )
            # System action
            self.listener.register( self.BUTTON_EXECUTE,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.system_pressed )
            self.listener.register( self.BUTTON_EXECUTE,
                                    pifacecad.IODIR_RISING_EDGE,
                                    self.system_released )

            # Switch through displays
            self.listener.register( self.BUTTON_SELECT_DISPLAY,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.switch_display )

        elif self.display == self.DISPLAY_WRITING:
            # No listeners during writing
            pass

    def progress_title(self):
        """Display the title for the progress bar"""
        self.write_queue.put( { 'action': 'clear', } )
        self.write_queue.put( { 'action': 'write',
                                'pos': [0,0],
                                'text': 'Complete:      %' } )

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
                                    'pos': [self.main_lines[0]['x'],0],
                                    'text': self.main_lines[0]['source'].current().name } )

            # Device
            self.show_device(self.main_lines[1]['x'], 1)

        elif self.display == self.DISPLAY_SYSTEM:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [0,0],
                                    'text': "System status" } )
            self.show_system_data()
        elif self.display == self.DISPLAY_LOAD:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [0,0],
                                    'text': "Load images" } )
            # Device
            self.show_device(self.load_line['x'], 1)

        elif self.display == self.DISPLAY_DELETE:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [0,0],
                                    'text': "Delete images" } )
            # Device
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.delete_line['x'],1],
                                    'text': self.images.current().name } )

    def show_system_data(self, rewrite=False):
        """Write the second line of the screen"""
        self.system_data[self.system_n](rewrite)

    def ip_address(self, rewrite=False):
        """Display the IP address"""
        self.system_action = None
        ip_addr = subprocess.check_output("hostname --all-ip-addresses", shell=True).decode('utf-8')[:-1]
        if ip_addr == '':
            ip_addr = 'No IP address'
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': ip_addr, 'blank': 1 } )

    def cpu_temp(self, rewrite=False):
        """Display the CPU temperature"""
        self.system_action = None
        cpu_temp = subprocess.check_output("/opt/vc/bin/vcgencmd measure_temp", shell=True).decode('utf-8')[:-1]
        m = re.search(r"temp=(.+)",cpu_temp)
        if m == None or m.group(1) == '':
            message = 'Cannot get temperature'
        else:
            message = m.group(1)
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': message, 'blank': 1 } )

    def storage_used(self, rewrite=False):
        """Display storage information"""
        self.system_action = None
        df = os.statvfs( self.source_dir )
        gb = 1024.0*1024.0*1024.0
        used = ( df.f_blocks - df.f_bfree ) * df.f_frsize / gb
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': "{0:.1f}G used".format(used, used), 'blank': 1 } )

    def storage_free(self, rewrite=False):
        """Display storage information"""
        self.system_action = None
        df = os.statvfs( self.source_dir )
        gb = 1024.0*1024.0*1024.0
        free = df.f_bavail * df.f_frsize / gb
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': "{0:.1f}G free".format(free, free), 'blank': 1 } )

    def storage_total(self, rewrite=False):
        """Display storage information"""
        self.system_action = None
        df = os.statvfs( self.source_dir )
        gb = 1024.0*1024.0*1024.0
        total = df.f_blocks * df.f_frsize / gb
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': "{1:.1f}G total".format(total, total), 'blank': 1 } )

    def shutdown(self, rewrite=False):
        self.system_action = 'Shutdown'
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': 'Shutdown', 'blank': 1 } )

    def reboot(self, rewrite=False):
        self.system_action = 'Reboot'
        self.write_queue.put( { 'action': 'write', 'pos': [0, 1], 'text': 'Reboot', 'blank': 1 } )

    def menu(self):
        # TODO Use this to have an exit button
        self.finish = 0

        self.refresh()
        self.updates = True

        self.setup_controls()
        self.listener.activate()

        while self.finish == 0:
            if self.is_pressed:
                if (self.press_start > 0 and
                    self.countdown > 0 and
                    int(time.time() - self.press_start) > self.PRESS_TIME - self.countdown):
                    self.countdown = self.countdown - 1
                    self.write_queue.put( { 'action': 'write',
                                            'pos': self.counter_pos,
                                            'text': str(self.countdown) } )

            elif self.scroll:
                self.write_queue.put( { 'action': 'scroll',
                                        'step': 1 } )
                time.sleep(0.3)

            elif self.updates and (self.display == self.DISPLAY_MAIN or self.display == self.DISPLAY_LOAD):
                # TODO Check for change of devices list
                x = 0
                if self.display == self.DISPLAY_MAIN:
                    x = self.main_lines[1]['x']-1
                else:
                    x = self.load_line['x']-1
                self.show_device_state(x, 1)
                time.sleep(1)
            else:
                # Avoid burning the CPU
                time.sleep(0.2)

    # Functions for left and right rocker switch

    def main_prev(self, event):
        self.info_n = 0
        if self.pointer_pos == 0:
            img = self.main_lines[0]['source'].prev().name
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': img } )
        elif self.pointer_pos == 1:
            drive = self.disks.prev()
            self.show_device(self.main_lines[1]['x'], 1)

    def main_next(self, event):
        self.info_n = 0
        if self.pointer_pos == 0:
            img = self.main_lines[0]['source'].next().name
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [self.IMG_X,0],
                                    'text': img } )
        elif self.pointer_pos == 1:
            drive = self.disks.next()
            self.show_device(self.main_lines[1]['x'], 1)

    def load_prev(self, event):
        #self.info_n = 0
        drive = self.disks.prev()
        self.show_device(self.load_line['x'], 1)

    def load_next(self, event):
        drive = self.disks.next()
        self.show_device(self.load_line['x'], 1)

    def delete_prev(self, event):
        #self.info_n = 0
        img = self.images.prev()
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [self.delete_line['x'],1],
                                'text': img.name } )

    def delete_next(self, event):
        img =self.images.next()
        self.write_queue.put( { 'action': 'write',
                                'blank': 1,
                                'pos': [self.delete_line['x'],1],
                                'text': img.name } )

    def system_prev(self, event):
        if self.system_n == 0:
            self.system_n = len(self.system_data)
        self.system_n -= 1
        self.show_system_data()

    def system_next(self, event):
        self.system_n += 1
        if self.system_n >= len(self.system_data):
            self.system_n = 0
        self.show_system_data()

    def scan_device(self, event):
        if self.disks.current() != None and self.disks.current().present:
            self.updates = False
            partitions = utils.get_device_partitions(self.disks.current().path)
            self.copy_dir = None
            tmp_listener = pifacecad.SwitchEventListener(chip=self.cad)
            tmp_listener.register( self.BUTTON_COPY_Y,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.copy_image )
            tmp_listener.register( self.BUTTON_COPY_N,
                                    pifacecad.IODIR_FALLING_EDGE,
                                    self.pass_image )
            tmp_listener.activate()
            for partition in partitions:
                self.write_queue.put( { 'action': 'write',
                                        'pos': [0, 0],
                                        'blank': 1,
                                        'text': partition} )
                mnt = utils.mount(partition)
                if mnt:
                    self.write_queue.put( { 'action': 'write',
                                            'pos': [0, 1],
                                            'blank': 1,
                                            'text': "Scanning ..."} )
                    images = utils.scan(mnt)
                    for dir in images:
                        self.write_queue.put( { 'action': 'write',
                                                'pos': [0, 0],
                                                'blank': 1,
                                                'text': images[dir]} )
                        self.write_queue.put( { 'action': 'write',
                                                'pos': [0, 1],
                                                'blank': 1,
                                                'text': "Y N"} )
                        self.do_copy = None
                        while self.do_copy == None:
                            pass
                        if self.do_copy == 1:
                            self.write_queue.put( { 'action': 'write',
                                                    'pos': [0, 1],
                                                    'blank': 1,
                                                    'text': "Copying ..."} )
                            # Find a nunique directory name
                            i = 1
                            while os.path.exists(self.source_dir + "/{0:06d}".format(i)):
                                i+=1
                            new_dir = self.source_dir + "/{0:06d}".format(i)
                            os.mkdir(new_dir)
                            distutils.dir_util.copy_tree( dir, new_dir )
                            self.main_lines[0]['source'] = utils.disk_image_list(self.source_dir)
                        #time.sleep(60)
                    utils.umount(mnt)
            tmp_listener.deactivate()
            self.refresh()
            self.updates = True

    def copy_image(self, event):
        self.do_copy = 1

    def pass_image(self, event):
        self.do_copy = 0

    def show_device_state(self, x, y):
        if self.disks.current() != None and self.disks.current().present:
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [x, y],
                                    'bitmap': self.SELECTED} )
        else:
            self.write_queue.put( { 'action': 'bitmap',
                                    'pos': [x, y],
                                    'bitmap': self.UNSELECTED} )

    def show_device(self, x, y):
        if self.disks.current() == None:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [x, y],
                                    'text': '' } )
        else:
            self.write_queue.put( { 'action': 'write',
                                    'blank': 1,
                                    'pos': [x, y],
                                    'text': self.disks.current() } )
        self.show_device_state(x-1, y)

    def scroll_on(self, event):
        self.scroll = True

    def scroll_off(self, event):
        self.scroll = False
        self.refresh()

    def question(self, label, fmt):
        self.write_queue.put( { 'action': 'pause' } )

        self.cad.lcd.clear()
        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write(label)

        self.cad.lcd.set_cursor(0, 1)
        self.cad.lcd.cursor_on()
        self.cad.lcd.blink_on()
        if ':' in fmt:
            (f, args) = fmt.split(':', 1)
            scanner = pifacecad.tools.LCDScanf(format=f, custom_values=args.split(','), cad=self.cad)
        else:
            scanner = pifacecad.tools.LCDScanf(format=fmt, cad=self.cad)

        answer = scanner.scan()
        self.cad.lcd.cursor_off()
        self.cad.lcd.blink_off()
        self.write_queue.put( { 'action': 'resume' } )
        return answer[0]

def _lcd_writer(queue, cad):
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

        'action': 'clear queue'   - Remove all items from the standard queue

        'action': 'pause'         - Pause writing to the LCD

        'action': 'resume'        - Resume writing to the LCD

    """
    #cad = pifacecad.PiFaceCAD()
    cad.lcd.backlight_on()
    cad.lcd.cursor_off()
    cad.lcd.blink_off()
    line_length = [0, 0]

    standard_queue = []
    background_queue = []

    pause = False

    while True:
        seek = True
        while seek:
            try:
                message = queue.get(False)
                if message['action'] == 'pause':
                    pause = True
                elif message['action'] == 'resume':
                    pause = False
                elif message['action'] == 'store':
                    background_queue.append(message)
                elif message['action'] == 'clear queue':
                    standard_queue = []
                else:
                    standard_queue.append(message)
            except:
                seek = False

        message = None
        if not pause:
            if len(standard_queue) > 0:
                message = standard_queue[0]
                standard_queue = standard_queue[1:]
            elif len(background_queue) > 0:
                message = background_queue[0]
                background_queue = background_queue[1:]

        if message == None:
            # Avoid burning the CPU
            time.sleep(0.2)
        else:
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
