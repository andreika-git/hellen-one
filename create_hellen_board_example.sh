#!/bin/bash
#
# This is a simple example of using Hellen-One scripts for your own board "Hellen999pin", revision "a".
# You have to put your folder somewhere outside of the Hellen-One repository.
# The folder should have a sub-folder for revision "a" and a sub-folder with all the files for your frame (gerber+BOM+CPL+schematic)
# as follows: ../my-boards/hellen999pin/boards/hellen999pin-a/frame/*
# For more info, please see: https://github.com/andreika-git/hellen-one/wiki
# For board examples and script usage, please see: https://github.com/andreika-git/hellen-boards/
#
# The script will create the output files for your board in:
# ../my-boards/hellen999pin/boards/hellen999pin-a/board/*
#
# (R309 and R311 are not populated).
#

project_base="../my-boards"
name="999pin"
rev="a"

if [[ ! -d ${project_base}/hellen${name}/boards/hellen${name}-${rev}/frame ]]; then
	echo "The folder not found!"
	exit 1
fi

sh ./bin/create_board.sh "${project_base}" "${name}" "${rev}" "R309=;R311="
