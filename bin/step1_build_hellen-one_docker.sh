#!/bin/bash

if [ ! -e hellen-one/git_scripts ]; then
    echo "No submodules?"
    git submodule update --init --recursive
fi

cd hellen-one

docker build -t hellen-one .
