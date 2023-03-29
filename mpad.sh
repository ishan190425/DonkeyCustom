#!/bin/bash

# Step 6: Update and Upgrade
sudo apt-get update -y --allow-releaseinfo-change
sudo apt-get upgrade -y

# Step 7: Raspi-config
echo "Please follow the instructions in Step 7 to update the Raspberry Pi settings manually."

# Step 8: Install Dependencies
sudo apt-get install -y build-essential python3 python3-dev python3-pip python3-virtualenv python3-numpy python3-picamera python3-pandas python3-rpi.gpio i2c-tools avahi-utils joystick libopenjp2-7-dev libtiff5-dev gfortran libatlas-base-dev libopenblas-dev libhdf5-serial-dev libgeos-dev git ntp

# Step 9: (Optional) Install OpenCV Dependencies
sudo apt-get install -y libilmbase-dev libopenexr-dev libgstreamer1.0-dev libjasper-dev libwebp-dev libatlas-base-dev libavcodec-dev libavformat-dev libswscale-dev libqtgui4 libqt4-test

# Step 10: Setup Virtual Env
python3 -m virtualenv -p python3 env --system-site-packages
echo "source ~/env/bin/activate" >> ~/.bashrc
source ~/.bashrc

# Step 11: Install Custom Donkeycar Python Code
mkdir projects
cd projects
git clone https://github.com/ishan190425/DonkeyCustom
cd DonkeyCustom
git checkout main
pip install -y -e .[pi]
pip install -y -r mpad.txt
pip install -y https://github.com/lhelontra/tensorflow-on-arm/releases/download/v2.2.0/tensorflow-2.2.0-cp37-none-linux_armv7l.whl

# Step 12: (Optional) Install OpenCV
sudo apt install -y python3-opencv
