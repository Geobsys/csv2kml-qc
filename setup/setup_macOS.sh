#!/bin/bash

# Checking sudo permissions
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo."
  exit
fi

# Installing Homebrew if not installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Installing dependencies using Homebrew
brew install git python@3.10


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
