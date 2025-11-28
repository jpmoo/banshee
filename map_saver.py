"""
Map saving and loading system.
Saves map terrain data and settlement structure (positions, names, vassal relationships).
Economy data is saved separately in game saves.
"""
import pickle
import os
from typing import List, Tuple, Optional
from terrain import Terrain
from settlements import Settlement, SettlementType


def save_map(map_data: List[List[Terrain]], map_width: int, map_height: int, 
             filepath: str, settlements: Optional[List[Settlement]] = None) -> bool:
    """
    Save map data and settlements to a file.
    
    Args:
        map_data: 2D list of Terrain objects
        map_width: Width of the map in tiles
        map_height: Height of the map in tiles
        filepath: Path to save the file
        settlements: Optional list of settlements to save
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Convert terrain to serializable format
        terrain_data = []
        for row in map_data:
            terrain_row = [tile.terrain_type.value for tile in row]
            terrain_data.append(terrain_row)
        
        # Convert settlements to serializable format
        settlements_data = []
        if settlements:
            # Create a mapping of settlements to IDs for vassal relationships
            settlement_ids = {}
            for i, settlement in enumerate(settlements):
                settlement_ids[id(settlement)] = i
            
            for settlement in settlements:
                settlement_dict = {
                    'settlement_type': settlement.settlement_type.value,
                    'x': settlement.x,
                    'y': settlement.y,
                    'name': settlement.name,
                    'supplies_resource': settlement.supplies_resource,
                    'vassal_to_id': None,  # Will be set below
                    # Note: Economy data (resources, trade_goods, money) is saved in game saves, not map saves
                }
                
                # Store vassal relationships by index
                if settlement.vassal_to:
                    for i, s in enumerate(settlements):
                        if s is settlement.vassal_to:
                            settlement_dict['vassal_to_id'] = i
                            break
                
                settlements_data.append(settlement_dict)
        
        save_data = {
            'map_width': map_width,
            'map_height': map_height,
            'terrain_data': terrain_data,
            'settlements': settlements_data,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        return True
    except Exception as e:
        print(f"Error saving map: {e}")
        return False


def load_map(filepath: str) -> Optional[Tuple[List[List[Terrain]], int, int, List[Settlement]]]:
    """
    Load map data and settlements from a file.
    
    Args:
        filepath: Path to the file to load
        
    Returns:
        Tuple of (map_data, map_width, map_height, settlements) if successful, None otherwise
    """
    try:
        from terrain import TerrainType
        
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        map_width = save_data['map_width']
        map_height = save_data['map_height']
        terrain_data = save_data['terrain_data']
        settlements_data = save_data.get('settlements', [])
        
        # Reconstruct terrain
        map_data = []
        for row in terrain_data:
            terrain_row = [Terrain(TerrainType(terrain_str)) for terrain_str in row]
            map_data.append(terrain_row)
        
        # Reconstruct settlements
        settlements = []
        for settlement_dict in settlements_data:
            settlement_type = SettlementType(settlement_dict['settlement_type'])
            settlement = Settlement(
                settlement_type=settlement_type,
                x=settlement_dict['x'],
                y=settlement_dict['y'],
                name=settlement_dict.get('name'),
                supplies_resource=settlement_dict.get('supplies_resource')
            )
            
            # Economy data is initialized to 0 by default (loaded from game saves if available)
            # Note: Economy data is saved separately in game saves, not map saves
            
            settlements.append(settlement)
        
        # Restore vassal relationships
        for i, settlement_dict in enumerate(settlements_data):
            settlement = settlements[i]
            vassal_to_id = settlement_dict.get('vassal_to_id')
            if vassal_to_id is not None and vassal_to_id < len(settlements):
                settlement.vassal_to = settlements[vassal_to_id]
                # Update vassal lists
                if settlement.settlement_type == SettlementType.VILLAGE:
                    if settlement.vassal_to:
                        settlement.vassal_to.vassal_villages.append(settlement)
                        resource = settlement.supplies_resource
                        if resource:
                            normalized_resource = settlement.supplies_resource
                            from settlements import normalize_resource_name
                            normalized_resource = normalize_resource_name(resource)
                            if normalized_resource not in settlement.vassal_to.resource_villages:
                                settlement.vassal_to.resource_villages[normalized_resource] = []
                            settlement.vassal_to.resource_villages[normalized_resource].append(settlement)
                elif settlement.settlement_type == SettlementType.TOWN:
                    if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.CITY:
                        settlement.vassal_to.vassal_towns.append(settlement)
        
        return (map_data, map_width, map_height, settlements)
    except Exception as e:
        print(f"Error loading map: {e}")
        return None


def get_saved_maps(maps_dir: str = "maps") -> List[str]:
    """
    Get a list of all saved map files.
    
    Args:
        maps_dir: Directory containing map files
        
    Returns:
        List of full paths to saved map files, sorted by filename (newest first)
    """
    map_files = []
    if os.path.exists(maps_dir):
        for filename in os.listdir(maps_dir):
            if filename.endswith('.banshee'):
                full_path = os.path.join(maps_dir, filename)
                map_files.append(full_path)
    # Sort by filename (which includes timestamp) in reverse order (newest first)
    map_files.sort(reverse=True)
    return map_files
