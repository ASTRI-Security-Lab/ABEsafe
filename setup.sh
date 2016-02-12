#!/bin/bash

#sudo apt-get update
sudo apt-get install -y git python python2.7-dev python-pip
sudo apt-get install -y dpkg-dev build-essential libwebkitgtk-dev libgtk2.0-dev
sudo apt-get install -y libjpeg-dev libtiff-dev libsdl1.2-dev libgstreamer-plugins-base0.10-dev libnotify-dev
sudo apt-get install -y freeglut3 freeglut3-dev
sudo pip install --upgrade pip
sudo pip install --upgrade setuptools
sudo pip install --upgrade --trusted-host wxpython.org --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix

git clone https://github.com/ASTRI-Security-Lab/ABEsafe
