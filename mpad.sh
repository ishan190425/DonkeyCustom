#!/bin/bash


# Step 3: Install Virtualenv
echo "Installing virtualenv..."
pip3 install virtualenv | pv -t

# Step 4: Create Virtual Environment
echo "Creating virtual environment..."
python3 -m virtualenv env | pv -t
echo "source ~/env/bin/activate" >> ~/.bashrc
source ~/.bashrc

# Step 5: Install Requirements
echo "Installing requirements..."
pip3 install -r requirements.txt | pv -t

# Step 6: Update and Upgrade
echo "Updating and upgrading packages..."
sudo apt-get update --allow-releaseinfo-change | pv -t
sudo apt-get -y upgrade | pv -t

# Step 7: Raspi-config
echo "Please follow the instructions in Step 7 to update the Raspberry Pi settings manually."

# Step 8: Install Dependencies
echo "Installing dependencies..."
sudo apt-get install -y build-essential python3 python3-dev python3-pip python3-virtualenv python3-numpy python3-picamera python3-pandas python3-rpi.gpio i2c-tools avahi-utils joystick libopenjp2-7-dev libtiff5-dev gfortran libatlas-base-dev libopenblas-dev libhdf5-serial-dev libgeos-dev git ntp | pv -t

# Step 9: (Optional) Install OpenCV Dependencies
echo "Installing OpenCV dependencies..."
sudo apt-get install -y libilmbase-dev libopenexr-dev libgstreamer1.0-dev libjasper-dev libwebp-dev libatlas-base-dev libavcodec-dev libavformat-dev libswscale-dev libqtgui4 libqt4-test | pv -t

# Step 10: Setup Virtual Env
echo "Setting up virtual environment..."
python3 -m virtualenv -p python3 env --system-site-packages | pv -t
echo "source ~/env/bin/activate" >> ~/.bashrc
source ~/.bashrc

# Step 11: Install Custom Donkeycar Python Code
echo "Installing DonkeyCar..."
mkdir projects
cd projects
git clone https://github.com/ishan190425/DonkeyCustom
cd DonkeyCustom
git checkout main
pip3 install -e .[pi] | pv -t
pip3 install -r mpad.txt | pv -t
pip3 install https://github.com/lhelontra/tensorflow-on-arm/releases/download/v2.2.0/tensorflow-2.2.0-cp37-none-linux_armv7l.whl | pv -t

# Step 12: (Optional) Install OpenCV
echo "Installing OpenCV..."
sudo apt install -y python3-opencv | pv -t

echo "Installation complete!"

donkey createcar --path ~/mycar
