#!/bin/bash

# This script serves as a CLI wrapper for umdgenc.exe.
# It handles the generation of the .umi and .ufl files, and then 
# calls umdgenc.exe to produce the final ISO images.

# Current Directory
ROOT_DIR=$(pwd)
INPUT_DIR="Rebuilt game"
OUTPUT_DIR="output"

# Paths to files
UMI_PATH="blueprint.umi"
UFL_PATH="blueprint.ufl"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory $INPUT_DIR does not exist."
    exit 1
fi

echo "Step 1: Generating blueprint.umi and blueprint.ufl..."
python3 "generate_umi.py"

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate blueprints."
    exit 1
fi

echo "Step 2: Running umdgenc.exe to generate ISO images..."
# We use the absolute path to umdgenc.exe to ensure it's found correctly.
./umdgenc.exe /g "$UMI_PATH" "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
	:
else
    echo "Error: umdgenc.exe failed to generate images."
    exit 1
fi

echo "pulling out patch"
cp "$OUTPUT_DIR/USER_L0.IMG" patched.iso
