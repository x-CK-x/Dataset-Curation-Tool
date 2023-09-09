#!/bin/bash

PATHFILE="dataset_curation_path.txt"
UPDATE_ENV=false

# Check if conda command is available
command -v conda >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Miniconda is already installed."
    # Add Miniconda to PATH
    export PATH="$HOME/miniconda/bin:$PATH"
    source ~/.bashrc
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

            UPDATE_ENV=true
        else
            echo "Repository already exists. Please move to a different directory to clone again."
            cd Dataset-Curation-Tool
        fi
    fi
    # Store the current path for future use
    echo "$PWD" > "$PATHFILE"
fi

# Delete the specified files
rm -f linux_run.sh mac_run.sh run.bat

# Fetch the latest changes and tags
git fetch

# Fetch the latest tag from the remote
LATEST_TAG=$(git for-each-ref refs/tags --sort=-creatordate --format '%(refname:short)' --count=1)

# Get the current tag of the local repository
CURRENT_TAG=$(git describe --tags --exact-match 2> /dev/null)

if [ "$CURRENT_TAG" != "$LATEST_TAG" ]; then
    echo "Currently on $CURRENT_TAG."
    
    git reset HEAD linux_run.sh mac_run.sh run.bat
	  git checkout -- linux_run.sh mac_run.sh run.bat

    # Stash any user changes
    git stash

    find . -name "__pycache__" -type d -exec rm -r {} +
    find . -name "*.pyc" -exec rm -f {} +

    git checkout tags/$LATEST_TAG

    # Apply stashed user changes
    git stash apply

    UPDATE_ENV=true
else
    echo "Already on tag $LATEST_TAG."
fi

# Check if the conda environment already exists
conda info --envs | grep data-curation > /dev/null
if [ $? -ne 0 ]; then
    conda env create -f environment.yml
else
    if $UPDATE_ENV; then
        echo "Conda environment 'data-curation' already exists. Checking for updates..."
        conda env update -n data-curation -f environment.yml
    fi
fi

# Activate the conda environment
source activate data-curation

# Run the python program with the passed arguments
python webui.py "$@"

trap 'echo "Error encountered. Press any key to exit."; read -rsn1' ERR
