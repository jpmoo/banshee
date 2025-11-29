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

# Find all PNG files directly in tilesets folder (not subdirectories)
png_files=()
tilesets_dir="tilesets"
if [ -d "$tilesets_dir" ]; then
    while IFS= read -r -d '' file; do
        png_files+=("$file")
    done < <(find "$tilesets_dir" -maxdepth 1 -type f -iname "*.png" -print0)
fi

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

# Delete existing JSON file for this PNG (if it exists)
png_basename=$(basename "$selected_abs" .png)
png_basename=$(basename "$png_basename" .PNG)  # Handle uppercase extension
json_file="tilesets/${png_basename}.json"
if [ -f "$json_file" ]; then
    rm "$json_file"
    echo "Deleted existing JSON file: $json_file"
fi

echo ""

# Run the Python script with the selected tileset
python select_tileset_tiles.py "$selected_abs"

# Deactivate virtual environment when done
deactivate

