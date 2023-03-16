#!/bin/bash

if [ ! -e hellen-one/git_scripts ]; then
    echo "No submodules?"
    git submodule update --init --recursive
fi

# See step2_copy_with_docker.sh for explanation of the following command

source revision.txt
echo "BOARD_REVISION=[${BOARD_REVISION}]"

docker run --rm -t --user $(id -u):$(id -g) --entrypoint bash -v "$(pwd)":/${PWD##*/} hellen-one ./bin/create_board_with_prefix.sh "${BOARD_PREFIX}" "/${PWD##*/}" "${BOARD_SUFFIX}" "${BOARD_REVISION}" "bom_replace_${BOARD_PREFIX}${BOARD_SUFFIX}-${BOARD_REVISION}.csv " "${BOARD_PCB_OFFSET}"

