Bakery
======

Use a Pi to make a Pi

Objective
---------

Use the Raspberry Pi to write images to other SD cards. The primary objective
is to be able create new Raspberry Pi OS cards but it can obviously be used for
copying any images.

WARNING 1
---------

This software is designed to wipe and write to any SD card that you connect via
the USB connectors on a Raspberry Pi. There is obviously a real danger of data
loss if used without care.

WARNING 2
---------

Did you read WARNING 1? If not, go back and read it again.

Hardware Requirements
---------------------

* USB to SD adapter
* PiFace Digital *or* Control and Display
* USB drive (optional)

The PiFace Digital is used for interaction and feedback so the Bakery can be
used without the need for a screen. Interaction using other add-on hardware can
be used in its place, subject to the necessary code changes.

The USB drive will be used to store the image files. This is not required if
the main SD card is sufficiently large.

Software requirements
---------------------

* hal

or

* python-pyudev
* python3-pyudev

Controls
--------

* **S1:** Previous image
* **S2:** Next image
* **S3:** Write image to SD card
* **S4:** Write list of image to USB drive

Device listener
---------------

The module lib/devicelisterner.py will detect when a new SD card has been
entered. At the moment it is detecting partitions but ideally it should get the
the disk. So, if it finds:

* /dev/sda1
* /dev/sda2

what it really needs to find is:

* /dev/sda

Question: Can the disk name be reliably found from the partition names? Or can
it be detected directly?

To do
-----

A (possibly incomplete) list of things that need doing:

1. Detect when a device has been plugged in.
2. Mount device.
3. S1 and S2 to select image. Display selected image with LEDs.
4. S3 to write image. Progress status with LEDs.
5. Create instruction file that can be written to an output file, including the
   list of images.
6. Maybe it should take more than just a single button press to start writing
   the image.
7. Get a PiFace Display. This would be much more useful than the PiFace Digital.
