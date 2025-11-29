"""
Map save/load functionality for persisting generated maps to disk.
"""
import pickle
import os
import gzip
from typing import List, Optional, Tuple, Dict
from terrain import Terrain
from settlements import Settlement, SettlementType


def save_map(map_data: List[List[Terrain]], width: int, height: int, 
             filepath: str, map_name: str, settlements: Optional[List[Settlement]] = None,
             seed: Optional[int] = None, worldbuilding_data: Optional[Dict] = None) -> bool:
    """
    Save a map to disk.
    
    Args:
        map_data: 2D list of Terrain objects
        width: Map width in tiles
        height: Map height in tiles
        filepath: Path to save the map file
        map_name: Name for the map
        settlements: Optional list of settlements to save
        seed: Optional seed used to generate the map
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Prepare data for saving
        save_data = {
            'width': width,
            'height': height,
            'map_data': map_data,
            'map_name': map_name,
            'settlements': settlements if settlements is not None else [],
            'seed': seed,
            'worldbuilding_data': worldbuilding_data  # Worldbuilding data from OpenAI
        }
        
        # Debug: Print settlement info before saving
        if settlements:
            print(f"Debug save: Saving {len(settlements)} settlements")
            town_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.TOWN)
            village_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.VILLAGE)
            city_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.CITY)
            print(f"Debug save: {city_count} cities, {town_count} towns, {village_count} villages")
        else:
            print("Debug save: WARNING - settlements is None or empty!")
        
        # Save to file using pickle with gzip compression
        # Use protocol 4 or higher to handle circular references better
        with gzip.open(filepath, 'wb', compresslevel=6) as f:
            pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        return True
    except Exception as e:
        print(f"Error saving map: {e}")
        return False


def load_map(filepath: str) -> Optional[Tuple[List[List[Terrain]], int, int, str, List[Settlement], Optional[int], Optional[Dict]]]:
    """
    Load a map from disk.
    
    Args:
        filepath: Path to the map file
        
    Returns:
        Tuple of (map_data, width, height, map_name, settlements, seed, worldbuilding_data) if successful, None otherwise
    """
    try:
        if not os.path.exists(filepath):
            print(f"Map file not found: {filepath}")
            return None
        
        # Load from file - try gzip first (new format), fall back to uncompressed (old format)
        try:
            # Try compressed format first
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            # Fall back to uncompressed format for backward compatibility
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        
        map_data = save_data['map_data']
        width = save_data['width']
        height = save_data['height']
        # Handle old save files that don't have map_name, settlements, seed, or worldbuilding_data
        map_name = save_data.get('map_name', os.path.basename(filepath).replace('.banshee', ''))
        settlements = save_data.get('settlements', [])
        seed = save_data.get('seed', None)
        worldbuilding_data = save_data.get('worldbuilding_data', None)
        
        # Debug: Print worldbuilding data info
        if worldbuilding_data:
            print(f"Debug load: Worldbuilding data found in map file")
            print(f"Debug load: Worldbuilding data has {len(worldbuilding_data)} top-level keys")
            if isinstance(worldbuilding_data, dict):
                for key in list(worldbuilding_data.keys())[:5]:  # Show first 5 keys
                    print(f"Debug load:   - {key}")
        else:
            print("Debug load: No worldbuilding data in map file")
        
        # Debug: Print settlement info after loading
        if settlements:
            print(f"Debug load: Loaded {len(settlements)} settlements")
            town_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.TOWN)
            village_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.VILLAGE)
            city_count = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.CITY)
            print(f"Debug load: {city_count} cities, {town_count} towns, {village_count} villages")
            
            # Migrate settlements: ensure economy attributes exist (for old maps)
            for settlement in settlements:
                if settlement.settlement_type == SettlementType.TOWN:
                    if not hasattr(settlement, 'resources') or settlement.resources is None:
                        settlement.resources = {
                            'lumber': 0,
                            'fish and fowl': 0,
                            'grain and livestock': 0,
                            'ore': 0
                        }
                    if not hasattr(settlement, 'trade_goods') or settlement.trade_goods is None:
                        settlement.trade_goods = 0
                    if not hasattr(settlement, 'money') or settlement.money is None:
                        settlement.money = 0
                elif settlement.settlement_type == SettlementType.CITY:
                    if not hasattr(settlement, 'trade_goods') or settlement.trade_goods is None:
                        settlement.trade_goods = 0
                    if not hasattr(settlement, 'money') or settlement.money is None:
                        settlement.money = 0
            
            # Verify vassal relationships
            if settlements:
                villages_with_towns = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.VILLAGE and hasattr(s, 'vassal_to') and s.vassal_to is not None)
                towns_with_cities = sum(1 for s in settlements if hasattr(s, 'settlement_type') and s.settlement_type == SettlementType.TOWN and hasattr(s, 'vassal_to') and s.vassal_to is not None)
                print(f"Debug load: {villages_with_towns} villages with town links, {towns_with_cities} towns with city links")
        else:
            print("Debug load: WARNING - No settlements loaded from file!")
        
        return (map_data, width, height, map_name, settlements, seed, worldbuilding_data)
    except Exception as e:
        print(f"Error loading map: {e}")
        return None


def get_saved_maps(directory: str = "maps") -> List[Tuple[str, str, Optional[int]]]:
    """
    Get list of saved map files in a directory with their names and seeds.
    
    Args:
        directory: Directory to search for map files
    
    Returns:
        List of tuples (filepath, map_name, seed) sorted by map name
    """
    if not os.path.exists(directory):
        return []
    
    map_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.banshee'):
            filepath = os.path.join(directory, filename)
            # Try to load the map name and seed, fallback to filename if it fails
            try:
                # Try compressed format first
                try:
                    with gzip.open(filepath, 'rb') as f:
                        save_data = pickle.load(f)
                except (gzip.BadGzipFile, OSError):
                    # Fall back to uncompressed format
                    with open(filepath, 'rb') as f:
                        save_data = pickle.load(f)
                map_name = save_data.get('map_name', os.path.basename(filepath).replace('.banshee', ''))
                seed = save_data.get('seed', None)
            except:
                map_name = os.path.basename(filepath).replace('.banshee', '')
                seed = None
            map_files.append((filepath, map_name, seed))
    
    # Sort by map name
    map_files.sort(key=lambda x: x[1].lower())
    return map_files


def get_map_name(filepath: str) -> Optional[str]:
    """
    Get the name of a saved map without loading the entire map.
    
    Args:
        filepath: Path to the map file
        
    Returns:
        Map name if successful, None otherwise
    """
    try:
        if not os.path.exists(filepath):
            return None
        
        # Try compressed format first, fall back to uncompressed
        try:
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        return save_data.get('map_name', os.path.basename(filepath).replace('.banshee', ''))
    except:
        return None


def get_map_metadata(filepath: str) -> Optional[Tuple[str, List[Settlement]]]:
    """
    Get map name and settlements from a map file without fully loading terrain.
    Note: This still deserializes the entire file, but we only use the metadata.
    For better performance, avoid calling this for many files at once.
    
    Args:
        filepath: Path to the map file
        
    Returns:
        Tuple of (map_name, settlements) if successful, None otherwise
    """
    try:
        if not os.path.exists(filepath):
            return None
        
        # Try compressed format first, fall back to uncompressed
        try:
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        
        map_name = save_data.get('map_name', os.path.basename(filepath).replace('.banshee', ''))
        settlements = save_data.get('settlements', [])
        
        return (map_name, settlements)
    except Exception as e:
        print(f"Error loading map metadata from {filepath}: {e}")
        return None


def get_map_seed(filepath: str) -> Optional[int]:
    """
    Get the seed of a saved map without loading the entire map.
    
    Args:
        filepath: Path to the map file
        
    Returns:
        Map seed if successful, None otherwise
    """
    try:
        if not os.path.exists(filepath):
            return None
        
        # Try compressed format first, fall back to uncompressed
        try:
            with gzip.open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        except (gzip.BadGzipFile, OSError):
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
        return save_data.get('seed', None)
    except:
        return None


def map_name_exists(map_name: str, directory: str = "maps") -> bool:
    """
    Check if a map name already exists.
    
    Args:
        map_name: Name to check
        directory: Directory to search for map files
        
    Returns:
        True if name exists, False otherwise
    """
    saved_maps = get_saved_maps(directory)
    for _, name in saved_maps:
        if name.lower() == map_name.lower():
            return True
    return False





