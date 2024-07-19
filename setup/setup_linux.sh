#!/bin/bash

# Checking sudo permissions
if [ "$EUID" -ne 0 ]
  then echo "Please run this script with sudo."
  exit
fi

# Installing dependencies
sudo apt-get install -y git python3.10

# Creating the virtual environment
python3.10 -m venv venv_csv2kml-qc

# Enabling the virtual environment
if source venv_csv2kml-qc/bin/activate; then
    echo "Virtual environment enabled."
else
    echo "Error activating virtual environment."
fi

# Install required Python packages
if pip install simplekml pyproj shapely numpy pandas fiona argparse regex gpsdatetime gnsstoolbox; then
    echo "Python packages installed successfully."
else
    echo "Error installing Python packages."
    exit 1
fi
