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

### Software

* python3-pifacecad
* python3-pyudev

### Set up

Extract Bakery into:

    /home/pi/Bakery

Either start Bakery manually, as shown in the 'Operation' section below, or
set it to start on boot by copying the file:

    /home/pi/Bakery/init.d/bakery

to `/etc/init.d`, making sure that it is executable, and running:

    sudo update-rc.d bakery defaults

## Configuration

Bakery looks for a configuration file called `bakery.cfg` either in the
current directory or in `/etc`. This should contain:

    [images]
    source=/path/to/images/directory

The images inside this directory should be contained inside a subdirectory
together with any script to be executed after writing, for example:

    Raspbian/rbian-140107.img.gz
    Bakery/bakery.img.gz
    Bakery/bakery.post.1

`bakery.img.gz` is a minimal image configured to run Bakery and 
`bakery.post.1` is a script that copies some images into the correct location
for it to use.

`rbian-140107.img.gz` is Raspbian from 14/01/07 and does not require any post
install configuration, although a script could be created to expand the file
system, for example.

In the scripts the devices for the partitions are available as $PARTITION1,
$PARTITION2, etc. The image directory is available as $IMGDIR.

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

* Add an 'exit' button.
* It would be useful to mount and configure the image after installing.
* Any files in /home/pi/images will be listed but only .img.gz files will work.
  It may be helpful to structure this in such a way that there can be other
  files, such as README files.
* Devices are now detected when they are plugged in and removed. The main SD
  writer needs to be identfied, by vendor and model ids, so that another device
  does not accidentally get written to.
* No easy way to copy new images on when not connected to a network. Need to
  have a feature to use external USB storage, either writing images directly
  from one or copying them onto the Pi.
* The init script doesn't appear to be shutting bakery down properly. Two
  python processes are left running. I think bakery.py needs to catch and
  handle the interrupt.
* It can probably do without the selection of images. It is probably enough
  just to write the currently displayed image.
