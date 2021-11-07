#!/bin/bash

sudo apt-get update
sudo apt -y upgrade

sudo apt-get install pkg-config
sudo apt-get install libcairo2-dev


# node 12 specifically
sudo apt update
sudo apt -y install curl dirmngr apt-transport-https lsb-release ca-certificates
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -

# sudo apt-get install npm
# sudo npm install npm@latest -g