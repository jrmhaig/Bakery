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

## Operation

Currently, this will assume that there is an image called:

    /home/pi/images/wheezy-raspbian.img.gz

and there is an a storage device mounted at:

    /dev/sda

This image will then be unzipped and written directly to the disk.

To run:

    python3 bakery3.py

## Limitations

* Image writing starts immediately without confirmation.
* The image is not checked to exist.
* /dev/sda is not checked to exist.
* There is no way to select different images.
* Feedback requires a monitor. 

Communication will be done via a PiFace CAD.
