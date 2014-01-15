#!/bin/bash
#
# Test to see if there is an SD card

DEV=$1

# bakery.py is run as root so this doesn't really need to be
FDSK=`sudo fdisk -l $1`

if [ "x$FDSK" == "x" ]
then
  exit 0
else
  exit 1
fi
