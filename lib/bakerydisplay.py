import pifacecad
from os.path import basename
from time import sleep, time

class BakeryDisplay:

    # Only use up to two devices
    # Without a USB hub, there cannot be any more on a Raspberry Pi
    MAX_DEVICES=2

    def __init__(self, disks, slist, write_function):
        # Callback function for writing to the device
        self.write_function = write_function

        # List of images available
        self.slist = slist

        # Watcher for disks & devices
        self.disks = disks
        # Number of devices present
        self.n_devices = 0
        # Send updates to display of devices
        self.updates = False

        self.cad = pifacecad.PiFaceCAD()
        self.cad.lcd.backlight_on()
        self.cad.lcd.cursor_off()
        self.cad.lcd.blink_off()
        self.listener = pifacecad.SwitchEventListener(chip=self.cad)
        self.listener.register(4, pifacecad.IODIR_FALLING_EDGE, self.pressed)
        self.listener.register(4, pifacecad.IODIR_RISING_EDGE, self.released)
        self.listener.register(5, pifacecad.IODIR_FALLING_EDGE, self.select)
        self.listener.register(6, pifacecad.IODIR_FALLING_EDGE, self.prev)
        self.listener.register(7, pifacecad.IODIR_FALLING_EDGE, self.next)

        self.part_block = []
        n = 0
        for i in range(4,-1,-1):
            n = n + (2**i)
            self.part_block.append( pifacecad.LCDBitmap([n]*8) )
        self.cad.lcd.store_custom_bitmap(1, self.part_block[4])

    def __del__(self):
        self.cad.lcd.backlight_off()

    def pressed(self, event):
        """Button has been pressed

        Start a counter so that writing only starts when the button has been
        pressed for five seconds.

        """
        self.press_time = time()

    def released(self, event):
        """Button has been released

        Only call the callback function if the button has been pressed for
        five seconds. Otherwise, do nothing.

        """
        if time() > self.press_time + 5:
            self.cad.lcd.clear()

            # Top line
            self.cad.lcd.set_cursor(0, 0)
            self.cad.lcd.write("Complete:  0.00%")

            # Second line
            self.progress_pointer=0
            self.cad.lcd.store_custom_bitmap(0, self.part_block[0])
            self.cad.lcd.set_cursor(0, 1)
            self.cad.lcd.write_custom_bitmap(0)

            self.updates = False
            self.write_function(self)

            sleep(5)
            self.refresh()
            self.updates = True

    def progress(self, percent):
        """Display the progress

        Write the percentage progress and show a progress bar on the LCD.
        A percentage of -1 indicates completion.

        """
        if percent == -1:
            self.cad.lcd.clear()
            self.cad.lcd.set_cursor(0, 0)
            self.cad.lcd.write("    FINISHED    ")
        else:
            self.cad.lcd.set_cursor(10, 0)
            self.cad.lcd.write("{0:5.2f}".format(percent))
            k = percent / 6.125   #    percent * 16 / 100
            l = int(k)            #    Number of complete blocks
            m = int((k - l) * 5)  #    Number of lines in partial block

            # Wrapped in an 'if' block to save a bit of time
            # Writing a character is slow - avoid if possible
            if self.progress_pointer < l:
                while self.progress_pointer < l:
                    self.cad.lcd.set_cursor(self.progress_pointer, 1)
                    self.cad.lcd.write_custom_bitmap(1)
                    self.progress_pointer = self.progress_pointer + 1

                self.cad.lcd.set_cursor(self.progress_pointer, 1)
                self.cad.lcd.store_custom_bitmap(0, self.part_block[m])
                self.cad.lcd.write_custom_bitmap(0)
            else:
                # Don't need to re-write character. Just change the bitmap.
                self.cad.lcd.store_custom_bitmap(0, self.part_block[m])

    def refresh(self):
        """Refresh the screen for the menu"""
        self.cad.lcd.clear()

        # Image name
        self.cad.lcd.write(self.slist.current())

        # Device
        self.devices_line(True)

    def devices_line(self, rewrite=False):
        """Display the devices line on the LCD"""
        if rewrite or self.n_devices != len(self.disks.watching):
            # Number of devices has changed
            self.n_devices = len(self.disks.watching)
            self.device_state = []
            # Not expecting more than two. Ignore any more
            # Write present drives
            for present in range(min(self.n_devices, self.MAX_DEVICES)):
                self.cad.lcd.set_cursor(present*8, 1)
                if self.disks.watching[present] in self.disks.devices:
                    self.cad.lcd.write_custom_bitmap(1)
                    self.device_state.append(1)
                else:
                    self.cad.lcd.write('_')
                    self.device_state.append(0)
                self.cad.lcd.write(' {0: <6}'.format(basename(self.disks.watching[present])))

            # Blank out missing drives
            for absent in range(min(self.n_devices, self.MAX_DEVICES), self.MAX_DEVICES):
                self.cad.lcd.set_cursor(absent*8, 1)
                self.cad.lcd.write(' '*8)
        else:
            for present in range(min(self.n_devices, self.MAX_DEVICES)):
                if self.device_state[present] == 0:
                    if self.disks.watching[present] in self.disks.devices:
                        self.device_state[present] = 1
                        self.cad.lcd.set_cursor(present*8, 1)
                        self.cad.lcd.write_custom_bitmap(1)
                else:
                    if self.disks.watching[present] not in self.disks.devices:
                        self.device_state[present] = 0
                        self.cad.lcd.set_cursor(present*8, 1)
                        self.cad.lcd.write('_')

    def menu(self):
        # TODO Use this to have an exit button
        self.finish = 0

        self.listener.activate()

        self.refresh()
        self.updates = True

        while self.finish == 0:
            if self.updates:
                self.devices_line()

    def prev(self, event):
        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write(self.slist.prev())

    def next(self, event):
        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write(self.slist.next())

    def select(self, event):
        self.slist.select()
        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write(self.slist.current())
