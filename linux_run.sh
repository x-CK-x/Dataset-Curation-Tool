#!/usr/bin/env bash

set -e
set -o pipefail

# Create/reset debug.log
echo "Script started at $(date)" > debug.log
echo "----------------------------------------" >> debug.log

PATHFILE="dataset_curation_path.txt"
UPDATE_ENV=false

echo "Use --update on the command line with the run file to update the program!"
echo "Use --update on the command line with the run file to update the program!" >> debug.log

OTHER_ARGS=()

# Parse arguments
for arg in "$@"; do
    if [ "$arg" = "--update" ]; then
        UPDATE_ENV=true
    else
        OTHER_ARGS+=("$arg")
    fi
done

echo "Checking if git is available..."
echo "Checking if git is available..." >> debug.log
if ! command -v git >/dev/null 2>&1; then
    echo "Git not found. Installing Git..."
    echo "Git not found. Installing Git..." >> debug.log

    # If apt is available:
    if command -v apt >/dev/null 2>&1; then
        sudo apt update >> debug.log 2>&1 && sudo apt install -y git >> debug.log 2>&1
        if [ $? -ne 0 ]; then
            echo "Git installation failed"
            echo "Git installation failed" >> debug.log
            echo "Press any key to exit."
            read -rsn1
            exit 1
        fi
    else
        echo "No suitable package manager found to install git automatically."
        echo "No suitable package manager found to install git automatically." >> debug.log
        echo "Please install git manually."
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi

    echo "Git installed successfully"
    echo "Git installed successfully" >> debug.log
else
    echo "Git is already installed"
    echo "Git is already installed" >> debug.log
fi

echo "Checking conda availability..."
echo "Checking conda availability..." >> debug.log
if ! command -v conda >/dev/null 2>&1; then
    echo "Miniconda not found. Installing Miniconda..."
    echo "Miniconda not found. Installing Miniconda..." >> debug.log
    curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to download Miniconda. Check internet connection."
        echo "Failed to download Miniconda. Check internet connection." >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi
    bash miniconda.sh -b -p "$HOME/miniconda" >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Miniconda installation failed"
        echo "Miniconda installation failed" >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi
    rm miniconda.sh
    export PATH="$HOME/miniconda/bin:$PATH"
    conda init bash >> debug.log 2>&1 || true
    source ~/.bashrc

    echo "Miniconda installed successfully"
    echo "Miniconda installed successfully" >> debug.log
else
    echo "Miniconda is already installed"
    echo "Miniconda is already installed" >> debug.log
    export PATH="$HOME/miniconda/bin:$PATH"
    source ~/.bashrc
fi

echo "Checking repository path..."
echo "Checking repository path..." >> debug.log

if [ -f "$PATHFILE" ]; then
    echo "Found stored path in $PATHFILE"
    echo "Found stored path in $PATHFILE" >> debug.log

    # Read and trim leading/trailing whitespace
    STORED_PATH=$(sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//' "$PATHFILE")

    if [ -z "$STORED_PATH" ]; then
        echo "Stored path is empty. Please delete $PATHFILE and run again."
        echo "Stored path is empty. Please delete $PATHFILE and run again." >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi

    cd "$STORED_PATH" >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to change directory to stored path: $STORED_PATH"
        echo "Failed to change directory to stored path: $STORED_PATH" >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi
    echo "Changed directory to stored path: $PWD"
    echo "Changed directory to stored path: $PWD" >> debug.log
else
    echo "No $PATHFILE found, using current directory as parent"
    echo "No $PATHFILE found, using current directory as parent" >> debug.log

    # Already in correct directory
    PARENT_PATH="$PWD"
    echo "Using current directory as parent: $PWD"
    echo "Using current directory as parent: $PWD" >> debug.log
fi

if [ ! -f "Dataset-Curation-Tool/environment.yml" ]; then
    echo "Dataset-Curation-Tool not found in $PWD. Attempting to clone..."
    echo "Dataset-Curation-Tool not found in $PWD. Attempting to clone..." >> debug.log
    git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git Dataset-Curation-Tool >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Git clone failed"
        echo "Git clone failed" >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi
    UPDATE_ENV=true
else
    echo "Dataset-Curation-Tool already present"
    echo "Dataset-Curation-Tool already present" >> debug.log
fi

cd Dataset-Curation-Tool >> debug.log 2>&1
if [ $? -ne 0 ]; then
    echo "Cloned (if needed) but failed to enter Dataset-Curation-Tool directory"
    echo "Cloned (if needed) but failed to enter Dataset-Curation-Tool directory" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
fi

if [ ! -f "environment.yml" ]; then
    echo "environment.yml not found inside Dataset-Curation-Tool"
    echo "environment.yml not found inside Dataset-Curation-Tool" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
fi

echo "Verified we are inside Dataset-Curation-Tool directory: $PWD"
echo "Verified we are inside Dataset-Curation-Tool directory: $PWD" >> debug.log

cd ..
if [ $? -ne 0 ]; then
    echo "Failed to go one directory up to store parent path"
    echo "Failed to go one directory up to store parent path" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
fi

echo "$PWD" > "$PATHFILE"
echo "Stored current path $PWD into $PATHFILE."
echo "Stored current path $PWD into $PATHFILE." >> debug.log

cd Dataset-Curation-Tool
if [ $? -ne 0 ]; then
    echo "Failed to re-enter Dataset-Curation-Tool directory"
    echo "Failed to re-enter Dataset-Curation-Tool directory" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
fi

echo "Deleting old run scripts..."
echo "Deleting old run scripts..." >> debug.log
rm -f linux_run.sh mac_run.sh run.bat

echo "Fetching latest changes and tags..."
echo "Fetching latest changes and tags..." >> debug.log
git fetch >> debug.log 2>&1
if [ $? -ne 0 ]; then
    echo "Failed to fetch from git repository"
    echo "Failed to fetch from git repository" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
fi

echo "Determining latest tag..."
echo "Determining latest tag..." >> debug.log
LATEST_TAG=$(git for-each-ref refs/tags --sort=-creatordate --format '%(refname:short)' --count=1)
CURRENT_TAG=$(git describe --tags --exact-match 2> /dev/null || true)

if [ -z "$CURRENT_TAG" ]; then
    echo "No current tag found - possibly a detached HEAD"
    echo "No current tag found - possibly a detached HEAD" >> debug.log
else
    echo "Currently on tag: $CURRENT_TAG. Latest tag: $LATEST_TAG."
    echo "Currently on tag: $CURRENT_TAG. Latest tag: $LATEST_TAG." >> debug.log
fi

if [ "$CURRENT_TAG" != "$LATEST_TAG" ]; then
    echo "Not on the latest tag. Checking out to $LATEST_TAG."
    echo "Not on the latest tag. Checking out to $LATEST_TAG." >> debug.log

    git reset HEAD linux_run.sh mac_run.sh run.bat >> debug.log 2>&1 || true
    git checkout -- linux_run.sh mac_run.sh run.bat >> debug.log 2>&1 || true

    echo "Stashing any user changes..."
    echo "Stashing any user changes..." >> debug.log
    git stash >> debug.log 2>&1 || true

    echo "Removing __pycache__ and pyc files"
    echo "Removing __pycache__ and pyc files" >> debug.log
    find . -name "__pycache__" -type d -exec rm -r {} + >> debug.log 2>&1
    find . -name "*.pyc" -exec rm -f {} + >> debug.log 2>&1

    echo "Checking out to $LATEST_TAG..."
    echo "Checking out to $LATEST_TAG..." >> debug.log
    git checkout "tags/$LATEST_TAG" >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to checkout to $LATEST_TAG."
        echo "Failed to checkout to $LATEST_TAG." >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi

    echo "Applying stashed user changes..."
    echo "Applying stashed user changes..." >> debug.log
    git stash apply >> debug.log 2>&1 || true

    UPDATE_ENV=true
else
    echo "Already on the latest tag $LATEST_TAG"
    echo "Already on the latest tag $LATEST_TAG" >> debug.log
fi

echo "Checking if the conda environment data-curation exists..."
echo "Checking if the conda environment data-curation exists..." >> debug.log
conda info --envs | grep data-curation > /dev/null
if [ $? -ne 0 ]; then
    echo "Environment data-curation not found. Creating environment..."
    echo "Environment data-curation not found. Creating environment..." >> debug.log
    conda env create -f environment.yml >> debug.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to create conda environment"
        echo "Failed to create conda environment" >> debug.log
        echo "Press any key to exit."
        read -rsn1
        exit 1
    fi
else
    if $UPDATE_ENV; then
        echo "Environment data-curation exists. Updating environment"
        echo "Environment data-curation exists. Updating environment" >> debug.log
        conda env update -n data-curation -f environment.yml >> debug.log 2>&1 || true
    else
        echo "Environment data-curation already exists and up to date"
        echo "Environment data-curation already exists and up to date" >> debug.log
    fi
fi

echo "Activating data-curation environment..."
echo "Activating data-curation environment..." >> debug.log
source activate data-curation || {
    echo "Failed to activate environment"
    echo "Failed to activate environment" >> debug.log
    echo "Press any key to exit."
    read -rsn1
    exit 1
}

echo "Running the python program..."
echo "Running the python program..." >> debug.log
python webui.py "${OTHER_ARGS[@]}" >> debug.log 2>&1 || {
    echo "Python program encountered an error"
    echo "Python program encountered an error" >> debug.log
    echo "Check debug.log for details. Press any key to exit."
    read -rsn1
    exit 1
}

echo "Starting UI at http://localhost:7860"
echo "Starting UI at http://localhost:7860" >> debug.log
OS=$(uname)
if [ "$OS" = "Linux" ]; then
    xdg-open http://localhost:7860 || true
elif [ "$OS" = "Darwin" ]; then
    open http://localhost:7860 || true
else
    echo "Unsupported OS: $OS"
    echo "Unsupported OS: $OS" >> debug.log
fi
