#!/usr/bin/python3
#
#   Copyright 2014 Joseph Haig
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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

# Get image directory
dirs = config.get('images', 'source')

# Listen for disks
disks = diskdetector.DiskEventListener()
disks.activate()

# Set up the display
display = bakerydisplay.BakeryDisplay(disks, dirs, utils.write_image)

# Run the main loop
display.menu()
