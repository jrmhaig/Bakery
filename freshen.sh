#!/bin/bash

# Use fdisk to write the partition table without changing. This refreshes the
# partitions in /dev.
# Is there a better way to do this?

fdisk $1 <<EOF
w
EOF
