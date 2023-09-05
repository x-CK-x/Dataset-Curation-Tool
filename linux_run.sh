#!/bin/bash

PATHFILE="dataset_curation_path.txt"

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

# Check if we have a stored path
if [ -f "$PATHFILE" ]; then
    STORED_PATH=$(<"$PATHFILE")
    cd "$STORED_PATH"
else
    # Check if the current directory is "Dataset-Curation-Tool"
    if [ "$(basename "$PWD")" == "Dataset-Curation-Tool" ]; then
        echo "Already in 'Dataset-Curation-Tool' directory."
    else
        # Check and clone the GitHub repository if not already cloned
        if [ ! -d "Dataset-Curation-Tool" ]; then
            git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
            cd Dataset-Curation-Tool
        else
            echo "Repository already exists. Please move to a different directory to clone again."
            sleep 10  # Pauses the script for 10 seconds
            exit 1
        fi
    fi
    # Store the current path for future use
    echo "$PWD" > "$PATHFILE"
fi

# Delete the specified files
rm -f linux_run.sh mac_run.sh run.bat

# Fetch the latest changes and tags
git fetch

# Stash any user changes
git stash

# Check the current tag
CURRENT_TAG=$(git describe --tags --exact-match 2> /dev/null)
if [ "$CURRENT_TAG" != "v4.2.8" ]; then
    git checkout tags/v4.2.8
else
    echo "Already on tag v4.2.8."
fi

# Apply stashed user changes
git stash apply

# Check if the conda environment already exists
conda info --envs | grep data-curation > /dev/null
if [ $? -ne 0 ]; then
    conda env create -f environment.yml
else
    echo "Conda environment 'data-curation' already exists. Checking for updates..."
    conda env update -n data-curation -f environment.yml
fi

# Activate the conda environment
source activate data-curation

# Run the python program with the passed arguments
python webui.py "$@"
