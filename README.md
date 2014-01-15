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

## Images

Images (and only images) should be stored in the directory

    /home/pi/images

zipped up with:

    gzip image.img

so that the file has a `.img.gz` extension.

Note that images provided by distributions may be packaged up in various forms,
such as tar, tar.gz and zip. None of these will work so you will need to unpack
them and gzip the image.

## Limitations

* /dev/sda is not checked to exist.
* Needs to be run with sudo. Can this be avoided?
* No 'exit' button.
* Does not start on boot.
* It would be useful to mount and configure the image after installing.
* It doesn't deal well with no image being selected.
* Selecting images is a bit slow. Does it need to clear the screen each time?
* Any files in /home/pi/images will be listed but only .img.gz files will work.
  It may be helpful to structure this in such a way that there can be other
  files, such as README files.
