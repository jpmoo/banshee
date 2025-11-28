"""
Terrain types for the RPG map system.
Each terrain type has properties for movement and visibility.
"""
from enum import Enum
from typing import Tuple


class TerrainType(Enum):
    """Terrain types with their properties."""
    GRASSLAND = "grassland"
    HILLS = "hills"
    FORESTED_HILL = "forested_hill"
    MOUNTAIN = "mountain"
    FOREST = "forest"
    RIVER = "river"
    SHALLOW_WATER = "shallow_water"
    DEEP_WATER = "deep_water"


class Terrain:
    """Represents a single terrain tile with its properties."""
    
    # Terrain properties: (allows_movement, allows_view)
    TERRAIN_PROPERTIES = {
        TerrainType.GRASSLAND: (True, True),
        TerrainType.HILLS: (True, True),
        TerrainType.FORESTED_HILL: (True, False),  # Like forest, allows movement but blocks view
        TerrainType.MOUNTAIN: (False, False),
        TerrainType.FOREST: (True, False),
        TerrainType.RIVER: (False, True),  # Rivers block movement but allow view
        TerrainType.SHALLOW_WATER: (False, True),
        TerrainType.DEEP_WATER: (False, True),
    }
    
    # Color mapping for visualization (RGB tuples)
    # Softer, more distinct colors for better visual separation
    TERRAIN_COLORS = {
        TerrainType.GRASSLAND: (120, 180, 100),       # Softer yellow-green (more distinct from water)
        TerrainType.HILLS: (120, 100, 70),            # Softer brown
        TerrainType.FORESTED_HILL: (80, 100, 60),     # Brownish-green
        TerrainType.MOUNTAIN: (100, 100, 100),        # Softer gray
        TerrainType.FOREST: (20, 80, 20),              # Softer dark green
        TerrainType.RIVER: (70, 130, 180),            # Steel blue for rivers (distinct from coastal water)
        TerrainType.SHALLOW_WATER: (70, 140, 180),  # Darker cyan-blue
        TerrainType.DEEP_WATER: (20, 60, 120),        # Softer dark blue
    }
    
    def __init__(self, terrain_type: TerrainType):
        self.terrain_type = terrain_type
        self.allows_movement, self.allows_view = self.TERRAIN_PROPERTIES[terrain_type]
        self.color = self.TERRAIN_COLORS[terrain_type]
    
    def can_move_through(self) -> bool:
        """Returns True if units can move through this terrain."""
        return self.allows_movement
    
    def can_see_through(self) -> bool:
        """Returns True if vision can pass through this terrain."""
        return self.allows_view
    
    def get_color(self) -> Tuple[int, int, int]:
        """Returns the RGB color for this terrain."""
        return self.color

