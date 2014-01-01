import pifacecad
import pifacedigitalio
from lib.udevevents import *
from time import sleep

class ITools:
    def hw_connect( images, udev ):
        """Factory method to connect to whatever harware is available."""
        try:
            return IFace_PiFaceCAD( images, udev )
        except pifacecad.core.NoPiFaceCADDetectedError:
            print("No PiFace CAD attached")
        
        try:
            return IFace_PiFaceDigital( images, udev )
        except pifacedigitalio.core.NoPiFaceDigitalDetectedError:
            print("No PiFace Digital attached")
        
        return HWInter( images )

class IFace:

    def __init__(self, images, udev):
        self.images = images
        self.images.pointer = 0

        self.udev_listener = udev
        self.udev_listener.activate()

        self.initialise()
        self.alert()

    def cleanup(self):
        self.udev_listener.deactivate()

    def alert(self):
        """Display an alert"""
        print("Ready to go with:", self.hw_name)

    def error(self, message):
        """Display an error"""
        print("Error!\n" + message)
        self.log('error', message)
        exit(1)

    def initialise(self):
        """Configuration variables

        Variables that are determined by the hardware type.
        This function should be replaced in all child classes.

        """
        self.hw_name = 'No hardware'

    def log(level, message):
        """Todo"""
        pass

    def loop():
        print("To do - loop for the basic case")
        exit(1)

class IFace_PiFaceCAD(IFace):

    def __init__(self, images, udev):
        self.hw = pifacecad.PiFaceCAD()
        super().__init__(images, udev)

    def initialise(self):
        self.hw_name = 'PiFace Control and Display'

    def alert(self):
        for i in range(3):
            self.hw.lcd.backlight_on()
            sleep(0.2)
            self.hw.lcd.backlight_off()
            sleep(0.2)
        self.hw.lcd.backlight_on()

    def error(self, message):
        self.hw.lcd.write("ERROR\n" + message)
        exit(1)

    def select_image(self, event):
        self.images.select()
        self.hw.lcd.clear()
        self.hw.lcd.write(self.images.current())

    def prev_image(self, event):
        self.hw.lcd.clear()
        self.hw.lcd.write(self.images.prev())

    def next_image(self, event):
        self.hw.lcd.clear()
        self.hw.lcd.write(self.images.next())

    def show_devices(self, event):
        self.hw.lcd.clear()
        if len(self.udev_listener.devices) == 0:
            self.hw.lcd.write('NONE')
        else:
            for dev in self.udev_listener.devices:
                self.hw.lcd.write(dev)

    def quit(self, event):
        self.hw.lcd.clear()
        self.finish = 1

    def loop(self):
        self.hw.lcd.write(self.images.current())
        self.finish = 0

        listener = pifacecad.SwitchEventListener(chip=self.hw)
        listener.register(5, pifacecad.IODIR_FALLING_EDGE, self.select_image)
        listener.register(6, pifacecad.IODIR_FALLING_EDGE, self.prev_image)
        listener.register(7, pifacecad.IODIR_FALLING_EDGE, self.next_image)
        listener.register(4, pifacecad.IODIR_FALLING_EDGE, self.quit)
        listener.register(0, pifacecad.IODIR_FALLING_EDGE, self.show_devices)
        listener.activate()

        while self.finish == 0:
            pass

        self.hw.lcd.clear()
        self.hw.lcd.write('Goodbye')
        listener.deactivate()

class IFace_PiFaceDigital(IFace):

    def __init__(self, images, udev):
        self.hw = pifacedigitalio.PiFaceDigital()
        super().__init__(images, udev)

    def initialise(self):
        if (len(self.images) > 8 ):
            self.error('Too many images for PiFace Digital')
        self.hw_name = 'PiFace Digital'

    def alert(self):
        for i in range(3):
            self.hw.output_port.value = 0xAA
            sleep(0.2)
            self.hw.output_port.value = 0x00
            sleep(0.2)

    def error(self, message):
        while True:
            self.hw.output_port.value = 0xAA
            sleep(1)
            self.hw.output_port.value = 0x00
            sleep(1)
