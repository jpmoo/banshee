"""
Play screen for the RPG game.
Displays the game world with player movement and status.
"""
import pygame
import random
import math
from typing import List, Optional, Tuple, Dict
from terrain import Terrain, TerrainType
from settlements import Settlement, SettlementType
from map_renderer import MapRenderer
from celtic_calendar import CelticCalendar
from save_game import save_game
from caravan import Caravan, CaravanState
from tileset_selection_screen import TilesetSelectionScreen


class PlayScreen:
    """Main play screen with 3x3 grid layout."""
    
    def __init__(self, screen: pygame.Surface, map_data: List[List[Terrain]], 
                 map_width: int, map_height: int, settlements: List[Settlement],
                 tile_size: int = 32, map_filepath: Optional[str] = None,
                 saved_state: Optional[Dict] = None, worldbuilding_data: Optional[Dict] = None):
        """
        Initialize the play screen.
        
        Args:
            screen: Pygame surface to draw on
            map_data: 2D list of terrain data
            map_width: Map width in tiles
            map_height: Map height in tiles
            settlements: List of all settlements on the map
            tile_size: Size of each tile in pixels
        """
        self.screen = screen
        self.map_data = map_data
        self.map_width = map_width
        self.map_height = map_height
        self.settlements = settlements
        self.tile_size = tile_size
        self.map_filepath = map_filepath  # Store map filepath for saving
        
        # Calculate grid layout (3x3)
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Top left 2x2: Map view
        self.map_view_width = (screen_width * 2) // 3
        self.map_view_height = (screen_height * 2) // 3
        
        # Right 1x2: Status messages
        self.status_width = screen_width - self.map_view_width
        self.status_height = self.map_view_height
        
        # Bottom 1x3: Command/Results area
        self.command_width = screen_width
        self.command_height = screen_height - self.map_view_height
        
        # Player position (in tiles)
        self.player_x = 0
        self.player_y = 0
        
        # Load from saved state if provided
        if saved_state:
            self.player_x = saved_state.get('player_x', 0)
            self.player_y = saved_state.get('player_y', 0)
            # Restore calendar
            calendar_year = saved_state.get('calendar_year', 1)
            calendar_month = saved_state.get('calendar_month', 1)
            calendar_day = saved_state.get('calendar_day', 1)
            calendar_hour = saved_state.get('calendar_hour', 6)
            # Restore command messages
            self.command_messages = saved_state.get('command_messages', [])
            # Restore explored/visible tiles
            self.explored_tiles = saved_state.get('explored_tiles', set())
            self.visible_tiles = saved_state.get('visible_tiles', set())
            
            # Store tileset info to restore after map_renderer is initialized
            self._saved_tileset_info = saved_state.get('tileset_info')
            
            # Restore settlement economy state
            settlement_economy = saved_state.get('settlement_economy', {})
            if settlement_economy:
                for settlement in settlements:
                    settlement_key = (settlement.x, settlement.y, settlement.settlement_type.value)
                    if settlement_key in settlement_economy:
                        economy_data = settlement_economy[settlement_key]
                        
                        # Restore resources (for towns)
                        if 'resources' in economy_data and settlement.settlement_type == SettlementType.TOWN:
                            if hasattr(settlement, 'resources') and settlement.resources is not None:
                                settlement.resources.update(economy_data['resources'])
                        
                        # Restore trade goods (for towns and cities)
                        if 'trade_goods' in economy_data:
                            if settlement.settlement_type in [SettlementType.TOWN, SettlementType.CITY]:
                                if hasattr(settlement, 'trade_goods'):
                                    settlement.trade_goods = economy_data['trade_goods']
                        
                        # Restore money (for towns and cities)
                        if 'money' in economy_data:
                            if settlement.settlement_type in [SettlementType.TOWN, SettlementType.CITY]:
                                if hasattr(settlement, 'money'):
                                    settlement.money = economy_data['money']
            
            print(f"Loaded saved game: player at ({self.player_x}, {self.player_y})")
        else:
            # Place player in a random ore village with clear path to its town
            villages = [s for s in settlements if s.settlement_type == SettlementType.VILLAGE]
            ore_villages = [v for v in villages if v.supplies_resource == "ore"]
            
            if ore_villages:
                # Shuffle to randomize selection
                random.shuffle(ore_villages)
                start_village = None
                
                # Find an ore village with a clear path to its town
                for village in ore_villages:
                    if village.vassal_to:  # Make sure it has a town
                        town = village.vassal_to
                        village_x, village_y = village.get_position()
                        town_x, town_y = town.get_position()
                        
                        # Check if there's a straight path with no blocked terrain
                        if self._has_clear_path(village_x, village_y, town_x, town_y):
                            start_village = village
                            break
                
                if start_village:
                    self.player_x, self.player_y = start_village.get_position()
                    print(f"Player starting at ore village: {start_village.name} at ({self.player_x}, {self.player_y})")
                elif ore_villages:
                    # Fallback: use first ore village even if path is blocked
                    start_village = ore_villages[0]
                    self.player_x, self.player_y = start_village.get_position()
                    print(f"Player starting at ore village: {start_village.name} at ({self.player_x}, {self.player_y}) (path check failed)")
                elif villages:
                    # Fallback: use any village
                    start_village = random.choice(villages)
                    self.player_x, self.player_y = start_village.get_position()
                    print(f"Player starting at village: {start_village.name} at ({self.player_x}, {self.player_y})")
                else:
                    # Fallback: start at center of map
                    self.player_x = map_width // 2
                    self.player_y = map_height // 2
                    print(f"No villages found, starting player at map center ({self.player_x}, {self.player_y})")
            elif villages:
                # Fallback: use any village if no ore villages
                start_village = random.choice(villages)
                self.player_x, self.player_y = start_village.get_position()
                print(f"Player starting at village: {start_village.name} at ({self.player_x}, {self.player_y})")
            else:
                # Fallback: start at center of map
                self.player_x = map_width // 2
                self.player_y = map_height // 2
                print(f"No villages found, starting player at map center ({self.player_x}, {self.player_y})")
        
        # Movement state (must be initialized before _update_camera)
        self.moving_direction = None  # 'north', 'south', 'east', 'west'
        
        # Movement animation state (must be initialized before _update_camera)
        self.is_moving = False
        self.move_start_x = 0.0  # Starting position for animation (in tiles, float)
        self.move_start_y = 0.0
        self.move_target_x = 0.0  # Target position for animation (in tiles, float)
        self.move_target_y = 0.0
        self.move_progress = 0.0  # 0.0 to 1.0
        self.move_duration = 0.0  # Duration in seconds
        self.move_elapsed = 0.0  # Elapsed time in seconds
        self.pending_terrain = None  # Terrain at destination (set when movement starts)
        self.pending_new_x = 0
        self.pending_new_y = 0
        self.pending_direction = None  # For forest/hills: track pending movement direction
        self.pending_move_count = 0  # Count of key presses for slow terrain (need 2)
        
        # Camera position (centered on player) - now safe to call after movement state is initialized
        self._update_camera()
        
        # Status messages (scrollable list)
        self.status_messages = []
        self.max_status_messages = 20
        
        # Command/Results area (scrollable list) - terminal style
        self.command_messages = []
        self.max_command_messages = 50  # More messages for terminal feel
        
        # Prompt state
        self.pending_prompt = None  # 'save_or_load', 'quit_save', etc.
        self.prompt_response = None
        
        # Renderer for map
        # Map renderer (start with color-based, can be switched)
        self.renderer = MapRenderer(tile_size=tile_size, use_tileset=False)
        self.map_renderer = self.renderer  # Alias for compatibility
        
        # Restore tileset info if loading from save
        if saved_state and hasattr(self, '_saved_tileset_info'):
            tileset_info = self._saved_tileset_info
            if tileset_info:
                self.map_renderer.switch_tileset(tileset_info)
                self.current_tileset_info = tileset_info
                print(f"Loaded tileset: {tileset_info.get('name', 'Unknown')}")
            else:
                # Legacy save - use color-based rendering
                self.map_renderer.switch_tileset({'type': 'color', 'name': 'Original Color-Based'})
                self.current_tileset_info = {'type': 'color', 'name': 'Original Color-Based'}
                print("Legacy save detected - using color-based rendering")
            # Clean up temporary attribute
            delattr(self, '_saved_tileset_info')
        else:
            # Initialize tileset info to color-based for new games
            self.current_tileset_info = {'type': 'color', 'name': 'Original Color-Based'}
        
        # Celtic calendar system
        if saved_state:
            self.calendar = CelticCalendar(
                year=saved_state.get('calendar_year', 1),
                month=saved_state.get('calendar_month', 1),
                day=saved_state.get('calendar_day', 1),
                hour=saved_state.get('calendar_hour', 6)
            )
        else:
            self.calendar = CelticCalendar(year=1, month=1, day=1, hour=6)  # Start at dawn
        
        # Fog of war system
        if not saved_state:
            self.explored_tiles = set()  # Set of (x, y) tuples for explored tiles
            self.visible_tiles = set()  # Set of (x, y) tuples for currently visible tiles
            # Mark starting position as explored and visible
            self.explored_tiles.add((self.player_x, self.player_y))
            self._update_visibility()
        
        # Map view mode
        self.map_view_mode = False
        self.map_view_tile_size = 4  # Smaller tiles for zoomed-out view
        self.map_view_camera_x = 0
        self.map_view_camera_y = 0
        
        # Trading caravans
        self.caravans: List[Caravan] = []
        self.last_caravan_check_day = self.calendar.day
        self.last_caravan_check_hour = self.calendar.hour
        
        # Current settlement (settlement player is standing on)
        self.current_settlement: Optional[Settlement] = None
        self._check_settlement_at_position()
        
        # Worldbuilding data
        self.worldbuilding_data = worldbuilding_data
        
        # Status area scrolling
        self.status_scroll_offset = 0
        self.status_scroll_speed = 20
        
        # Tileset selection screen
        self.showing_tileset_selection = False
        self.tileset_selection_screen: Optional[TilesetSelectionScreen] = None
        # Current tileset info (for saving/loading)
        self.current_tileset_info: Optional[Dict] = None
        
    def _update_camera(self):
        """Update camera position to center on player."""
        # Calculate viewport size in tiles
        viewport_width = self.map_view_width // self.tile_size
        viewport_height = self.map_view_height // self.tile_size
        
        # Center camera on player
        self.camera_x = self.player_x - viewport_width // 2
        self.camera_y = self.player_y - viewport_height // 2
        
        # Clamp camera to map bounds
        self.camera_x = max(0, min(self.map_width - viewport_width, self.camera_x))
        self.camera_y = max(0, min(self.map_height - viewport_height, self.camera_y))
    
    def _clamp_map_view_camera(self):
        """Clamp map view camera to map bounds."""
        viewport_width = self.map_view_width // self.map_view_tile_size
        viewport_height = self.map_view_height // self.map_view_tile_size
        
        self.map_view_camera_x = max(0, min(self.map_width - viewport_width, self.map_view_camera_x))
        self.map_view_camera_y = max(0, min(self.map_height - viewport_height, self.map_view_camera_y))
    
    def _render_map_view(self):
        """Render the zoomed-out map view showing only explored areas."""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Draw map view (top left 2x2)
        map_surface = pygame.Surface((self.map_view_width, self.map_view_height))
        map_surface.fill((0, 0, 0))  # Black background
        
        # Calculate visible tile range
        tiles_visible_y = (self.map_view_height // self.map_view_tile_size) + 2
        tiles_visible_x = (self.map_view_width // self.map_view_tile_size) + 2
        
        start_y = max(0, self.map_view_camera_y)
        end_y = min(self.map_height, self.map_view_camera_y + tiles_visible_y)
        start_x = max(0, self.map_view_camera_x)
        end_x = min(self.map_width, self.map_view_camera_x + tiles_visible_x)
        
        # Draw all explored tiles (no distance limit in zoomed-out map view)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Only show explored tiles
                if (x, y) not in self.explored_tiles:
                    continue
                
                terrain = self.map_data[y][x]
                color = terrain.get_color()
                
                # Calculate screen position
                screen_x = (x - self.map_view_camera_x) * self.map_view_tile_size
                screen_y = (y - self.map_view_camera_y) * self.map_view_tile_size
                
                # Draw tile
                rect = pygame.Rect(screen_x, screen_y, self.map_view_tile_size, self.map_view_tile_size)
                pygame.draw.rect(map_surface, color, rect)
        
        # Draw settlements (only if explored)
        for settlement in self.settlements:
            x, y = settlement.get_position()
            
            # Only draw if explored
            if (x, y) not in self.explored_tiles:
                continue
            
            if not (start_x <= x < end_x and start_y <= y < end_y):
                continue
            
            screen_x = (x - self.map_view_camera_x) * self.map_view_tile_size
            screen_y = (y - self.map_view_camera_y) * self.map_view_tile_size
            center_x = screen_x + self.map_view_tile_size // 2
            center_y = screen_y + self.map_view_tile_size // 2
            
            if settlement.settlement_type == SettlementType.CITY:
                # Cities: Very large and visible (star/pentagon shape)
                size = max(8, self.map_view_tile_size)
                # Draw star/pentagon
                points = []
                for i in range(5):
                    angle = (i * 2 * 3.14159 / 5) - 3.14159 / 2
                    outer_x = center_x + int(size * 0.8 * math.cos(angle))
                    outer_y = center_y + int(size * 0.8 * math.sin(angle))
                    points.append((outer_x, outer_y))
                pygame.draw.polygon(map_surface, (255, 215, 0), points)  # Gold
                pygame.draw.polygon(map_surface, (255, 255, 255), points, 2)  # White border
            elif settlement.settlement_type == SettlementType.TOWN:
                # Towns: Large and visible
                size = max(6, self.map_view_tile_size - 2)
                town_rect = pygame.Rect(
                    center_x - size // 2,
                    center_y - size // 2,
                    size,
                    size
                )
                pygame.draw.rect(map_surface, (255, 255, 0), town_rect)  # Bright yellow
                pygame.draw.rect(map_surface, (255, 255, 255), town_rect, 2)  # White border
        
        # Draw player position
        if (self.player_x, self.player_y) in self.explored_tiles:
            player_screen_x = (self.player_x - self.map_view_camera_x) * self.map_view_tile_size
            player_screen_y = (self.player_y - self.map_view_camera_y) * self.map_view_tile_size
            if 0 <= player_screen_x < self.map_view_width and 0 <= player_screen_y < self.map_view_height:
                pygame.draw.circle(map_surface, (255, 0, 0), 
                                 (player_screen_x + self.map_view_tile_size // 2, 
                                  player_screen_y + self.map_view_tile_size // 2),
                                 max(3, self.map_view_tile_size // 2))
                pygame.draw.circle(map_surface, (255, 255, 255),
                                 (player_screen_x + self.map_view_tile_size // 2,
                                  player_screen_y + self.map_view_tile_size // 2),
                                 max(3, self.map_view_tile_size // 2), 1)
        
        self.screen.blit(map_surface, (0, 0))
        
        # Draw status area (right 1x2) - show map view instructions
        status_rect = pygame.Rect(self.map_view_width, 0, self.status_width, self.status_height)
        pygame.draw.rect(self.screen, (20, 20, 30), status_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), status_rect, 2)
        
        font = pygame.font.Font(None, 24)
        title_font = pygame.font.Font(None, 28)
        
        title_text = title_font.render("Map View", True, (255, 255, 255))
        self.screen.blit(title_text, (self.map_view_width + 10, 10))
        
        instructions = [
            "WASD/Arrow Keys: Scroll",
            "M: Return to game",
            "",
            "Only explored areas",
            "are shown."
        ]
        y_offset = 50
        for instruction in instructions:
            text_surface = font.render(instruction, True, (200, 200, 200))
            self.screen.blit(text_surface, (self.map_view_width + 10, y_offset))
            y_offset += 25
    
    def move_player(self, direction: str):
        """
        Move the player in the specified direction.
        Grassland: instant movement (1 tap)
        Forest/Hills: requires 2 taps to move one tile
        
        Args:
            direction: 'north', 'south', 'east', or 'west'
        """
        # Don't allow new movement if already moving
        if self.is_moving:
            return
        
        # Calculate new position
        new_x = self.player_x
        new_y = self.player_y
        
        if direction == 'north':
            new_y = max(0, self.player_y - 1)
        elif direction == 'south':
            new_y = min(self.map_height - 1, self.player_y + 1)
        elif direction == 'east':
            new_x = min(self.map_width - 1, self.player_x + 1)
        elif direction == 'west':
            new_x = max(0, self.player_x - 1)
        
        # Check if movement is valid (not into impassable terrain)
        if 0 <= new_x < self.map_width and 0 <= new_y < self.map_height:
            terrain = self.map_data[new_y][new_x]
            # Check if terrain allows movement using the terrain's method
            if terrain.can_move_through():
                # Check if this is slow terrain (forest or hills)
                is_slow_terrain = terrain.terrain_type in [TerrainType.FOREST, TerrainType.HILLS, TerrainType.FORESTED_HILL]
                
                if is_slow_terrain:
                    # For slow terrain, require 2 key presses
                    if self.pending_direction == direction:
                        # Second press - complete the movement
                        self.pending_move_count += 1
                        if self.pending_move_count >= 2:
                            # Complete movement
                            self._execute_movement(new_x, new_y, terrain)
                            # Reset pending state
                            self.pending_direction = None
                            self.pending_move_count = 0
                        else:
                            # Still need more presses - show slowed message
                            terrain_name = terrain.terrain_type.value.replace('_', ' ').title()
                            self.add_command_message(f"Slowed - {terrain_name}")
                    else:
                        # First press in this direction - start pending movement
                        self.pending_direction = direction
                        self.pending_move_count = 1
                        terrain_name = terrain.terrain_type.value.replace('_', ' ').title()
                        self.add_command_message(f"Slowed - {terrain_name}")
                else:
                    # Grassland or other fast terrain - instant movement (no message)
                    self._execute_movement(new_x, new_y, terrain)
                    # Clear any pending movement
                    self.pending_direction = None
                    self.pending_move_count = 0
            else:
                # Impassable terrain
                terrain_name = terrain.terrain_type.value.replace('_', ' ').title()
                self.add_command_message(f"Impassable - {terrain_name}")
                # Clear pending movement if blocked
                self.pending_direction = None
                self.pending_move_count = 0
        else:
            # Out of bounds
            self.add_command_message("Impassable - Out of bounds")
            # Clear pending movement if blocked
            self.pending_direction = None
            self.pending_move_count = 0
    
    def _execute_movement(self, new_x: int, new_y: int, terrain: Terrain):
        """
        Execute the actual movement to the new position.
        
        Args:
            new_x: Target X coordinate
            new_y: Target Y coordinate
            terrain: Terrain at destination
        """
        direction_names = {
            'north': 'north',
            'south': 'south',
            'east': 'east',
            'west': 'west'
        }
        
        # Determine direction for message
        if new_y < self.player_y:
            direction = 'north'
        elif new_y > self.player_y:
            direction = 'south'
        elif new_x > self.player_x:
            direction = 'east'
        elif new_x < self.player_x:
            direction = 'west'
        else:
            direction = None
        
        # Update player position
        self.player_x = new_x
        self.player_y = new_y
        self._update_camera()
        
        # Mark new position as explored
        self.explored_tiles.add((self.player_x, self.player_y))
        
        # Update visibility after movement
        self._update_visibility()
        
        # Check if player landed on a settlement
        self._check_settlement_at_position()
        
        # Calculate time cost based on terrain type
        hours = self._get_movement_time(terrain.terrain_type)
        self.calendar.add_hours(hours)
        
        # Update caravans when player moves (time passes)
        self._update_caravans_on_move()
        
        # No "Moved" message - only show messages for issues
    
    def update_movement(self, dt: float):
        """
        Update movement animation (no longer used, but kept for compatibility).
        
        Args:
            dt: Delta time in seconds since last frame
        """
        # Movement is now instant for grassland, and requires 2 taps for forest/hills
        # No animation needed
        pass
    
    def get_player_render_position(self) -> Tuple[float, float]:
        """
        Get the current player position for rendering.
        
        Returns:
            (x, y) position in tiles as floats
        """
        # Movement is now instant, so just return the current position
        return (float(self.player_x), float(self.player_y))
    
    def _get_movement_time(self, terrain_type: TerrainType) -> int:
        """
        Get the number of hours it takes to move one tile on this terrain.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            Number of hours required to move one tile
        """
        # Movement time per tile based on terrain
        movement_times = {
            TerrainType.GRASSLAND: 2,
            TerrainType.FOREST: 4,
            TerrainType.HILLS: 4,
            TerrainType.FORESTED_HILL: 4,  # Same as forest
            TerrainType.MOUNTAIN: 8,  # Mountains are slower (though usually impassable)
            TerrainType.RIVER: 2,  # Assuming shallow crossing
            TerrainType.SHALLOW_WATER: 3,  # Slower than grassland
            TerrainType.DEEP_WATER: 0,  # Usually impassable, but if passable, very slow
        }
        
        return movement_times.get(terrain_type, 2)  # Default to 2 hours
    
    def _update_visibility(self):
        """Update visible tiles based on line-of-sight from player position."""
        self.visible_tiles.clear()
        
        # Calculate viewport size in tiles
        # Viewport shows tiles: map_view_width / tile_size by map_view_height / tile_size
        viewport_width_tiles = self.map_view_width // self.tile_size
        viewport_height_tiles = self.map_view_height // self.tile_size
        
        # Calculate the rectangular bounds of the viewport centered on the player
        # Half-width and half-height from center
        half_width = viewport_width_tiles // 2
        half_height = viewport_height_tiles // 2
        
        # Check all tiles within the rectangular viewport bounds
        for dy in range(-half_height, half_height + 1):
            for dx in range(-half_width, half_width + 1):
                target_x = self.player_x + dx
                target_y = self.player_y + dy
                
                # Check bounds
                if target_x < 0 or target_x >= self.map_width or target_y < 0 or target_y >= self.map_height:
                    continue
                
                # Check line of sight
                if self._has_line_of_sight(self.player_x, self.player_y, target_x, target_y):
                    self.visible_tiles.add((target_x, target_y))
                    # Mark as explored when visible (only mark tiles within viewport as explored)
                    self.explored_tiles.add((target_x, target_y))
    
    def _get_terrain_elevation(self, terrain_type: TerrainType) -> int:
        """
        Get the elevation level for a terrain type.
        Higher numbers = higher elevation.
        
        Args:
            terrain_type: The terrain type
            
        Returns:
            Elevation level (0-10)
        """
        elevation_map = {
            TerrainType.DEEP_WATER: 0,
            TerrainType.SHALLOW_WATER: 1,
            TerrainType.RIVER: 1,
            TerrainType.GRASSLAND: 2,
            TerrainType.FOREST: 3,  # Same elevation as grassland but blocks view
            TerrainType.HILLS: 5,
            TerrainType.FORESTED_HILL: 5,  # Same elevation as hills but blocks view like forest
            TerrainType.MOUNTAIN: 8,
        }
        return elevation_map.get(terrain_type, 2)  # Default to grassland elevation
    
    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        Check if there's line of sight between two points.
        Uses Bresenham's line algorithm to check each tile along the path.
        
        Rules:
        - Forested hills block view like forests
        - When viewing from higher elevation to lower elevation, you can see everything
          at lower elevation with no blocking (except for blocking at your own elevation, like forests)
        - Mountains and forests block view (but you can see the first tile)
        
        Args:
            x1, y1: Starting position
            x2, y2: Target position
            
        Returns:
            True if line of sight exists
        """
        # If same tile, always visible
        if x1 == x2 and y1 == y2:
            return True
        
        # Get starting elevation
        start_elevation = 2  # Default
        if 0 <= y1 < self.map_height and 0 <= x1 < self.map_width:
            start_terrain = self.map_data[y1][x1].terrain_type
            start_elevation = self._get_terrain_elevation(start_terrain)
        
        # Get target elevation
        target_elevation = 2  # Default
        if 0 <= y2 < self.map_height and 0 <= x2 < self.map_width:
            target_terrain = self.map_data[y2][x2].terrain_type
            target_elevation = self._get_terrain_elevation(target_terrain)
        
        # Use Bresenham's line algorithm to check each tile
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        first_tile = True
        
        while True:
            # Check current tile
            if 0 <= y < self.map_height and 0 <= x < self.map_width:
                terrain = self.map_data[y][x].terrain_type
                tile_elevation = self._get_terrain_elevation(terrain)
                
                # If this is the target tile, we can see it (first tile rule)
                if x == x2 and y == y2:
                    return True
                
                # If not the first tile, check blocking
                if not first_tile:
                    # Check if this blocking terrain is at lower elevation than starting position
                    # If so, it cannot block view (you can see over lower terrain)
                    if start_elevation > tile_elevation:
                        # We're looking down - lower elevation terrain cannot block our view
                        # Only terrain at our elevation or higher can block
                        # Mountains always block view (they're higher elevation)
                        if terrain == TerrainType.MOUNTAIN:
                            return False
                        # Forests, forested hills, and regular hills at lower elevation don't block
                        # Continue to next tile without blocking
                    elif start_elevation == tile_elevation:
                        # Same elevation - check for blocking terrain
                        # Mountains always block view
                        if terrain == TerrainType.MOUNTAIN:
                            return False
                        
                        # Forests block view at same elevation
                        if terrain == TerrainType.FOREST:
                            return False
                        
                        # Forested hills block view like forests at same elevation
                        if terrain == TerrainType.FORESTED_HILL:
                            return False
                        
                        # Hills block view if we're not on a hill
                        if terrain == TerrainType.HILLS:
                            if start_elevation < 5:  # Not on a hill
                                return False
                    else:
                        # Looking up (start_elevation < tile_elevation) - use normal blocking rules
                        # Mountains always block view
                        if terrain == TerrainType.MOUNTAIN:
                            return False
                        
                        # Forests block view
                        if terrain == TerrainType.FOREST:
                            return False
                        
                        # Forested hills block view like forests
                        if terrain == TerrainType.FORESTED_HILL:
                            return False
                        
                        # Hills block view if we're not on a hill
                        if terrain == TerrainType.HILLS:
                            if start_elevation < 5:  # Not on a hill
                                return False
                
                first_tile = False
            
            # Move to next tile
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return True
    
    def _get_path(self, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int]]:
        """
        Get a path between two points using A* pathfinding.
        Falls back to straight line if A* fails.
        
        Args:
            x1, y1: Starting position
            x2, y2: Target position
            
        Returns:
            List of (x, y) tuples representing the path (excluding start, including end)
        """
        # Try A* pathfinding first
        path = self._astar_path(x1, y1, x2, y2)
        if path:
            return path
        
        # Fallback to straight line if A* fails
        path = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        # First, move to next tile
        while True:
            # If we've reached the target, we're done
            if x == x2 and y == y2:
                break
            
            # Move to next tile
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            
            # Add this tile to path
            path.append((x, y))
        
        return path
    
    def _astar_path(self, x1: int, y1: int, x2: int, y2: int) -> Optional[List[Tuple[int, int]]]:
        """
        A* pathfinding algorithm to find a path around obstacles.
        
        Args:
            x1, y1: Starting position
            x2, y2: Target position
            
        Returns:
            List of (x, y) tuples representing the path (excluding start, including end), or None if no path found
        """
        from heapq import heappush, heappop
        
        # Heuristic function (Manhattan distance)
        def heuristic(x, y):
            return abs(x - x2) + abs(y - y2)
        
        # Check if a position is valid and passable
        def is_valid(x, y):
            if not (0 <= x < self.map_width and 0 <= y < self.map_height):
                return False
            terrain = self.map_data[y][x]
            # Explicitly prevent movement through water, rivers, and mountains
            if terrain.terrain_type in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, 
                                       TerrainType.RIVER, TerrainType.MOUNTAIN]:
                return False
            return terrain.can_move_through()
        
        # A* algorithm
        open_set = [(0, x1, y1)]  # (f_score, x, y)
        came_from = {}
        g_score = {(x1, y1): 0}
        f_score = {(x1, y1): heuristic(x1, y1)}
        visited = set()
        
        # 8-directional movement (including diagonals)
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        while open_set:
            current_f, current_x, current_y = heappop(open_set)
            
            if (current_x, current_y) in visited:
                continue
            
            visited.add((current_x, current_y))
            
            # Check if we've reached the goal
            if current_x == x2 and current_y == y2:
                # Reconstruct path
                path = []
                current = (current_x, current_y)
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            # Check all neighbors
            for dx, dy in directions:
                neighbor_x = current_x + dx
                neighbor_y = current_y + dy
                neighbor = (neighbor_x, neighbor_y)
                
                if not is_valid(neighbor_x, neighbor_y):
                    continue
                
                # Cost is 1 for cardinal, sqrt(2) for diagonal
                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                tentative_g = g_score.get((current_x, current_y), float('inf')) + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = (current_x, current_y)
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor_x, neighbor_y)
                    heappush(open_set, (f_score[neighbor], neighbor_x, neighbor_y))
        
        # No path found
        return None
    
    def _validate_path(self, path: List[Tuple[int, int]]) -> Optional[List[Tuple[int, int]]]:
        """
        Validate a path to ensure it doesn't contain water, rivers, or mountains.
        
        Args:
            path: List of (x, y) tuples representing the path
            
        Returns:
            Validated path if all tiles are passable, None otherwise
        """
        if not path:
            return None
        
        validated_path = []
        for x, y in path:
            if not (0 <= x < self.map_width and 0 <= y < self.map_height):
                return None  # Out of bounds
            terrain = self.map_data[y][x]
            # Explicitly block water, rivers, and mountains
            if terrain.terrain_type in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, 
                                       TerrainType.RIVER, TerrainType.MOUNTAIN]:
                return None  # Invalid path
            if not terrain.can_move_through():
                return None  # Impassable terrain
            validated_path.append((x, y))
        
        return validated_path
    
    def _has_clear_path(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        Check if there's a path between two points (using A* pathfinding).
        
        Args:
            x1, y1: Starting position
            x2, y2: Target position
            
        Returns:
            True if a valid path exists
        """
        path = self._astar_path(x1, y1, x2, y2)
        if path is None:
                    return False
        # Validate the path
        validated = self._validate_path(path)
        return validated is not None
    
    def _check_settlement_at_position(self):
        """Check if player is standing on a settlement and update current_settlement."""
        self.current_settlement = None
        for settlement in self.settlements:
            sx, sy = settlement.get_position()
            if sx == self.player_x and sy == self.player_y:
                self.current_settlement = settlement
                break
    
    def _find_settlement_worldbuilding_data(self, settlement: Settlement) -> Optional[Dict]:
        """
        Find worldbuilding data for a settlement.
        
        Args:
            settlement: The settlement to find data for
            
        Returns:
            Dictionary with description and leader info, or None if not found
        """
        if not self.worldbuilding_data:
            return None
        
        # Find the settlement in the worldbuilding structure
        # Structure: {"City 1": {..., "Vassal Town 1": {..., "Vassal Village 1": {...}}}}
        
        if settlement.settlement_type == SettlementType.CITY:
            # Find city by index
            cities = [s for s in self.settlements if s.settlement_type == SettlementType.CITY]
            try:
                city_index = cities.index(settlement) + 1
                city_key = f"City {city_index}"
                if city_key in self.worldbuilding_data:
                    return self.worldbuilding_data[city_key]
            except ValueError:
                pass
        
        elif settlement.settlement_type == SettlementType.TOWN:
            # Find town - could be under a city or under "City NONE FOR FREE TOWN"
            if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.CITY:
                # Town under a city
                cities = [s for s in self.settlements if s.settlement_type == SettlementType.CITY]
                try:
                    city_index = cities.index(settlement.vassal_to) + 1
                    city_key = f"City {city_index}"
                    if city_key in self.worldbuilding_data:
                        city_data = self.worldbuilding_data[city_key]
                        # Find town index within this city
                        vassal_towns = [t for t in self.settlements 
                                     if t.settlement_type == SettlementType.TOWN and t.vassal_to == settlement.vassal_to]
                        try:
                            town_index = vassal_towns.index(settlement) + 1
                            town_key = f"Vassal Town {town_index}"
                            if town_key in city_data:
                                return city_data[town_key]
                        except ValueError:
                            pass
                except ValueError:
                    pass
            else:
                # Free town - under "City NONE FOR FREE TOWN"
                free_town_key = "City NONE FOR FREE TOWN"
                if free_town_key in self.worldbuilding_data:
                    free_town_data = self.worldbuilding_data[free_town_key]
                    free_towns = [t for t in self.settlements 
                                if t.settlement_type == SettlementType.TOWN and t.vassal_to is None]
                    try:
                        town_index = free_towns.index(settlement) + 1
                        town_key = f"Vassal Town {town_index}"
                        if town_key in free_town_data:
                            return free_town_data[town_key]
                    except ValueError:
                        pass
        
        elif settlement.settlement_type == SettlementType.VILLAGE:
            # Find village - under a town
            if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.TOWN:
                town = settlement.vassal_to
                # Find the town's data first
                town_data = self._find_settlement_worldbuilding_data(town)
                if town_data:
                    # Find village index within this town
                    vassal_villages = town.vassal_villages if hasattr(town, 'vassal_villages') else []
                    try:
                        village_index = vassal_villages.index(settlement) + 1
                        village_key = f"Vassal Village {village_index}"
                        if village_key in town_data:
                            return town_data[village_key]
                    except (ValueError, AttributeError):
                        pass
        
        return None
    
    def add_status_message(self, message: str):
        """Add a status message to the status area."""
        self.status_messages.append(message)
        if len(self.status_messages) > self.max_status_messages:
            self.status_messages.pop(0)
    
    def add_command_message(self, message: str):
        """Add a command/result message to the command area."""
        self.command_messages.append(message)
        if len(self.command_messages) > self.max_command_messages:
            self.command_messages.pop(0)
    
    def _execute_command(self, command: str) -> Optional[str]:
        """
        Execute a terminal command.
        
        Args:
            command: The command string to execute (single character)
            
        Returns:
            Result message or None
        """
        command = command.lower().strip()
        
        # Movement commands (handled directly in handle_event, but kept for other keys)
        if command in ['n', 'north']:
            self.move_player('north')
            return None  # move_player already adds messages
        elif command in ['s', 'south']:
            self.move_player('south')
            return None
        elif command in ['e', 'east']:
            self.move_player('east')
            return None
        elif command in ['w', 'west']:
            self.move_player('west')
            return None
        
        # Map view command (handled directly in handle_event)
        elif command in ['m', 'map']:
            # This is handled in handle_event, but return message if needed
            return None
        
        # Help command
        elif command in ['?', 'h', 'help']:
            return "Commands: n/s/e/w (move), m (map), h/? (help)"
        
        # Unknown command
        else:
            return f"Unknown command: {command}. Type 'h' for help."
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        # Handle tileset selection screen first
        if self.showing_tileset_selection:
            result = self.tileset_selection_screen.handle_event(event)
            if result:
                if result.get('action') == 'select':
                    tileset_info = result.get('tileset')
                    self.map_renderer.switch_tileset(tileset_info)
                    self.add_command_message(f"Switched to: {tileset_info['name']}")
                    self.showing_tileset_selection = False
                    self.tileset_selection_screen = None
                    # Store current tileset info for saving
                    self.current_tileset_info = tileset_info
                    # Force a render to refresh the map
                    self.render()
                    pygame.display.flip()
                elif result.get('action') == 'cancel':
                    self.add_command_message("Tileset selection cancelled")
                    self.showing_tileset_selection = False
                    self.tileset_selection_screen = None
            return None
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            'quit' if should exit play screen, None otherwise
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                # Toggle map view
                self.map_view_mode = not self.map_view_mode
                if self.map_view_mode:
                    # Initialize map view camera to center on player
                    self.map_view_camera_x = self.player_x - (self.map_view_width // self.map_view_tile_size) // 2
                    self.map_view_camera_y = self.player_y - (self.map_view_height // self.map_view_tile_size) // 2
                    self._clamp_map_view_camera()
            elif self.map_view_mode:
                # Map view scrolling
                scroll_speed = 5  # tiles per keypress
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.map_view_camera_y = max(0, self.map_view_camera_y - scroll_speed)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.map_view_camera_y = min(self.map_height - (self.map_view_height // self.map_view_tile_size), 
                                                 self.map_view_camera_y + scroll_speed)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.map_view_camera_x = min(self.map_width - (self.map_view_width // self.map_view_tile_size),
                                                 self.map_view_camera_x + scroll_speed)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.map_view_camera_x = max(0, self.map_view_camera_x - scroll_speed)
            else:
                # Execute commands immediately on keypress (terminal style)
                command_executed = False
                
                # Check for prompt responses FIRST (before movement commands)
                if self.pending_prompt:
                    # Handle prompt responses
                    if self.pending_prompt == 'save_or_load':
                        if event.key == pygame.K_s:
                            self.add_command_message("> Save")
                            # Save game
                            if self.map_filepath:
                                saved_filepath = save_game(
                                    self.map_filepath,
                                    self.player_x,
                                    self.player_y,
                                    self.calendar,
                                    self.command_messages,
                                    self.explored_tiles,
                                    self.visible_tiles,
                                    self.settlements,
                                    self.current_tileset_info
                                )
                                if saved_filepath:
                                    self.add_command_message("Game saved")
                                else:
                                    self.add_command_message("Error saving game")
                            else:
                                self.add_command_message("Cannot save: no map file")
                            self.pending_prompt = None
                            command_executed = True
                        elif event.key == pygame.K_l:
                            self.add_command_message("> Load")
                            self.add_command_message("Loading not implemented in-game. Use main menu.")
                            self.pending_prompt = None
                            command_executed = True
                        elif event.key == pygame.K_ESCAPE:
                            # Cancel prompt
                            self.add_command_message("Cancelled")
                            self.pending_prompt = None
                            command_executed = True
                    elif self.pending_prompt == 'quit':
                        if event.key == pygame.K_s:
                            self.add_command_message("> Save and quit")
                            # Save and quit
                            if self.map_filepath:
                                saved_filepath = save_game(
                                    self.map_filepath,
                                    self.player_x,
                                    self.player_y,
                                    self.calendar,
                                    self.command_messages,
                                    self.explored_tiles,
                                    self.visible_tiles,
                                    self.settlements,
                                    self.current_tileset_info
                                )
                                if saved_filepath:
                                    self.add_command_message("Game saved. Quitting...")
                                else:
                                    self.add_command_message("Error saving game. Quitting anyway...")
                            else:
                                self.add_command_message("Cannot save: no map file. Quitting...")
                            self.pending_prompt = None
                            return 'quit'
                        elif event.key == pygame.K_q:
                            self.add_command_message("> Quit")
                            self.add_command_message("Quitting without saving...")
                            self.pending_prompt = None
                            return 'quit'
                        elif event.key == pygame.K_c or event.key == pygame.K_ESCAPE:
                            # Cancel quit
                            self.add_command_message("> Cancel")
                            self.add_command_message("Cancelled")
                            self.pending_prompt = None
                            command_executed = True
                
                # Only process movement and other commands if no prompt is active
                if not self.pending_prompt and not command_executed:
                    # Movement commands
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.add_command_message("> Move north")
                        self.move_player('north')
                        command_executed = True
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.add_command_message("> Move south")
                        self.move_player('south')
                        command_executed = True
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.add_command_message("> Move east")
                        self.move_player('east')
                        command_executed = True
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.add_command_message("> Move west")
                        self.move_player('west')
                        command_executed = True
                    elif event.key == pygame.K_m:
                        self.add_command_message("> Toggle map view")
                        # Toggle map view
                        self.map_view_mode = not self.map_view_mode
                        if self.map_view_mode:
                            # Initialize map view camera to center on player
                            self.map_view_camera_x = self.player_x - (self.map_view_width // self.map_view_tile_size) // 2
                            self.map_view_camera_y = self.player_y - (self.map_view_height // self.map_view_tile_size) // 2
                            self._clamp_map_view_camera()
                            self.add_command_message("Map view opened")
                        else:
                            self.add_command_message("Map view closed")
                        command_executed = True
                    elif event.key == pygame.K_f:
                        # Save/Load prompt
                        self.add_command_message("> Save/Load menu")
                        self.pending_prompt = 'save_or_load'
                        self.add_command_message("Save or Load? (s/l)")
                        command_executed = True
                    elif event.key == pygame.K_q:
                        # Quit prompt
                        self.add_command_message("> Quit game")
                        self.pending_prompt = 'quit'
                        self.add_command_message("Save and quit, quit, or cancel? (s/q/c)")
                        command_executed = True
                    elif event.key == pygame.K_SPACE:
                        # Pass a turn (advance time without moving)
                        self.add_command_message("> Pass")
                        # Advance time by 2 hours (same as moving on grassland)
                        self.calendar.add_hours(2)
                        # Update caravans when time passes
                        self._update_caravans_on_move()
                        command_executed = True
                    elif event.key == pygame.K_t:
                        # Tileset selection
                        self.add_command_message("> Tileset selection")
                        self.showing_tileset_selection = True
                        self.tileset_selection_screen = TilesetSelectionScreen(self.screen)
                        command_executed = True
                    elif event.key == pygame.K_UP and self.current_settlement:
                        # Scroll status area up
                        self.status_scroll_offset = max(0, self.status_scroll_offset - self.status_scroll_speed)
                        command_executed = True
                    elif event.key == pygame.K_DOWN and self.current_settlement:
                        # Scroll status area down
                        self.status_scroll_offset += self.status_scroll_speed
                        command_executed = True
        elif event.type == pygame.MOUSEWHEEL:
            # Handle mouse wheel scrolling in status area
            if self.current_settlement:
                self.status_scroll_offset = max(0, self.status_scroll_offset - event.y * self.status_scroll_speed)
        
        return None
    
    def _check_and_spawn_caravans(self):
        """Check if it's morning and spawn caravans with 30% probability."""
        # Check if it's morning (hour 6) and we haven't checked today
        if self.calendar.hour == 6 and (self.last_caravan_check_day != self.calendar.day or 
                                         self.last_caravan_check_hour != self.calendar.hour):
            self.last_caravan_check_day = self.calendar.day
            self.last_caravan_check_hour = self.calendar.hour
            
            # Get all villages that have a town to supply
            villages = [s for s in self.settlements if s.settlement_type == SettlementType.VILLAGE]
            
            for village in villages:
                if not village.vassal_to:
                    continue  # Skip villages without a town
                
                town = village.vassal_to
                
                # Check if town already has 1000+ of this resource - if so, don't spawn caravan
                if village.supplies_resource and town.settlement_type == SettlementType.TOWN:
                    if village.supplies_resource in town.resources:
                        if town.resources[village.supplies_resource] >= 1000:
                            continue  # Town has enough of this resource, skip spawning
                
                    # Check if there's already a caravan for this village
                    existing = [c for c in self.caravans if c.village == village and 
                               c.state in [CaravanState.AT_VILLAGE, CaravanState.TRAVELING_TO_TOWN]]
                    if existing:
                        continue  # Already has a caravan
                    
                # 30% chance to spawn a caravan
                if random.random() < 0.3:
                    # Create new caravan
                    village_x, village_y = village.get_position()
                    town_x, town_y = town.get_position()
                    
                    # Check if path is clear
                    if self._has_clear_path(village_x, village_y, town_x, town_y):
                        caravan = Caravan(village, town, village_x, village_y)
                        
                        # Set paths
                        path_to_town = self._get_path(village_x, village_y, town_x, town_y)
                        path_to_village = self._get_path(town_x, town_y, village_x, village_y)
                        
                        # Validate paths - ensure no water tiles
                        path_to_town = self._validate_path(path_to_town)
                        path_to_village = self._validate_path(path_to_village)
                        
                        if path_to_town and path_to_village:
                            caravan.set_path_to_town(path_to_town)
                            caravan.set_path_to_village(path_to_village)
                            
                            # Start journey to town
                            caravan.start_journey_to_town()
                            
                            self.caravans.append(caravan)
                        else:
                            continue  # Invalid path, skip this caravan
                    # Note: If path is not clear, caravan simply doesn't spawn (silent failure)
    
    def _update_caravans_on_move(self):
        """Update caravan positions when player moves (time passes)."""
        """Caravans move one tile at a time, respecting terrain movement rules."""
        
        for caravan in self.caravans[:]:  # Use slice to avoid modification during iteration
            if caravan.state == CaravanState.TRAVELING_TO_TOWN:
                # Get current position as integer tile coordinates
                current_tile_x = int(caravan.x)
                current_tile_y = int(caravan.y)
                
                # Check if we have a path and haven't reached the end
                if caravan.path_index_to_town >= len(caravan.path_to_town):
                    # Arrived at town
                    town_x, town_y = caravan.town.get_position()
                    caravan.x = float(town_x)
                    caravan.y = float(town_y)
                    caravan.state = CaravanState.AT_TOWN
                    caravan.arrived_at_town_time = (self.calendar.day, self.calendar.hour)
                    
                    # Add resources to town immediately
                    if caravan.village.supplies_resource:
                        caravan.town.add_resource(caravan.village.supplies_resource, 10)
                        
                        # Check for trade good production
                        trade_goods_produced = caravan.town.produce_trade_goods()
                        
                        # Check for trade good transfer to liege
                        trade_goods_transferred = caravan.town.transfer_trade_goods_to_liege()
                        
                        # Log messages if something happened
                        if trade_goods_produced > 0:
                            self.add_status_message(f"{caravan.town.name or 'Town'} produced {trade_goods_produced} trade good(s)")
                        if trade_goods_transferred > 0:
                            liege_name = caravan.town.vassal_to.name if caravan.town.vassal_to else "Unknown"
                            self.add_status_message(f"{caravan.town.name or 'Town'} sent {trade_goods_transferred} trade goods to {liege_name}")
                    continue
                
                # Get next waypoint
                target_x, target_y = caravan.path_to_town[caravan.path_index_to_town]
                
                # Check if we're already at the target tile
                if current_tile_x == target_x and current_tile_y == target_y:
                    # Move to next waypoint
                    caravan.path_index_to_town += 1
                    continue
                
                # Check terrain at target location
                if 0 <= target_y < self.map_height and 0 <= target_x < self.map_width:
                    target_terrain = self.map_data[target_y][target_x]
                    
                    # Check if terrain requires 2 moves (hills, forest, forested_hill)
                    is_slow_terrain = target_terrain.terrain_type in [
                        TerrainType.HILLS, 
                        TerrainType.FOREST, 
                        TerrainType.FORESTED_HILL
                    ]
                    
                    if is_slow_terrain:
                        # Need 2 moves for slow terrain
                        if caravan.pending_direction is None:
                            # First move - start pending
                            caravan.pending_direction = (target_x, target_y)
                            caravan.pending_move_count = 1
                        elif caravan.pending_direction == (target_x, target_y):
                            # Second move in same direction - complete movement
                            caravan.pending_move_count += 1
                            if caravan.pending_move_count >= 2:
                                # Complete movement
                                caravan.x = float(target_x)
                                caravan.y = float(target_y)
                                caravan.path_index_to_town += 1
                                caravan.pending_direction = None
                                caravan.pending_move_count = 0
                        else:
                            # Different direction - reset and start new pending
                            caravan.pending_direction = (target_x, target_y)
                            caravan.pending_move_count = 1
                    else:
                        # Fast terrain - move immediately
                        caravan.x = float(target_x)
                        caravan.y = float(target_y)
                        caravan.path_index_to_town += 1
                        caravan.pending_direction = None
                        caravan.pending_move_count = 0
            
            elif caravan.state == CaravanState.AT_TOWN:
                # Check if it's the next morning (hour 6)
                if caravan.arrived_at_town_time:
                    arrived_day, arrived_hour = caravan.arrived_at_town_time
                    # Start return journey on the next morning (hour 6)
                    if self.calendar.hour == 6:
                        # Check if at least one day has passed, or if it's the same day but we arrived before 6
                        if (self.calendar.day > arrived_day or 
                            (self.calendar.day == arrived_day and arrived_hour < 6)):
                            caravan.start_journey_to_village()
            
            elif caravan.state == CaravanState.TRAVELING_TO_VILLAGE:
                # Get current position as integer tile coordinates
                current_tile_x = int(caravan.x)
                current_tile_y = int(caravan.y)
                
                # Check if we have a path and haven't reached the end
                if caravan.path_index_to_village >= len(caravan.path_to_village):
                    # Arrived at village
                    village_x, village_y = caravan.village.get_position()
                    caravan.x = float(village_x)
                    caravan.y = float(village_y)
                    caravan.state = CaravanState.AT_VILLAGE
                    # Remove caravan when it returns
                    self.caravans.remove(caravan)
                    continue
                
                # Get next waypoint
                target_x, target_y = caravan.path_to_village[caravan.path_index_to_village]
                
                # Check if we're already at the target tile
                if current_tile_x == target_x and current_tile_y == target_y:
                    # Move to next waypoint
                    caravan.path_index_to_village += 1
                    continue
                
                # Check terrain at target location
                if 0 <= target_y < self.map_height and 0 <= target_x < self.map_width:
                    target_terrain = self.map_data[target_y][target_x]
                    
                    # Check if terrain requires 2 moves (hills, forest, forested_hill)
                    is_slow_terrain = target_terrain.terrain_type in [
                        TerrainType.HILLS, 
                        TerrainType.FOREST, 
                        TerrainType.FORESTED_HILL
                    ]
                    
                    if is_slow_terrain:
                        # Need 2 moves for slow terrain
                        if caravan.pending_direction is None:
                            # First move - start pending
                            caravan.pending_direction = (target_x, target_y)
                            caravan.pending_move_count = 1
                        elif caravan.pending_direction == (target_x, target_y):
                            # Second move in same direction - complete movement
                            caravan.pending_move_count += 1
                            if caravan.pending_move_count >= 2:
                                # Complete movement
                                caravan.x = float(target_x)
                                caravan.y = float(target_y)
                                caravan.path_index_to_village += 1
                                caravan.pending_direction = None
                                caravan.pending_move_count = 0
                        else:
                            # Different direction - reset and start new pending
                            caravan.pending_direction = (target_x, target_y)
                            caravan.pending_move_count = 1
                    else:
                        # Fast terrain - move immediately
                        caravan.x = float(target_x)
                        caravan.y = float(target_y)
                        caravan.path_index_to_village += 1
                        caravan.pending_direction = None
                        caravan.pending_move_count = 0
    
    def update(self, dt: float):
        """
        Update game state (movement animation, etc.).
        
        Args:
            dt: Delta time in seconds since last frame
        """
        # Update movement animation
        self.update_movement(dt)
        
        # Check for caravan spawning in the morning
        self._check_and_spawn_caravans()
        
        # Note: Caravans are now updated in _update_caravans_on_move() when player moves
    
    def render(self):
        """Render the play screen."""
        # Render tileset selection screen if active
        if self.showing_tileset_selection and self.tileset_selection_screen:
            self.tileset_selection_screen.render()
            return
        
        # Check if in map view mode
        if self.map_view_mode:
            self._render_map_view()
            pygame.display.flip()
            return
        
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Draw map view (top left 2x2)
        map_surface = pygame.Surface((self.map_view_width, self.map_view_height))
        # Convert camera position to integers for rendering (tiles are discrete)
        camera_x_int = int(self.camera_x)
        camera_y_int = int(self.camera_y)
        self.renderer.render_map(self.map_data, map_surface, camera_x_int, camera_y_int, 
                                self.settlements, explored_tiles=self.explored_tiles, 
                                visible_tiles=self.visible_tiles, caravans=self.caravans)
        
        # Draw player marker on map (with smooth interpolation during movement)
        player_tile_x, player_tile_y = self.get_player_render_position()
        player_screen_x = (player_tile_x - self.camera_x) * self.tile_size
        player_screen_y = (player_tile_y - self.camera_y) * self.tile_size
        
        if 0 <= player_screen_x < self.map_view_width and 0 <= player_screen_y < self.map_view_height:
            # Draw player as a colored circle
            pygame.draw.circle(map_surface, (255, 0, 0), 
                             (int(player_screen_x + self.tile_size // 2), 
                              int(player_screen_y + self.tile_size // 2)),
                             self.tile_size // 3)
            pygame.draw.circle(map_surface, (255, 255, 255),
                             (int(player_screen_x + self.tile_size // 2),
                              int(player_screen_y + self.tile_size // 2)),
                             self.tile_size // 3, 2)
        
        self.screen.blit(map_surface, (0, 0))
        
        # Draw status area (right 1x2)
        status_rect = pygame.Rect(self.map_view_width, 0, self.status_width, self.status_height)
        pygame.draw.rect(self.screen, (20, 20, 30), status_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), status_rect, 2)
        
        # Draw status messages
        font = pygame.font.Font(None, 24)
        title_font = pygame.font.Font(None, 28)
        
        # Title
        title_text = title_font.render("Status", True, (255, 255, 255))
        self.screen.blit(title_text, (self.map_view_width + 10, 10))
        
        # Display time and date
        datetime_text = self.calendar.get_full_datetime_string()
        datetime_surface = font.render(datetime_text, True, (255, 215, 0))  # Gold color
        self.screen.blit(datetime_surface, (self.map_view_width + 10, 40))
        
        # Display current terrain type
        if 0 <= self.player_y < self.map_height and 0 <= self.player_x < self.map_width:
            current_terrain = self.map_data[self.player_y][self.player_x]
            terrain_type = current_terrain.terrain_type
            # Format terrain type name (capitalize and replace underscores)
            terrain_name = terrain_type.value.replace('_', ' ').title()
            terrain_text = f"Terrain: {terrain_name}"
            terrain_surface = font.render(terrain_text, True, (200, 200, 255))  # Light blue
            self.screen.blit(terrain_surface, (self.map_view_width + 10, 70))
        
        # Display settlement information if player is on a settlement
        # Create a clipping surface for scrollable content
        status_content_start_y = 100
        status_content_height = self.status_height - status_content_start_y - 10
        status_clip_rect = pygame.Rect(self.map_view_width, status_content_start_y, 
                                      self.status_width, status_content_height)
        
        # Create a surface for scrollable content
        content_surface = pygame.Surface((self.status_width, 2000))  # Large enough for long content
        content_surface.fill((20, 20, 30))  # Match background
        
        y_offset = -self.status_scroll_offset  # Apply scroll offset
        
        if self.current_settlement:
            settlement = self.current_settlement
            settlement_name = settlement.name if settlement.name else "Unnamed"
            
            # Settlement name header
            settlement_title = title_font.render(settlement_name, True, (255, 255, 0))  # Yellow
            content_surface.blit(settlement_title, (10, y_offset))
            y_offset += 30
            
            # Get worldbuilding data
            wb_data = self._find_settlement_worldbuilding_data(settlement)
            
            # Debug: Print worldbuilding data lookup
            if not wb_data:
                print(f"Debug: No worldbuilding data found for {settlement.name} (type: {settlement.settlement_type})")
                if self.worldbuilding_data:
                    print(f"Debug: Worldbuilding data exists with {len(self.worldbuilding_data)} top-level keys")
                else:
                    print("Debug: No worldbuilding data loaded at all")
            
            # Display description if available
            if wb_data and 'description' in wb_data:
                desc_text = wb_data['description']
                # Word wrap description
                desc_font = pygame.font.Font(None, 22)
                words = desc_text.split()
                lines = []
                current_line = []
                current_width = 0
                max_width = self.status_width - 30
                
                for word in words:
                    word_surface = desc_font.render(word + ' ', True, (200, 200, 200))
                    word_width = word_surface.get_width()
                    if current_width + word_width > max_width and current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width
                    else:
                        current_line.append(word)
                        current_width += word_width
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                for line in lines:
                    desc_surface = desc_font.render(line, True, (200, 200, 200))
                    content_surface.blit(desc_surface, (10, y_offset))
                    y_offset += 22
                y_offset += 10
            
            # Display leader info if available
            if wb_data and 'leader' in wb_data:
                leader = wb_data['leader']
                leader_font = pygame.font.Font(None, 24)
                
                if 'name' in leader:
                    leader_name_text = f"Leader: {leader['name']}"
                    leader_name_surface = leader_font.render(leader_name_text, True, (255, 200, 100))  # Orange
                    content_surface.blit(leader_name_surface, (10, y_offset))
                    y_offset += 28
                
                if 'biography' in leader:
                    bio_text = leader['biography']
                    # Word wrap biography
                    bio_font = pygame.font.Font(None, 22)
                    words = bio_text.split()
                    lines = []
                    current_line = []
                    current_width = 0
                    max_width = self.status_width - 30
                    
                    for word in words:
                        word_surface = bio_font.render(word + ' ', True, (180, 180, 255))
                        word_width = word_surface.get_width()
                        if current_width + word_width > max_width and current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_width = word_width
                        else:
                            current_line.append(word)
                            current_width += word_width
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    for line in lines:
                        bio_surface = bio_font.render(line, True, (180, 180, 255))
                        content_surface.blit(bio_surface, (10, y_offset))
                        y_offset += 22
                    y_offset += 10
            
            # Display settlement type-specific info
            if settlement.settlement_type == SettlementType.VILLAGE:
                # Village: Show resource and town relationship
                resource = settlement.supplies_resource or "Unknown"
                town_name = settlement.vassal_to.name if settlement.vassal_to else "Unknown"
                village_text = f"Sends {resource} to {town_name} in return for protection."
                village_surface = font.render(village_text, True, (200, 255, 200))  # Light green
                content_surface.blit(village_surface, (10, y_offset))
                y_offset += 30
            
            elif settlement.settlement_type == SettlementType.TOWN:
                # Town: Show vassal relationships, resources, and trade goods
                # Vassal relationships
                if settlement.vassal_to:
                    liege_name = settlement.vassal_to.name if settlement.vassal_to.name else "Unnamed"
                    liege_text = f"Vassal to: {liege_name}"
                    liege_surface = font.render(liege_text, True, (255, 200, 100))  # Orange
                    content_surface.blit(liege_surface, (10, y_offset))
                    y_offset += 25
                else:
                    free_text = "Status: Independent"
                    free_surface = font.render(free_text, True, (150, 150, 150))  # Gray
                    content_surface.blit(free_surface, (10, y_offset))
                    y_offset += 25
                
                # Vassal villages
                if settlement.vassal_villages:
                    vassal_count = len(settlement.vassal_villages)
                    vassal_text = f"Vassal villages: {vassal_count}"
                    vassal_surface = font.render(vassal_text, True, (200, 200, 200))
                    content_surface.blit(vassal_surface, (10, y_offset))
                    y_offset += 25
                
                # Resources
                resources_text = "Resources:"
                resources_surface = font.render(resources_text, True, (200, 200, 255))
                content_surface.blit(resources_surface, (10, y_offset))
                y_offset += 25
                
                for resource_name, amount in settlement.resources.items():
                    resource_text = f"  {resource_name}: {amount}"
                    resource_surface = font.render(resource_text, True, (180, 180, 255))
                    content_surface.blit(resource_surface, (10, y_offset))
                    y_offset += 20
                
                # Trade goods
                trade_text = f"Trade goods: {settlement.trade_goods}"
                trade_surface = font.render(trade_text, True, (255, 215, 0))  # Gold
                content_surface.blit(trade_surface, (10, y_offset))
                y_offset += 30
            
            elif settlement.settlement_type == SettlementType.CITY:
                # City: Show vassal relationships and trade goods
                # Vassal towns
                if settlement.vassal_towns:
                    vassal_count = len(settlement.vassal_towns)
                    vassal_text = f"Vassal towns: {vassal_count}"
                    vassal_surface = font.render(vassal_text, True, (200, 200, 200))
                    content_surface.blit(vassal_surface, (10, y_offset))
                    y_offset += 25
                
                # Trade goods
                trade_text = f"Trade goods: {settlement.trade_goods}"
                trade_surface = font.render(trade_text, True, (255, 215, 0))  # Gold
                content_surface.blit(trade_surface, (10, y_offset))
                y_offset += 30
            
            # Update max scroll based on content height
            max_scroll = max(0, y_offset + self.status_scroll_offset - status_content_height)
            self.status_scroll_offset = min(self.status_scroll_offset, max_scroll)
        
        # Blit the scrollable content with clipping
        self.screen.set_clip(status_clip_rect)
        self.screen.blit(content_surface, (self.map_view_width, status_content_start_y + self.status_scroll_offset))
        self.screen.set_clip(None)
        
        # Messages (scrollable, show most recent) - appear after settlement info or at y_offset=100 if no settlement
        if not self.current_settlement:
            y_offset = 100
            for message in self.status_messages[-12:]:  # Show last 12 messages (less space due to date and terrain)
                text_surface = font.render(message, True, (200, 200, 200))
                if y_offset + text_surface.get_height() < self.status_height - 10:
                    self.screen.blit(text_surface, (self.map_view_width + 10, y_offset))
                    y_offset += 25
        
        # Draw command/results area (bottom 1x3) - terminal style
        command_rect = pygame.Rect(0, self.map_view_height, self.command_width, self.command_height)
        pygame.draw.rect(self.screen, (10, 10, 15), command_rect)  # Darker background for terminal feel
        pygame.draw.rect(self.screen, (50, 50, 50), command_rect, 2)
        
        # Terminal-style message log
        font = pygame.font.Font(None, 20)  # Monospace-like font size
        line_height = 22
        
        # Calculate how many lines fit
        available_height = self.command_height - 20  # Padding
        max_lines = available_height // line_height
        
        # Show recent messages
        messages_to_show = self.command_messages[-max_lines:] if max_lines > 0 else []
        
        # Draw messages
        y_offset = self.map_view_height + 10
        for message in messages_to_show:
            # Color code: commands with ">" are green, results are white
            if message.startswith(">"):
                color = (100, 255, 100)  # Green for commands
            else:
                color = (200, 200, 200)  # Light gray for results
            
            text_surface = font.render(message, True, color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += line_height
        
        # Draw prompt at the bottom if not in a prompt state
        if not self.pending_prompt:
            prompt_text = "> "
            prompt_surface = font.render(prompt_text, True, (100, 255, 100))  # Green
            self.screen.blit(prompt_surface, (10, y_offset))
        
        pygame.display.flip()

