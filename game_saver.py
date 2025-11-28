"""
Game saving and loading system.
Saves game state including economy data, camera position, and map reference.
Matches existing save file format (gzip compressed).
"""
import pickle
import gzip
import os
import datetime
from typing import List, Tuple, Optional, Dict
from settlements import Settlement, RESOURCES


def save_game(settlements: List[Settlement], map_filepath: str, player_x: int, player_y: int,
              filepath: str, calendar_year: int = 0, calendar_month: int = 1, 
              calendar_day: int = 1, calendar_hour: int = 0,
              command_messages: List[str] = None, explored_tiles: set = None,
              visible_tiles: set = None) -> bool:
    """
    Save game state to a file (gzip compressed, matching existing format).
    
    Args:
        settlements: List of all settlements with their economy data
        map_filepath: Path to the map file being used
        player_x: Current player X position (camera center)
        player_y: Current player Y position (camera center)
        filepath: Path to save the game file
        calendar_year: Current game year
        calendar_month: Current game month
        calendar_day: Current game day
        calendar_hour: Current game hour
        command_messages: List of command messages
        explored_tiles: Set of explored tile coordinates
        visible_tiles: Set of visible tile coordinates
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Create a mapping of settlements to IDs for reference
        settlement_ids = {}
        for i, settlement in enumerate(settlements):
            settlement_ids[id(settlement)] = i
        
        # Save economy data for each settlement
        settlements_economy = []
        for settlement in settlements:
            settlement_dict = {
                'settlement_id': settlement_ids[id(settlement)],
                'resources': settlement.resources.copy() if hasattr(settlement, 'resources') else {},
                'trade_goods': settlement.trade_goods if hasattr(settlement, 'trade_goods') else 0,
                'money': settlement.money if hasattr(settlement, 'money') else 0,
            }
            settlements_economy.append(settlement_dict)
        
        save_data = {
            'map_filepath': map_filepath,
            'player_x': player_x,
            'player_y': player_y,
            'calendar_year': calendar_year,
            'calendar_month': calendar_month,
            'calendar_day': calendar_day,
            'calendar_hour': calendar_hour,
            'command_messages': command_messages or [],
            'explored_tiles': list(explored_tiles) if explored_tiles else [],
            'visible_tiles': list(visible_tiles) if visible_tiles else [],
            'save_timestamp': datetime.datetime.now().isoformat(),
            'settlements_economy': settlements_economy,  # Economy data
        }
        
        # Ensure saves directory exists
        saves_dir = os.path.dirname(filepath) if os.path.dirname(filepath) else "saves"
        os.makedirs(saves_dir, exist_ok=True)
        
        # Save as gzip compressed (matching existing format)
        with gzip.open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False


def load_game(filepath: str, settlements: List[Settlement]) -> Optional[Dict]:
    """
    Load game state from a file (gzip compressed, matching existing format).
    
    Args:
        filepath: Path to the game file to load
        settlements: List of settlements to restore economy data to
                    (must match the order from when the game was saved)
        
    Returns:
        Dictionary with game state data, or None if failed
    """
    try:
        # Load from gzip compressed file
        with gzip.open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        # Restore economy data to settlements
        settlements_economy = save_data.get('settlements_economy', [])
        for settlement_data in settlements_economy:
            settlement_id = settlement_data.get('settlement_id')
            if settlement_id is not None and settlement_id < len(settlements):
                settlement = settlements[settlement_id]
                
                # Restore resources
                if 'resources' in settlement_data:
                    settlement.resources = settlement_data['resources'].copy()
                    # Ensure all resources are present
                    for resource in RESOURCES:
                        if resource not in settlement.resources:
                            settlement.resources[resource] = 0
                else:
                    # Initialize to 0 if not present
                    settlement.resources = {resource: 0 for resource in RESOURCES}
                
                # Restore trade goods and money
                settlement.trade_goods = settlement_data.get('trade_goods', 0)
                settlement.money = settlement_data.get('money', 0)
        
        # Return all game state data
        return {
            'map_filepath': save_data.get('map_filepath', ''),
            'player_x': save_data.get('player_x', 0),
            'player_y': save_data.get('player_y', 0),
            'calendar_year': save_data.get('calendar_year', 0),
            'calendar_month': save_data.get('calendar_month', 1),
            'calendar_day': save_data.get('calendar_day', 1),
            'calendar_hour': save_data.get('calendar_hour', 0),
            'command_messages': save_data.get('command_messages', []),
            'explored_tiles': set(save_data.get('explored_tiles', [])),
            'visible_tiles': set(save_data.get('visible_tiles', [])),
            'save_timestamp': save_data.get('save_timestamp', ''),
        }
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def list_save_files(saves_dir: str = "saves") -> List[Tuple[str, str]]:
    """
    List all save files in the saves directory.
    
    Args:
        saves_dir: Directory containing save files
        
    Returns:
        List of tuples (filename, full_path) for each save file
    """
    save_files = []
    if os.path.exists(saves_dir):
        for filename in os.listdir(saves_dir):
            if filename.endswith('.banshee'):
                full_path = os.path.join(saves_dir, filename)
                save_files.append((filename, full_path))
    # Sort by filename (which includes timestamp)
    save_files.sort(reverse=True)
    return save_files

