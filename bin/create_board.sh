#!/bin/bash

############################################################################################
# Hellen-One: A board creation script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

project_base="$1"
frame_name="$2"
frame_rev="$3"
bom_replace="$4"

python_bin="python2.7"

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

echo "Processing board..."
$python_bin bin/process_board.py ${project_base} ${frame_name} ${frame_rev} ${bom_replace}

echo "All done!"
exit 0
