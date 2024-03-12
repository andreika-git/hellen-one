#!/bin/bash

if [ ! -e hellen-one/git_scripts ]; then
    echo "No submodules?"
    git submodule update --init --recursive
fi


# This command is me trying to be fancy
# '--entrypoint python3' skips the normal container CMD and starts python3 instead
#    using the parameters specified after 'hellen-one'
#
# -v "$(pwd)":/${PWD##*/} simply mounts the current working directory
#    at /<the name of the current directory>
#
# '/${PWD##*/}' is doing the $pwd basename thing again

source revision.txt

if [ -z "${BOARD_PREFIX}" ]; then
    echo "Error! BOARD_PREFIX is not set!"
    exit 1
fi

if [ -z "${BOARD_SUFFIX}" ]; then
    echo "Error! BOARD_SUFFIX is not set!"
    exit 2
fi

echo "BOARD_REVISION=[${BOARD_REVISION}]"
echo "BOARD_LAYERS=[${BOARD_LAYERS}]"

docker run --rm -t --user $(id -u):$(id -g) --entrypoint python3 -v "$(pwd)":/${PWD##*/} hellen-one ./bin/copy_from_Kicad.py "frames:${BOARD_PREFIX}" "/${PWD##*/}" "../../gerber" "${BOARD_SUFFIX}" "${BOARD_REVISION}" "${BOARD_LAYERS}"
