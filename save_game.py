"""
Save and load game state.
"""
import os
import pickle
import gzip
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from celtic_calendar import CelticCalendar
from map_saver import get_map_name, load_map
from settlements import Settlement, SettlementType


def save_game(map_filepath: str, player_x: int, player_y: int, 
              calendar: CelticCalendar, command_messages: List[str],
              explored_tiles: set, visible_tiles: set,
              settlements: Optional[List] = None,
              tileset_info: Optional[Dict] = None,
              directory: str = "saves") -> Optional[str]:
    """
    Save the current game state.
    
    Args:
        map_filepath: Path to the map file being used (will be converted to relative)
        player_x: Player X position
        player_y: Player Y position
        calendar: Celtic calendar instance
        command_messages: Last 30 items from message log
        explored_tiles: Set of explored tile coordinates
        visible_tiles: Set of visible tile coordinates
        settlements: List of settlements with their economy state
        directory: Directory to save to
        
    Returns:
        Filepath of saved game if successful, None otherwise
    """
    try:
        # Create saves directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Convert map_filepath to relative path if it's absolute
        relative_map_path = map_filepath
        if os.path.isabs(map_filepath):
            # Get the current working directory (game folder)
            game_dir = os.getcwd()
            try:
                # Try to make it relative
                relative_map_path = os.path.relpath(map_filepath, game_dir)
            except ValueError:
                # If that fails (different drives on Windows), keep original but log warning
                print(f"Warning: Could not convert absolute path to relative: {map_filepath}")
                relative_map_path = map_filepath
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"save_{timestamp}.banshee"
        filepath = os.path.join(directory, filename)
        
        # Extract settlement economy data (resources, trade_goods, money)
        settlement_economy = {}
        if settlements:
            for settlement in settlements:
                economy_data = {}
                
                if settlement.settlement_type.value == "town":
                    if hasattr(settlement, 'resources') and settlement.resources is not None:
                        economy_data['resources'] = settlement.resources.copy()
                    if hasattr(settlement, 'trade_goods') and settlement.trade_goods is not None:
                        economy_data['trade_goods'] = settlement.trade_goods
                    if hasattr(settlement, 'money') and settlement.money is not None:
                        economy_data['money'] = settlement.money
                elif settlement.settlement_type.value == "city":
                    if hasattr(settlement, 'trade_goods') and settlement.trade_goods is not None:
                        economy_data['trade_goods'] = settlement.trade_goods
                    if hasattr(settlement, 'money') and settlement.money is not None:
                        economy_data['money'] = settlement.money
                
                if economy_data:
                    # Use position and type as identifier (more reliable than object ID)
                    settlement_key = (settlement.x, settlement.y, settlement.settlement_type.value)
                    settlement_economy[settlement_key] = economy_data
        
        # Get map name from map file
        map_name = None
        if map_filepath:
            map_name = get_map_name(map_filepath)
        
        # Find nearest settlement for location info
        nearest_settlement_info = None
        if settlements and player_x is not None and player_y is not None:
            # Find nearest city or town
            cities_and_towns = [s for s in settlements if s.settlement_type in (SettlementType.CITY, SettlementType.TOWN)]
            if cities_and_towns:
                nearest = None
                min_distance = float('inf')
                for settlement in cities_and_towns:
                    sx, sy = settlement.get_position()
                    distance = abs(sx - player_x) + abs(sy - player_y)
                    if distance < min_distance:
                        min_distance = distance
                        nearest = settlement
                
                if nearest:
                    if nearest.settlement_type == SettlementType.CITY:
                        nearest_settlement_info = f"the city of {nearest.name}" if nearest.name else "a city"
                    elif nearest.vassal_to is None:
                        nearest_settlement_info = f"the free town of {nearest.name}" if nearest.name else "a free town"
                    else:
                        nearest_settlement_info = f"the town of {nearest.name}" if nearest.name else "a town"
        
        # Convert tileset paths to relative if they're absolute
        saved_tileset_info = None
        if tileset_info:
            saved_tileset_info = tileset_info.copy()
            game_dir = os.getcwd()
            
            # Convert PNG path to relative
            if 'path' in saved_tileset_info and saved_tileset_info['path']:
                tileset_path = saved_tileset_info['path']
                if os.path.isabs(tileset_path):
                    try:
                        # Try to make it relative
                        saved_tileset_info['path'] = os.path.relpath(tileset_path, game_dir)
                    except ValueError:
                        # If that fails (different drives on Windows), keep original
                        print(f"Warning: Could not convert tileset path to relative: {tileset_path}")
            
            # Convert JSON path to relative
            if 'json_path' in saved_tileset_info and saved_tileset_info['json_path']:
                json_path = saved_tileset_info['json_path']
                if os.path.isabs(json_path):
                    try:
                        # Try to make it relative
                        saved_tileset_info['json_path'] = os.path.relpath(json_path, game_dir)
                    except ValueError:
                        # If that fails (different drives on Windows), keep original
                        print(f"Warning: Could not convert JSON path to relative: {json_path}")
        
        # Prepare save data
        save_data = {
            'map_filepath': relative_map_path,  # Store relative path
            'map_name': map_name,  # Store map name for display
            'nearest_settlement_info': nearest_settlement_info,  # Store nearest settlement info
            'player_x': player_x,
            'player_y': player_y,
            'calendar_year': calendar.year,
            'calendar_month': calendar.month,
            'calendar_day': calendar.day,
            'calendar_hour': calendar.hour,
            'command_messages': command_messages[-30:],  # Last 30 messages
            'explored_tiles': list(explored_tiles),  # Convert set to list for pickle
            'visible_tiles': list(visible_tiles),  # Convert set to list for pickle
            'settlement_economy': settlement_economy,  # Save economy state
            'tileset_info': saved_tileset_info,  # Save current tileset info (with relative path)
            'save_timestamp': datetime.now().isoformat(),
        }
        
        # Save to compressed file
        with gzip.open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"Game saved to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error saving game: {e}")
        return None


def load_game(filepath: str) -> Optional[Dict]:
    """
    Load a saved game state.
    
    Args:
        filepath: Path to the save file
        
    Returns:
        Dictionary with game state if successful, None otherwise
    """
    try:
        if not os.path.exists(filepath):
            print(f"Save file not found: {filepath}")
            return None
        
        # Load from compressed file
        with gzip.open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        # Convert map_filepath to absolute if it's relative (for loading)
        if 'map_filepath' in save_data:
            map_path = save_data['map_filepath']
            if not os.path.isabs(map_path):
                # It's relative, make it absolute based on current working directory
                game_dir = os.getcwd()
                save_data['map_filepath'] = os.path.join(game_dir, map_path)
            # If it's already absolute, keep it as is (for backward compatibility)
        
        # Convert tileset paths to absolute if they're relative (for loading)
        if 'tileset_info' in save_data and save_data['tileset_info']:
            tileset_info = save_data['tileset_info']
            game_dir = os.getcwd()
            
            # Convert PNG path to absolute
            if 'path' in tileset_info and tileset_info['path']:
                tileset_path = tileset_info['path']
                if not os.path.isabs(tileset_path):
                    # It's relative, make it absolute based on current working directory
                    tileset_info['path'] = os.path.join(game_dir, tileset_path)
            
            # Convert JSON path to absolute
            if 'json_path' in tileset_info and tileset_info['json_path']:
                json_path = tileset_info['json_path']
                if not os.path.isabs(json_path):
                    # It's relative, make it absolute based on current working directory
                    tileset_info['json_path'] = os.path.join(game_dir, json_path)
        
        # Convert lists back to sets
        if 'explored_tiles' in save_data:
            save_data['explored_tiles'] = set(save_data['explored_tiles'])
        if 'visible_tiles' in save_data:
            save_data['visible_tiles'] = set(save_data['visible_tiles'])
        
        return save_data
        
    except Exception as e:
        print(f"Error loading game: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_saved_games(directory: str = "saves") -> List[Tuple[str, Dict]]:
    """
    Get list of saved games with metadata.
    
    Args:
        directory: Directory to search for save files
        
    Returns:
        List of tuples (filepath, save_data) sorted by save timestamp (newest first)
    """
    if not os.path.exists(directory):
        print(f"Debug: Saves directory '{directory}' does not exist")
        return []
    
    saved_games = []
    try:
        files = os.listdir(directory)
        print(f"Debug: Found {len(files)} files in saves directory")
    except Exception as e:
        print(f"Error listing saves directory: {e}")
        return []
    
    for filename in files:
        if filename.endswith('.banshee') and filename.startswith('save_'):
            filepath = os.path.join(directory, filename)
            try:
                # Load save data to get metadata
                # Use a simplified load that doesn't convert paths for metadata display
                with gzip.open(filepath, 'rb') as f:
                    save_data = pickle.load(f)
                
                # Convert lists back to sets (but we don't need them for display)
                if 'explored_tiles' in save_data and isinstance(save_data['explored_tiles'], list):
                    save_data['explored_tiles'] = set(save_data['explored_tiles'])
                if 'visible_tiles' in save_data and isinstance(save_data['visible_tiles'], list):
                    save_data['visible_tiles'] = set(save_data['visible_tiles'])
                
                if save_data:
                    saved_games.append((filepath, save_data))
                    print(f"Debug: Loaded save file {filename}")
            except Exception as e:
                print(f"Error reading save file {filename}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Sort by save timestamp (newest first)
    saved_games.sort(key=lambda x: x[1].get('save_timestamp', ''), reverse=True)
    print(f"Debug: Returning {len(saved_games)} saved games")
    return saved_games

