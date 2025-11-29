"""
Trading caravan system.
Caravans travel from villages to towns and back.
"""
from typing import Tuple, Optional
from settlements import Settlement


class CaravanState:
    """States a caravan can be in."""
    AT_VILLAGE = "at_village"
    TRAVELING_TO_TOWN = "traveling_to_town"
    AT_TOWN = "at_town"
    TRAVELING_TO_VILLAGE = "traveling_to_village"


class Caravan:
    """Represents a trading caravan."""
    
    def __init__(self, village: Settlement, town: Settlement, 
                 start_x: int, start_y: int):
        """
        Initialize a caravan.
        
        Args:
            village: The village this caravan belongs to
            town: The town this caravan is traveling to
            start_x: Starting X position (village position)
            start_y: Starting Y position (village position)
        """
        self.village = village
        self.town = town
        self.x = float(start_x)  # Current position (float for smooth movement)
        self.y = float(start_y)
        self.state = CaravanState.AT_VILLAGE
        
        # Path from village to town
        self.path_to_town = []
        self.path_index_to_town = 0
        
        # Path from town to village
        self.path_to_village = []
        self.path_index_to_village = 0
        
        # Movement state
        self.target_x = float(start_x)
        self.target_y = float(start_y)
        self.movement_progress = 0.0  # 0.0 to 1.0
        
        # Time tracking
        self.arrived_at_town_time = None  # Will be set when arriving at town
        self.arrived_at_village_time = None  # Will be set when arriving at village
    
        # Movement tracking for slow terrain (hills, forests)
        self.pending_move_count = 0  # Count of moves needed for current tile
        self.pending_direction = None  # Direction we're trying to move
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position as float coordinates."""
        return (self.x, self.y)
    
    def get_tile_position(self) -> Tuple[int, int]:
        """Get current position as integer tile coordinates."""
        return (int(self.x), int(self.y))
    
    def set_path_to_town(self, path: list):
        """Set the path from village to town."""
        self.path_to_town = path
        self.path_index_to_town = 0
    
    def set_path_to_village(self, path: list):
        """Set the path from town to village."""
        self.path_to_village = path
        self.path_index_to_village = 0
    
    def start_journey_to_town(self):
        """Start the journey from village to town."""
        if not self.path_to_town:
            return False
        
        self.state = CaravanState.TRAVELING_TO_TOWN
        self.path_index_to_town = 0
        if self.path_index_to_town < len(self.path_to_town):
            self.target_x, self.target_y = self.path_to_town[self.path_index_to_town]
            self.movement_progress = 0.0
        return True
    
    def start_journey_to_village(self):
        """Start the journey from town to village."""
        if not self.path_to_village:
            return False
        
        self.state = CaravanState.TRAVELING_TO_VILLAGE
        self.path_index_to_village = 0
        if self.path_index_to_village < len(self.path_to_village):
            self.target_x, self.target_y = self.path_to_village[self.path_index_to_village]
            self.movement_progress = 0.0
        return True

