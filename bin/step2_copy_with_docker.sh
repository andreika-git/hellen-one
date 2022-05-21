#!/bin/bash

if [ ! -f hellen-one/git_scripts ]; then
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
echo "BOARD_REVISION=[${BOARD_REVISION}]"

docker run --rm -t --user $(id -u):$(id -g) --entrypoint python3 -v "$(pwd)":/${PWD##*/} hellen-one ./bin/copy_from_Kicad.py "frames:${BOARD_PREFIX}" "/${PWD##*/}" "../../gerber" "${BOARD_SUFFIX}" "${BOARD_REVISION}"

echo "Done!"
