#!/bin/bash

# Check if conda command is available
command -v conda >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Miniconda is already installed."
else
    echo "Miniconda is not installed. Installing now..."
    # Assuming you want to install Miniconda3 for 64-bit Linux. Change the URL if needed.
    curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash miniconda.sh -b -p $HOME/miniconda
    rm miniconda.sh
    # Add Miniconda to PATH
    export PATH="$HOME/miniconda/bin:$PATH"
    # Initialize conda for shell interaction
    conda init bash
    source ~/.bashrc
fi

# Clone the GitHub repository if not already cloned
if [ ! -d "Dataset-Curation-Tool" ]; then
    git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
fi

# Change directory and create conda environment
cd Dataset-Curation-Tool
conda env create -f environment.yml

# Activate the conda environment
source activate data-curation

# Run the python program with the passed arguments
python webui.py "$@"