#!/bin/bash

# Banshee Tileset Selector Script
# Allows selecting a PNG tileset file and runs the tile selector

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Please create it first."
    exit 1
fi

# Find all PNG files in current directory
png_files=()
while IFS= read -r -d '' file; do
    png_files+=("$file")
done < <(find . -maxdepth 1 -type f -iname "*.png" -print0)

if [ ${#png_files[@]} -eq 0 ]; then
    echo "Error: No PNG files found in current directory."
    deactivate
    exit 1
fi

# Display available PNG files
echo "Available tileset images:"
echo ""
for i in "${!png_files[@]}"; do
    filename=$(basename "${png_files[$i]}")
    echo "  $((i+1)). $filename"
done
echo ""

# Prompt for selection
read -p "Select a tileset image (1-${#png_files[@]}): " selection

# Validate selection
if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt ${#png_files[@]} ]; then
    echo "Error: Invalid selection."
    deactivate
    exit 1
fi

# Get selected file (convert to absolute path)
selected_file="${png_files[$((selection-1))]}"
selected_abs=$(cd "$(dirname "$selected_file")" && pwd)/$(basename "$selected_file")

echo ""
echo "Selected: $(basename "$selected_abs")"
echo ""

# Run the Python script with the selected tileset
python select_tileset_tiles.py "$selected_abs"

# Deactivate virtual environment when done
deactivate

