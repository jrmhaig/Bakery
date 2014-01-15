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

* PiFace Control and Display

## Operation

Run with:

    sudo python3 bakery.py

Images are found in /home/pi/images and should be gzipped.
Use the rocker switch to move between different images and press to select.
Press and hold button number 5 for five seconds to write the image to the SD
card. The progress will be written on the display.

## Limitations

* /dev/sda is not checked to exist.
* Needs to be run with sudo. Can this be avoided?
* No 'exit' button.
* Does not start on boot.
* It would be useful to mount and configure the image after installing.
* It doesn't deal well with no image being selected.
* Selecting images is a bit slow. Does it need to clear the screen eachh time?
* Any files in /home/pi/images will be listed but only .gz files will work.
