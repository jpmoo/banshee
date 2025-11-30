"""
Quest location map generation.
Loads pre-generated maps for quest locations based on their descriptions.
"""
import json
import os
from typing import List, Optional
from terrain import Terrain, TerrainType

# Cache for loaded maps
_maps_cache = None

def _load_maps_data() -> dict:
    """Load maps data from JSON file."""
    global _maps_cache
    if _maps_cache is not None:
        return _maps_cache
    
    maps_file = os.path.join(os.path.dirname(__file__), "quest_location_maps_data.json")
    if not os.path.exists(maps_file):
        print(f"Warning: Quest location maps file not found: {maps_file}")
        return {}
    
    try:
        with open(maps_file, 'r') as f:
            _maps_cache = json.load(f)
        return _maps_cache
    except Exception as e:
        print(f"Error loading quest location maps: {e}")
        return {}


def _resize_map(map_data: List[List[str]], target_size: int) -> List[List[str]]:
    """Resize a map to target size, cropping or padding as needed."""
    source_size = len(map_data)
    if source_size == 0:
        return [[TerrainType.GRASSLAND.value] * target_size for _ in range(target_size)]
    
    # If sizes match, return as-is
    if source_size == target_size:
        return map_data
    
    # Create new map
    resized = []
    for y in range(target_size):
        row = []
        for x in range(target_size):
            # Map coordinates from target to source
            source_x = int(x * source_size / target_size)
            source_y = int(y * source_size / target_size)
            # Clamp to source bounds
            source_x = min(source_x, source_size - 1)
            source_y = min(source_y, source_size - 1)
            row.append(map_data[source_y][source_x])
        resized.append(row)
    
    return resized


def generate_quest_location_map(description: str, location_terrain_type: str, 
                                size: int) -> List[List[Terrain]]:
    """
    Load a pre-generated quest location map based on the description and terrain type.
    
    Args:
        description: The location description text (may include item text, will be stripped for lookup)
        location_terrain_type: The terrain type ("hill", "forested_hill", "forest", "grassland", "waterside")
        size: The size of the map (size x size)
        
    Returns:
        2D list of Terrain objects
    """
    # Load maps data
    maps_data = _load_maps_data()
    
    # Strip any appended item text from description for map lookup
    # Maps are stored with original descriptions, but quest descriptions may have "There, you must retrieve..." appended
    lookup_description = description
    if " There, you must retrieve " in description:
        lookup_description = description.split(" There, you must retrieve ")[0]
    
    # Get map for this description
    terrain_maps = maps_data.get(location_terrain_type, {})
    map_array = terrain_maps.get(lookup_description)
    
    # If map not found, fall back to default terrain
    if map_array is None:
        # Map location terrain type to TerrainType for outer edges
        edge_terrain_map = {
            "hill": TerrainType.HILLS,
            "forested_hill": TerrainType.FORESTED_HILL,
            "forest": TerrainType.FOREST,
            "grassland": TerrainType.GRASSLAND,
            "waterside": TerrainType.GRASSLAND
        }
        edge_terrain = edge_terrain_map.get(location_terrain_type, TerrainType.GRASSLAND)
        
        # Create default map
        map_data = []
        for y in range(size):
            row = []
            for x in range(size):
                row.append(Terrain(edge_terrain))
            map_data.append(row)
        return map_data
    
    # Resize map to target size
    resized_map = _resize_map(map_array, size)
    
    # Convert to Terrain objects
    map_data = []
    for row in resized_map:
        terrain_row = []
        for terrain_str in row:
            # Convert string to TerrainType
            try:
                terrain_type = TerrainType(terrain_str)
            except ValueError:
                # Fallback to grassland if unknown
                terrain_type = TerrainType.GRASSLAND
            terrain_row.append(Terrain(terrain_type))
        map_data.append(terrain_row)
    
    return map_data

