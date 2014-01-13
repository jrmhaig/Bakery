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
            self.cad.lcd.set_cursor(0, 0)
            self.cad.lcd.write("Complete:  0.00%")
            self.cad.lcd.set_cursor(0, 1)
            self.cad.lcd.write("................")
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
            l = int(16 * percent / 100)
            self.cad.lcd.set_cursor(0, 1)
            self.cad.lcd.write('X'*l)
