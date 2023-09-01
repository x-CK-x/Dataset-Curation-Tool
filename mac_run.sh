#!/bin/bash

PATHFILE="dataset_curation_path.txt"

# Check if conda command is available
command -v conda >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Miniconda is already installed."
else
    echo "Miniconda is not installed. Installing now..."
    # Downloading Miniconda3 for macOS
    curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
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
    if [ "$(basename "$PWD")" != "Dataset-Curation-Tool" ]; then
        # Check and clone the GitHub repository if not already cloned
        if [ ! -d "Dataset-Curation-Tool" ]; then
            git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
        else
            echo "Repository already exists. Skipping clone."
        fi
        cd Dataset-Curation-Tool
    else
        echo "Already in 'Dataset-Curation-Tool' directory."
    fi
    # Store the current path for future use
    echo "$PWD" > "$PATHFILE"
fi

# Fetch latest changes and tags from remote
git fetch

# Stash any user changes
git stash

# Check the current tag
CURRENT_TAG=$(git describe --tags --exact-match 2> /dev/null)
if [ "$CURRENT_TAG" != "v4.2.5" ]; then
    git checkout tags/v4.2.5
else
    echo "Already on tag v4.2.5."
fi

# Apply stashed user changes
git stash apply

# Check if the conda environment already exists
conda info --envs | grep data-curation > /dev/null
if [ $? -ne 0 ]; then
    conda env create -f environment.yml
else
    echo "Conda environment 'data-curation' already exists. Skipping environment creation."
fi

# Activate the conda environment
conda activate data-curation

# Run the python program with the passed arguments
python webui.py "$@"
