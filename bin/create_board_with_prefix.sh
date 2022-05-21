#!/bin/bash

############################################################################################
# Hellen-One: A board creation script with custom (non-hellen) board prefix.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

board_prefix="$1"
project_base="$2"
frame_name="$3"
frame_rev="$4"
bom_replace="$5"
comp_img_offset="$6"

python_bin="python3.8"

############################################################################################

echo "Hellen-One: Starting a board creation..."
echo "Checking dependencies..."

# check args
if [ -z "$1" ]; then
	echo "This script cannot be executed directly! Please run user scripts from the base directory!"
	exit 1
fi


# check python version (should be 2.x ONLY), etc...
if ! ./bin/check_all.sh; then
	exit 2
fi

# start virtual framebuffer (should be already installed)
export DISPLAY=:99.0
Xvfb :99 -screen 0 640x480x24 &

echo "Processing ${board_prefix} board..."
if ! $python_bin bin/process_board.py ${board_prefix} ${project_base} ${frame_name} ${frame_rev} ${bom_replace} ${comp_img_offset}; then
	echo "ABORTING!"
	exit 3
else
	echo "All done!"
	exit 0
fi

