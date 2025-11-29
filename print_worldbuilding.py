#!/usr/bin/env python3
"""
Print all worldbuilding data from a map file.
"""
import sys
import os
import pickle
import gzip
import json


def print_worldbuilding(filepath: str):
    """Print all worldbuilding data from a map file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    
    try:
        # Try to load the map file
        try:
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        
        # Get worldbuilding data
        worldbuilding_data = save_data.get('worldbuilding_data', None)
        
        if worldbuilding_data:
            print("="*80)
            print("WORLDBUILDING DATA:")
            print("="*80)
            print(json.dumps(worldbuilding_data, indent=2, ensure_ascii=False))
            print("="*80)
            
            # Also print summary
            print(f"\nSummary:")
            print(f"  Top-level keys: {len(worldbuilding_data)}")
            if isinstance(worldbuilding_data, dict):
                for key in worldbuilding_data.keys():
                    data = worldbuilding_data[key]
                    if isinstance(data, dict):
                        print(f"\n  {key}:")
                        print(f"    Keys: {list(data.keys())}")
                        if 'description' in data:
                            desc = data['description']
                            print(f"    Description: {desc[:100]}...")
                        if 'leader' in data:
                            leader = data['leader']
                            if isinstance(leader, dict):
                                if 'name' in leader:
                                    print(f"    Leader name: {leader['name']}")
        else:
            print("✗ No worldbuilding data in file")
        
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python print_worldbuilding.py <map_file_path>")
        sys.exit(1)
    
    print_worldbuilding(sys.argv[1])

