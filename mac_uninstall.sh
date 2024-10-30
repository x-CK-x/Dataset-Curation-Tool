#!/bin/bash

# Name of the conda environment
ENV_NAME="data-curation"
PATHFILE="dataset_curation_path.txt"

echo "Starting uninstallation of the '$ENV_NAME' environment."

# Check if conda is installed
if ! command -v conda &> /dev/null
then
    echo "Conda is not installed. Nothing to uninstall."
    exit 0
fi

# Deactivate any active conda environment
conda deactivate

# Check if the environment exists
if conda env list | grep -q "$ENV_NAME"
then
    echo "Removing conda environment '$ENV_NAME'..."
    conda env remove -n "$ENV_NAME"
else
    echo "Conda environment '$ENV_NAME' does not exist."
fi

# Remove the Dataset-Curation-Tool directory if it exists
if [ -f "$PATHFILE" ]; then
    STORED_PATH=$(<"$PATHFILE")
    if [ -d "$STORED_PATH" ]; then
        echo "Removing 'Dataset-Curation-Tool' directory at '$STORED_PATH'..."
        rm -rf "$STORED_PATH"
    else
        echo "Directory '$STORED_PATH' does not exist."
    fi
    # Remove the path file
    rm -f "$PATHFILE"
fi

echo "Uninstallation complete."
