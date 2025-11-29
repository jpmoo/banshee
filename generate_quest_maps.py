"""
Generate specific maps for each quest location description.
This script creates map data for all 250 descriptions and saves them.
"""
import json
from data_quest_locations import quest_location_descriptions
from quest_location_maps import generate_quest_location_map

# Standard quest location map size
MAP_SIZE = 50  # Will be adjusted to viewport size, but use this for generation

def generate_all_maps():
    """Generate maps for all descriptions and return as dictionary."""
    all_maps = {}
    
    for terrain_type, descriptions in quest_location_descriptions.items():
        all_maps[terrain_type] = {}
        print(f"Generating maps for {terrain_type}...")
        
        for i, description in enumerate(descriptions, 1):
            print(f"  [{i}/{len(descriptions)}] {description[:50]}...")
            
            # Generate map
            map_data = generate_quest_location_map(description, terrain_type, MAP_SIZE)
            
            # Convert to serializable format (list of terrain type strings)
            map_array = []
            for row in map_data:
                map_row = []
                for terrain in row:
                    map_row.append(terrain.terrain_type.value)
                map_array.append(map_row)
            
            # Store with description
            all_maps[terrain_type][description] = map_array
    
    return all_maps

def save_maps_to_file(maps_data, filename="quest_location_maps_data.json"):
    """Save maps to JSON file."""
    with open(filename, 'w') as f:
        json.dump(maps_data, f, indent=2)
    print(f"\n✓ Saved {filename}")

if __name__ == "__main__":
    print("Generating quest location maps...")
    maps = generate_all_maps()
    save_maps_to_file(maps)
    print(f"\n✓ Generated maps for {sum(len(descs) for descs in quest_location_descriptions.values())} descriptions")

Generate specific maps for each quest location description.
This script creates map data for all 250 descriptions and saves them.
"""
import json
from data_quest_locations import quest_location_descriptions
from quest_location_maps import generate_quest_location_map

# Standard quest location map size
MAP_SIZE = 50  # Will be adjusted to viewport size, but use this for generation

def generate_all_maps():
    """Generate maps for all descriptions and return as dictionary."""
    all_maps = {}
    
    for terrain_type, descriptions in quest_location_descriptions.items():
        all_maps[terrain_type] = {}
        print(f"Generating maps for {terrain_type}...")
        
        for i, description in enumerate(descriptions, 1):
            print(f"  [{i}/{len(descriptions)}] {description[:50]}...")
            
            # Generate map
            map_data = generate_quest_location_map(description, terrain_type, MAP_SIZE)
            
            # Convert to serializable format (list of terrain type strings)
            map_array = []
            for row in map_data:
                map_row = []
                for terrain in row:
                    map_row.append(terrain.terrain_type.value)
                map_array.append(map_row)
            
            # Store with description
            all_maps[terrain_type][description] = map_array
    
    return all_maps

def save_maps_to_file(maps_data, filename="quest_location_maps_data.json"):
    """Save maps to JSON file."""
    with open(filename, 'w') as f:
        json.dump(maps_data, f, indent=2)
    print(f"\n✓ Saved {filename}")

if __name__ == "__main__":
    print("Generating quest location maps...")
    maps = generate_all_maps()
    save_maps_to_file(maps)
    print(f"\n✓ Generated maps for {sum(len(descs) for descs in quest_location_descriptions.values())} descriptions")

