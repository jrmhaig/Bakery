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

The pifacecommon library from python3-pifacecad must be version 4.1.1 or
later. At time of writing, the version that is in the Raspbian respositories
is 4.0 so the 'testing' branch from Github should be used. Alternatively, the
`interrupts.py` file may be replaced, as described below.

### Set up

A Debian Squeeze based distribution must be used as the PiFace libraries are
not currently available for others. Raspbian may be used but Moebius is
recommended to maximise the available disk space for images. Moebius may be
downloaded from here:

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

It is recommended that you do _not_ expand the root filesystem but instead
create a separate partition for the storage of images.

Reboot to enable the SPI module and PiFace CAD.

Extract Bakery into:

    /home/pi/Bakery

*Important:* Until a version of the PiFace libraries newer than 4.0.0 becomes
available you must patch the PiFace `interrupts.py` file:

    cp /home/pi/Bakery/pifacecommon/interrupts.py /usr/lib/python3/dist-packages/pifacecommon/interrupts.py

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
    Bakery/bakery.vars
    Bakery/bakery.post.1

* `bakery.img.gz` is a minimal image configured to run Bakery
* `bakery.vars` is a list of options to collect, which are then passed as
environment variables to the post install scripts
* `bakery.post.1` is a script that copies some images into the correct location
for it to use

The `opts` file comprises line in the format:

    VARIABLE=<default value>

and these will be passed to all post install scripts.

## Operation

Run with:

    sudo python3 bakery.py

Images are found in /home/pi/images and should be gzipped.

### Controls

<table>
  <tr>
    <th>Button</th>
    <th>Main view</th>
    <th>Load image view</th>
    <th>Delete image view</th>
    <th>System status view</th>
  </tr>
  <tr>
    <th>1</th>
    <td>Swith between lines</td>
    <td colspan=3><i>No action</i></td>
  </tr>
  <tr>
    <th>2</th>
    <td colspan=4>Next view</td>
  </tr>
  <tr>
    <th>3</th>
    <td colspan=4><i>No action</i></td>
  </tr>
  <tr>
    <th>4</th>
    <td colspan=4>Scroll display</td>
  </tr>
  <tr>
    <th>5</th>
    <td>Write image (hold for 5 seconds)</td>
    <td>Scan selected device</td>
    <td>Delete image (hold for 5 seconds)</td>
    <td>Execute displayed action (hold for 5 seconds)</td>
  </tr>
  <tr>
    <th>Rocker press</th>
    <td>Display further information<td>
    <td colspan=3><i>No action</i></td>
  </tr>
  <tr>
    <th>Rocker</th>
    <td>Select image or device<td>
    <td>Select device to scan<td>
    <td>Select image to delete<td>
    <td>Show next data or option<td>
  </tr>
</table>

#### Main view

* *Button 1:* Switch active line on display
* *Button 2:* Change to system load image view (below)
* *Button 4:* Scroll display
* *Button 5:* Hold for 5 seconds to write currently displayed image
* *Rocker left/right:* Move between options
* *Rocker button:* Display information about selected image or device

#### Load image view

* *Button 2:* Change to delete image view (below)
* *Button 4:* Scroll display
* *Button 5:* Scan selected device
* *Rocker left/right:* Move between devices

##### After scanning

* *Button 2:* Copy found image
* *Button 3:* Do not copy found image


#### Delete image view

* *Button 2:* Change to information view (below)
* *Button 4:* Scroll display
* *Button 5:* Hold for 5 seconds to delete currently displayed image
* *Rocker left/right:* Move between images

#### System information view

* *Button 2:* Change to main view (above)
* *Button 3:* Scroll display
* *Button 4:* Hold for 5 seconds to execute command (for shutdown and reboot options)
* *Rocker left/right:* Move between options

## System information

The system information view will display:

* IP address
* CPU temperature

There are options to reboot or shutdown.

## Images

Images should be stored in subdirectories of the source directory defined in
the configuration file (see above) and they should be zipped up using:

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

The scripts are passed environment variable defined in the `image.var` plus:

| Variable | Description |
|----------|-------------|
| $DEVICE     | Device path. Eg, /dev/sda |
| $PARTITION1 | Device path of the first partition. Eg, /dev/sda1 |
| $PARTITION2 | Device path of the second partition. Eg, /dev/sda2 |
| (etc) | |
| $IMGDIR | The directory containing the image and other related files |

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
