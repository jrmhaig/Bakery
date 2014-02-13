#!/usr/bin/python3

import configparser
import lib.bakerydisplay as bakerydisplay
import lib.diskdetector as diskdetector
import lib.utils as utils

# Look for configuration file and read it
config_files = [
                '/etc/bakery.cfg',
                'conf/bakery.cfg'
               ]
config = configparser.ConfigParser()
config.read( config_files )

# Get the list of images
dirs = config.get('images', 'source')
images = utils.disk_image_list(dirs)

# Listen for disks
disks = diskdetector.DiskEventListener()
disks.activate()

# Set up the display
display = bakerydisplay.BakeryDisplay(disks, images, utils.write_image)

# Run the main loop
display.menu()
