"""
Quest generation system.
Generates procedurally generated quests with locations, distances, and directions.
"""
import random
import math
from typing import Optional, Tuple, List, Dict
from terrain import Terrain, TerrainType
from settlements import Settlement, SettlementType
from data_quest_locations import quest_location_descriptions


def generate_quest(settlement: Settlement, map_data: List[List[Terrain]], 
                   map_width: int, map_height: int, pathfinder=None) -> Optional[Dict]:
    """
    Generate a quest for a settlement.
    
    Args:
        settlement: The settlement offering the quest
        map_data: 2D list of terrain data
        map_width: Map width in tiles
        map_height: Map height in tiles
        pathfinder: Optional pathfinding function (x1, y1, x2, y2) -> List[Tuple[int, int]]
        
    Returns:
        Quest dictionary or None if no valid location found
    """
    # Determine distance constraints based on settlement type
    if settlement.settlement_type == SettlementType.VILLAGE:
        min_days = 2
        max_days = 5
        require_path = True
    elif settlement.settlement_type == SettlementType.TOWN:
        min_days = 3
        max_days = 10
        require_path = True
    else:  # CITY
        min_days = 10
        max_days = None  # No maximum
        require_path = False
    
    # Try each location terrain type in random order until we find a valid location
    location_types = ["hill", "forested_hill", "grassland", "forest", "waterside"]
    random.shuffle(location_types)  # Randomize order
    
    quest_x, quest_y = None, None
    location_terrain_type = None
    
    # First pass: try with original constraints
    for terrain_type in location_types:
        # Try to find valid location for this terrain type
        quest_x, quest_y = find_quest_location(
            settlement, map_data, map_width, map_height,
            terrain_type, min_days, max_days, require_path, pathfinder
        )
        
        if quest_x is not None and quest_y is not None:
            # Found a valid location!
            location_terrain_type = terrain_type
            break
    
    # Second pass: find ANY passable terrain within reasonable distance
    if quest_x is None or quest_y is None:
        # Find any passable terrain within distance constraints
        # Sample random tiles to check (much faster than checking all)
        all_tiles = [(x, y) for y in range(map_height) for x in range(map_width) 
                     if map_data[y][x].can_move_through()]
        random.shuffle(all_tiles)
        
        # Check up to 200 random tiles
        for x, y in all_tiles[:200]:
            # Quick straight-line distance estimate first
            straight_distance_days = estimate_straight_line_distance(
                settlement.x, settlement.y, x, y, map_data
            ) / 24.0
            
            # Quick filter on straight-line distance
            if straight_distance_days < min_days * 0.8:
                continue
            if max_days is not None and straight_distance_days > max_days * 1.5:
                continue
            
            # Full path distance calculation
            distance_hours = calculate_path_distance(
                settlement.x, settlement.y, x, y,
                map_data, map_width, map_height, pathfinder
            )
            distance_days = distance_hours / 24.0
            
            # Check distance constraints
            if distance_days < min_days:
                continue
            if max_days is not None and distance_days > max_days:
                continue
            
            # Check path if required
            if require_path:
                if pathfinder:
                    path = pathfinder(settlement.x, settlement.y, x, y)
                    if not path:
                        continue
                else:
                    if not has_passable_route(settlement.x, settlement.y, x, y, map_data, map_width, map_height):
                        continue
            
            # Found a valid location!
            quest_x, quest_y = x, y
            # Determine terrain type
            terrain = map_data[y][x]
            if terrain.terrain_type == TerrainType.HILLS:
                location_terrain_type = "hill"
            elif terrain.terrain_type == TerrainType.FORESTED_HILL:
                location_terrain_type = "forested_hill"
            elif terrain.terrain_type == TerrainType.FOREST:
                location_terrain_type = "forest"
            else:
                location_terrain_type = "grassland"
            break
    
    # If STILL no location found (should be extremely rare), use settlement position + offset
    if quest_x is None or quest_y is None:
        # Place quest at a fixed offset from settlement (fallback)
        offset_x = min(50, map_width // 10)
        offset_y = min(50, map_height // 10)
        quest_x = min(map_width - 1, max(0, settlement.x + offset_x))
        quest_y = min(map_height - 1, max(0, settlement.y + offset_y))
        location_terrain_type = "grassland"
    
    # Calculate distance in hours
    distance_hours = calculate_path_distance(
        settlement.x, settlement.y, quest_x, quest_y,
        map_data, map_width, map_height, pathfinder
    )
    distance_days = distance_hours / 24.0
    
    # Determine compass direction
    direction = get_compass_direction(settlement.x, settlement.y, quest_x, quest_y)
    
    # Select a random location description for this terrain type
    location_descriptions = quest_location_descriptions.get(location_terrain_type, [])
    if location_descriptions:
        location_description = random.choice(location_descriptions)
    else:
        # Fallback if no descriptions available for this terrain type
        location_description = f"{location_terrain_type.replace('_', ' ')} location"
    
    # Build quest data
    quest = {
        'quest_giver': settlement,
        'quest_type': 'fetch',
        'location_terrain_type': location_terrain_type,
        'location_description': location_description,  # Store the description
        'quest_coordinates': (quest_x, quest_y),
        'quest_direction': direction,
        'distance': distance_hours,  # Store in hours
        'distance_days': distance_days
    }
    
    return quest


def find_quest_location(settlement: Settlement, map_data: List[List[Terrain]],
                       map_width: int, map_height: int, location_type: str,
                       min_days: float, max_days: Optional[float],
                       require_path: bool, pathfinder=None) -> Tuple[Optional[int], Optional[int]]:
    """
    Find a valid quest location matching the terrain type and distance constraints.
    
    Returns:
        (x, y) coordinates or (None, None) if no valid location found
    """
    settlement_x, settlement_y = settlement.x, settlement.y
    
    # Map location type to terrain type
    terrain_type_map = {
        "hill": TerrainType.HILLS,
        "forested_hill": TerrainType.FORESTED_HILL,
        "grassland": TerrainType.GRASSLAND,
        "forest": TerrainType.FOREST,
        "waterside": None  # Special case - any passable terrain next to water
    }
    
    target_terrain = terrain_type_map.get(location_type)
    
    # Collect all candidate locations
    # First pass: collect all matching terrain tiles (fast)
    terrain_matches = []
    
    for y in range(map_height):
        for x in range(map_width):
            terrain = map_data[y][x]
            
            # Check if terrain matches
            if location_type == "waterside":
                # Check if this is passable terrain adjacent to water
                if not terrain.can_move_through():
                    continue
                # Check if adjacent to water
                is_waterside = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < map_width and 0 <= ny < map_height:
                            adj_terrain = map_data[ny][nx]
                            if adj_terrain.terrain_type in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, TerrainType.RIVER]:
                                is_waterside = True
                                break
                    if is_waterside:
                        break
                if not is_waterside:
                    continue
            else:
                # Check if terrain type matches
                if terrain.terrain_type != target_terrain:
                    continue
                if not terrain.can_move_through():
                    continue
            
            terrain_matches.append((x, y))
    
    if not terrain_matches:
        return (None, None)
    
    # Shuffle and sample a subset for distance/path checking (much faster)
    random.shuffle(terrain_matches)
    # Check up to 100 candidates (or all if fewer)
    max_candidates_to_check = min(100, len(terrain_matches))
    candidates = []
    
    for x, y in terrain_matches[:max_candidates_to_check]:
        # Quick straight-line distance estimate first
        straight_distance_days = estimate_straight_line_distance(settlement_x, settlement_y, x, y, map_data) / 24.0
        
        # Quick filter on straight-line distance (with some margin for actual path being longer)
        if straight_distance_days < min_days * 0.8:  # Allow some margin
            continue
        if max_days is not None and straight_distance_days > max_days * 1.2:  # Allow some margin
            continue
        
        # Now do full path distance calculation (only for promising candidates)
        distance_hours = calculate_path_distance(
            settlement_x, settlement_y, x, y,
            map_data, map_width, map_height, pathfinder
        )
        distance_days = distance_hours / 24.0
        
        # Check distance constraints
        if distance_days < min_days:
            continue
        if max_days is not None and distance_days > max_days:
            continue
        
        # Check path if required
        if require_path:
            if pathfinder:
                path = pathfinder(settlement_x, settlement_y, x, y)
                if not path:
                    continue
            else:
                # Simple check - ensure there's a passable route
                if not has_passable_route(settlement_x, settlement_y, x, y, map_data, map_width, map_height):
                    continue
        
        candidates.append((x, y, distance_days))
        
        # If we found enough candidates, we can stop early
        if len(candidates) >= 10:
            break
    
    # If we didn't find any in the sample, try a few more random ones
    if not candidates and len(terrain_matches) > max_candidates_to_check:
        for x, y in random.sample(terrain_matches[max_candidates_to_check:], min(50, len(terrain_matches) - max_candidates_to_check)):
            # Quick straight-line distance estimate
            straight_distance_days = estimate_straight_line_distance(settlement_x, settlement_y, x, y, map_data) / 24.0
            if straight_distance_days < min_days * 0.8 or (max_days is not None and straight_distance_days > max_days * 1.2):
                continue
            
            distance_hours = calculate_path_distance(
                settlement_x, settlement_y, x, y,
                map_data, map_width, map_height, pathfinder
            )
            distance_days = distance_hours / 24.0
            
            if distance_days < min_days or (max_days is not None and distance_days > max_days):
                continue
            
            if require_path:
                if pathfinder:
                    path = pathfinder(settlement_x, settlement_y, x, y)
                    if not path:
                        continue
                else:
                    if not has_passable_route(settlement_x, settlement_y, x, y, map_data, map_width, map_height):
                        continue
            
            candidates.append((x, y, distance_days))
            if len(candidates) >= 10:
                break
    
    if not candidates:
        return (None, None)
    
    # Randomly select from candidates
    selected = random.choice(candidates)
    return (selected[0], selected[1])


def calculate_path_distance(x1: int, y1: int, x2: int, y2: int,
                           map_data: List[List[Terrain]], map_width: int, map_height: int,
                           pathfinder=None) -> float:
    """
    Calculate travel time in hours for a path between two points.
    
    Args:
        x1, y1: Start coordinates
        x2, y2: End coordinates
        map_data: 2D list of terrain data
        map_width: Map width
        map_height: Map height
        pathfinder: Optional pathfinding function
        
    Returns:
        Total travel time in hours
    """
    if pathfinder:
        path = pathfinder(x1, y1, x2, y2)
        if not path:
            # Fallback to straight-line estimate
            return estimate_straight_line_distance(x1, y1, x2, y2, map_data)
        
        total_hours = 0.0
        current_x, current_y = x1, y1
        
        for next_x, next_y in path:
            # Get terrain at current position
            if 0 <= current_y < map_height and 0 <= current_x < map_width:
                terrain = map_data[current_y][current_x]
                hours = get_movement_time(terrain.terrain_type)
                total_hours += hours
            current_x, current_y = next_x, next_y
        
        # Add time for final tile
        if 0 <= current_y < map_height and 0 <= current_x < map_width:
            terrain = map_data[current_y][current_x]
            hours = get_movement_time(terrain.terrain_type)
            total_hours += hours
        
        return total_hours
    else:
        # Fallback to straight-line estimate
        return estimate_straight_line_distance(x1, y1, x2, y2, map_data)


def estimate_straight_line_distance(x1: int, y1: int, x2: int, y2: int,
                                    map_data: List[List[Terrain]]) -> float:
    """
    Estimate distance using straight-line path with average terrain speed.
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    distance = math.sqrt(dx * dx + dy * dy)
    
    # Use average movement time (3 hours per tile as rough estimate)
    return distance * 3.0


def has_passable_route(x1: int, y1: int, x2: int, y2: int,
                      map_data: List[List[Terrain]], map_width: int, map_height: int) -> bool:
    """
    Simple check if there's a passable route between two points.
    Uses a simple flood-fill approach.
    """
    # Simple BFS to check connectivity
    visited = set()
    queue = [(x1, y1)]
    visited.add((x1, y1))
    
    while queue:
        x, y = queue.pop(0)
        
        if x == x2 and y == y2:
            return True
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < map_width and 0 <= ny < map_height:
                if (nx, ny) not in visited:
                    terrain = map_data[ny][nx]
                    if terrain.can_move_through():
                        visited.add((nx, ny))
                        queue.append((nx, ny))
    
    return False


def get_movement_time(terrain_type: TerrainType) -> float:
    """
    Get movement time in hours for a terrain type.
    """
    movement_times = {
        TerrainType.GRASSLAND: 2.0,
        TerrainType.FOREST: 4.0,
        TerrainType.HILLS: 4.0,
        TerrainType.FORESTED_HILL: 4.0,
        TerrainType.MOUNTAIN: 8.0,
        TerrainType.RIVER: 2.0,
        TerrainType.SHALLOW_WATER: 3.0,
        TerrainType.DEEP_WATER: 0.0,
    }
    return movement_times.get(terrain_type, 2.0)


def get_compass_direction(x1: int, y1: int, x2: int, y2: int) -> str:
    """
    Get general compass direction from point 1 to point 2.
    Only returns cardinal directions (north, south, east, west).
    
    Returns:
        One of: "north", "south", "east", "west"
    """
    dx = x2 - x1
    dy = y2 - y1
    
    # Normalize to get direction
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        return "here"  # Same location
    
    # Calculate angle
    angle = math.atan2(dy, dx)
    angle_deg = math.degrees(angle)
    
    # Normalize to 0-360
    if angle_deg < 0:
        angle_deg += 360
    
    # Map to cardinal directions only (north, south, east, west)
    # Use 90-degree sectors centered on each cardinal direction
    if 315 <= angle_deg or angle_deg < 45:
        return "east"
    elif 45 <= angle_deg < 135:
        return "south"
    elif 135 <= angle_deg < 225:
        return "west"
    else:  # 225 <= angle_deg < 315
        return "north"

