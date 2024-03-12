#!/bin/bash

if [ ! -e hellen-one/git_scripts ]; then
    echo "No submodules?"
    git submodule update --init --recursive
fi

# See step2_copy_with_docker.sh for explanation of the following command

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

docker run --rm -t --user $(id -u):$(id -g) --entrypoint bash -v "$(pwd)":/${PWD##*/} hellen-one ./bin/create_board_with_prefix.sh "${BOARD_PREFIX}" "/${PWD##*/}" "${BOARD_SUFFIX}" "${BOARD_REVISION}" "bom_replace_${BOARD_PREFIX}${BOARD_SUFFIX}-${BOARD_REVISION}.csv " "${BOARD_PCB_OFFSET}" "${BOARD_LAYERS}"

