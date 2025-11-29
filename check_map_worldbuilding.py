#!/usr/bin/env python3
"""
Check if worldbuilding data exists in a map file.
"""
import sys
import os
import pickle
import gzip
import json


def check_map_worldbuilding(filepath: str):
    """Check if worldbuilding data exists in a map file."""
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
        
        # Check for worldbuilding data
        worldbuilding_data = save_data.get('worldbuilding_data', None)
        
        if worldbuilding_data:
            print(f"✓ Worldbuilding data found in {filepath}")
            print(f"  Top-level keys: {len(worldbuilding_data)}")
            if isinstance(worldbuilding_data, dict):
                print(f"  Keys: {list(worldbuilding_data.keys())[:10]}")  # Show first 10
                
                # Check structure
                for key in list(worldbuilding_data.keys())[:3]:
                    data = worldbuilding_data[key]
                    if isinstance(data, dict):
                        print(f"\n  {key}:")
                        print(f"    Keys: {list(data.keys())[:5]}")
                        if 'description' in data:
                            desc = data['description']
                            print(f"    Has description: {len(desc)} chars")
                        if 'leader' in data:
                            leader = data['leader']
                            print(f"    Has leader: {list(leader.keys()) if isinstance(leader, dict) else 'N/A'}")
        else:
            print(f"✗ No worldbuilding data in {filepath}")
        
        # Check settlements
        settlements = save_data.get('settlements', [])
        if settlements:
            print(f"\n  Settlements: {len(settlements)}")
            from settlements import SettlementType
            cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
            towns = [s for s in settlements if s.settlement_type == SettlementType.TOWN]
            villages = [s for s in settlements if s.settlement_type == SettlementType.VILLAGE]
            print(f"    Cities: {len(cities)}")
            print(f"    Towns: {len(towns)}")
            print(f"    Villages: {len(villages)}")
        
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_map_worldbuilding.py <map_file_path>")
        sys.exit(1)
    
    check_map_worldbuilding(sys.argv[1])

