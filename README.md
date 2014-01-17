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
* USB to SD adapter

### Set up

Extract Bakery into:

    /home/pi/Bakery

Either start Bakery manually, as shown in the 'Operation' section below, or
set it to start on boot by copying the file:

    /home/pi/Bakery/init.d/bakery

to `/etc/init.d`, making sure that it is executable, and running:

    sudo update-rc.d bakery defaults

## Operation

Run with:

    sudo python3 bakery.py

Images are found in /home/pi/images and should be gzipped.
Use the rocker switch to move between different images and press to select.
Press and hold button number 5 for five seconds to write the image to the SD
card. The progress will be written on the display.

## Images

Images (and only images) should be stored in the directory

    /home/pi/images

zipped up with:

    gzip image.img

so that the file has a `.img.gz` extension.

Note that images provided by distributions may be packaged up in various forms,
such as tar, tar.gz and zip. None of these will work so you will need to unpack
them and gzip the image.

## To do list

* Can it be run without sudo? Is this necessary?
* Add an 'exit' button.
* It would be useful to mount and configure the image after installing.
* Any files in /home/pi/images will be listed but only .img.gz files will work.
  It may be helpful to structure this in such a way that there can be other
  files, such as README files.
* I am having problems with the USB-SD adapter arbitrarily remounting. I don't
  know if this is to do with the SD card, the adapter or the power supply.
* Switching between images doesn't overwrite properly if the new name is
  shorter than the old.
* Why does the image selector look like '[ ]' while the device indicator is a
  single character? Decide on one or the other!
* If an image is not selected or a disk is not present it shouldn't print
  'Completed 0.00%' before printing the error message.
* The list of devices is now scanned when Bakery starts up. The first disk,
  the one attached to the upper USB port, is still used for writing. Currently,
  devices that are added later are not detected. These should be detected and
  the display updated as appropriate. Then, it should be possible to mount a
  new device and find new disk images to use, so as to provide external
  storage and a way to copy new images on to the Pi.
* The 'no SD card' mark is a '_' character, which isn't quite the bottom line.
  Make a new bitmap for the bottom line to look better with the block.
* No easy way to copy new images on when not connected to a network. Need to
  have a feature to use external USB storage, either writing images directly
  from one or copying them onto the Pi.
* When a disk is being written, the disk detector could clean up if the SD
  card is removed. At the moment it just gets messed up.
