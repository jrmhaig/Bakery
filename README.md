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

* python3-pyudev

Controls
--------

### PiFace Control and Display

* **Rocker:** Previous or next image
* **Rocker button:** Select image
* **Button 1:** Display connected devices
* **Button 5:** Exit

### PiFace Digital ###

* **S1:** Previous image
* **S2:** Next image
* **S3:** Write image to SD card
* **S4:** Write list of image to USB drive

Device listener
---------------

The module lib/udevevents.py listens for devices added via the USB ports.
These are added or removed to a list that can be displayed with button 1.

To do
-----

A (possibly incomplete) list of things that need doing:

1. Mount device.
2. S3 to write image. Progress status with LEDs.
3. Create instruction file that can be written to an output file, including the
   list of images.
4. Maybe it should take more than just a single button press to start writing
   the image.
5. Allow for selecting device and image to write via CAD.
