import pifacecad
from time import sleep, time

class BakeryDisplay:
    def __init__(self, write_function):
        self.write_function = write_function

        self.cad = pifacecad.PiFaceCAD()
        self.cad.lcd.backlight_on()
        self.cad.lcd.cursor_off()
        self.cad.lcd.blink_off()
        self.listener = pifacecad.SwitchEventListener(chip=self.cad)
        self.listener.register(4, pifacecad.IODIR_FALLING_EDGE, self.pressed)
        self.listener.register(4, pifacecad.IODIR_RISING_EDGE, self.released)
        self.listener.activate()

        self.part_block = []
        n = 0
        for i in range(4,-1,-1):
            n = n + (2**i)
            self.part_block.append( pifacecad.LCDBitmap([n]*8) )
        self.cad.lcd.store_custom_bitmap(1, self.part_block[4])

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

            self.write_function(self)

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
