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

The pifacecad module must be version 4.1 or later. If 4.1 has not been released
yet then the testing branch from Github must be used.

### Set up

A minimal Linux distribution can be found here:

* http://moebiuslinux.sourceforge.net/

Upgrade:

    apt-get update
    apt-get upgrade
    apt-get clean all

The last line cleans up the apt cache because there is not a lot of free space
in the root partition.

Install the required packages:

    apt-get install python3-pifacecad python3-pyudev
    apt-get clean all

Enable SPI by removing this line from /etc/modprobe.d/raspi-blacklist.conf:

    blacklist spi-bcm2708

Reboot to enable the SPI module and PiFace CAD.

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
    Bakery/bakery.opts
    Bakery/bakery.post.1

* `bakery.img.gz` is a minimal image configured to run Bakery
* `bakery.opts` is a list of options to collect, which are then passed as
environment variables to the post install scripts
* `bakery.post.1` is a script that copies some images into the correct location
for it to use

The `opts` file is in the format:

    VARIABLE=<default value>

`rbian-140107.img.gz` is Raspbian from 14/01/07 and does not require any post
install configuration, although a script could be created to expand the file
system, for example.

In the scripts the devices for the partitions are available as $PARTITION1,
$PARTITION2, etc. The image directory is available as $IMGDIR.

## Operation

Run with:

    sudo python3 bakery.py

Images are found in /home/pi/images and should be gzipped.

### Controls

* *Button 1:* Switch active line on display
* *Button 3:* Scroll display
* *Button 4:* Hold for 5 seconds to write currently displayed image
* *Rocker left/right:* Move between options

## Images

Images (and only images) should be stored in the directory

    /home/pi/images

zipped up with:

    gzip image.img

so that the file has a `.img.gz` extension.

Note that images provided by distributions may be packaged up in various forms,
such as tar, tar.gz and zip. None of these will work so you will need to unpack
them and gzip the image.

## Configuration scripts

The configuration scripts for an image must be in the same directory as the
image and named consistently. For `image.img` the scripts must be called:

    image.post.1
    image.post.2
    image.post.3
    (etc)

The number indicates the order in which they are executed.

The scripts have the following environment variables set:

    $IMGDIR = Directory containing the image and scripts
    $PARTITION1 = Device of the first partition on the image
    $PARTITION2 = Device of the second partition on the image
    (etc)

The title of the script is the first comment in the format:

    #TITLE# Config script

The text 'Config script' will be displayed during its execution.

### Example script ###

    #!/bin/bash
    #TITLE# Set the hostname
    # The root partition is the second partition on the disk
    
    mount $PARTITION2 /mnt
    echo new-hostname > /mnt/etc/hostname
    umount $PARTITION2

## To do list

* Add an 'exit' button.
* Devices are now detected when they are plugged in and removed. The main SD
  writer needs to be identfied, by vendor and model ids, so that another device
  does not accidentally get written to.
* No easy way to copy new images on when not connected to a network. Need to
  have a feature to use external USB storage, either writing images directly
  from one or copying them onto the Pi.

## Longer term plans

The SD card writer (and duplicator) is just the first step towards a 'control
centre' device that can be used for managing a network of Raspberry Pis in a
classroom environment. Future features could include:

* Install a very small 'seed' image that then completes installation over
  the network. For a large number of installs this may be quicker.
* Store known configurations for a quick refresh for a particular user
* DHCP server
* Network router/gateway
* FTP, NFS, Samba
* Git - Gitlab and proxy to Github
* Update services - eg, apt and yum server
* Copy files to and from Pis on the network. In particular, copy files onto all Pis.
