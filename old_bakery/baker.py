from lib.selectlist import *
from lib.iface import *
#from lib.udevevents import *
from lib.diskdetector import *
import configparser
from time import sleep

config = configparser.ConfigParser()
config.read('baker.cfg')

dirs = config.get('images', 'source')

#sdi = SdImages(*[dirs])
sdi = disk_image_list(*[dirs])
#udev = UdevEventListener()
disk = DiskEventListener()

#iface = ITools.hw_connect( sdi, udev )
iface = ITools.hw_connect( sdi, disk )

iface.loop()
iface.cleanup()