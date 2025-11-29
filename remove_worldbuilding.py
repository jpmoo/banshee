#!/usr/bin/env python3
"""
Utility script to remove worldbuilding data from map files.
"""
import pickle
import gzip
import os
import sys
from pathlib import Path


def remove_worldbuilding_from_map(filepath: str) -> bool:
    """
    Remove worldbuilding_data from a map file.
    
    Args:
        filepath: Path to the map file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(filepath):
            print(f"Error: Map file not found: {filepath}")
            return False
        
        # Load from file
        try:
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        
        # Check if worldbuilding_data exists
        if 'worldbuilding_data' in save_data:
            print(f"Removing worldbuilding data from {filepath}...")
            del save_data['worldbuilding_data']
            
            # Save back to file
            try:
                with gzip.open(filepath, 'wb') as f:
                    pickle.dump(save_data, f)
                print(f"Successfully removed worldbuilding data from {filepath}")
                return True
            except Exception as e:
                print(f"Error saving file: {e}")
                return False
        else:
            print(f"No worldbuilding data found in {filepath}")
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python remove_worldbuilding.py <map_file_path> [<map_file_path> ...]")
        print("   or: python remove_worldbuilding.py --all")
        sys.exit(1)
    
    if sys.argv[1] == '--all':
        # Find all map files in maps directory
        maps_dir = Path('maps')
        if not maps_dir.exists():
            print("Error: maps directory not found")
            sys.exit(1)
        
        map_files = list(maps_dir.glob('*.banshee')) + list(maps_dir.glob('*.banshee_map'))
        if not map_files:
            print("No map files found in maps directory")
            sys.exit(0)
        
        print(f"Found {len(map_files)} map file(s)")
        for map_file in map_files:
            remove_worldbuilding_from_map(str(map_file))
    else:
        # Process specified files
        for filepath in sys.argv[1:]:
            remove_worldbuilding_from_map(filepath)


if __name__ == '__main__':
    main()

