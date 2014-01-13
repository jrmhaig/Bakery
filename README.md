# Bakery

Use a Pi to make a Pi

## Objective

Use the Raspberry Pi to write images to other SD cards. The primary objective
is to be able create new Raspberry Pi OS cards but it can obviously be used for
copying any images.

## WARNING 1

This software is designed to wipe and write to any SD card that you connect via
the USB connectors on a Raspberry Pi. There is obviously a real danger of data
loss if used without care.

## WARNING 2

Did you read WARNING 1? If not, go back and read it again.

## Requirements

### Hardware

* PiFace Control and Displa

## Operation

Currently, this will assume that there is an image called:

    /home/pi/images/wheezy-raspbian.img.gz

and there is an a storage device mounted at:

    /dev/sda

This image will then be unzipped and written directly to the disk.

To run:

    sudo python3 bakery.py

Press and hold button number 5 (the one separate from the others) for five
seconds. When you release the image will start to be written to the disk.
The progress is displayed on the LCD.

## Limitations

* Image writing starts immediately without confirmation.
* The image is not checked to exist.
* /dev/sda is not checked to exist.
* There is no way to select different images.
* Feedback requires a monitor. 
* Needs to be run with sudo. Can this be avoided?
* Progress bar should be made up of blocks instead of 'X's.
* No 'exit' button.
