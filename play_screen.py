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
from quest_generator import generate_quest
from journal_dialog import show_journal_dialog
from text_utils import wrap_text


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
        
        # Quest state - initialize before _update_camera() which may check in_quest_location
        self.in_quest_location = False
        self.quest_location_map = None
        self.quest_item_location = None  # (x, y) location of quest item on quest map
        self.quest_location_size = 0
        self.quest_location_approach_direction = None
        self.pending_exit_quest_confirmation = False  # Flag for exit confirmation prompt
        
        # Camera position (centered on player) - now safe to call after movement state is initialized
        self._update_camera()
        
        # Status messages (scrollable list)
        self.status_messages = []
        self.max_status_messages = 20
        
        # Command/Results area (scrollable list) - terminal style
        self.command_messages = []
        self.max_command_messages = 50  # More messages for terminal feel
        
        # Prompt state
        self.pending_prompt = None  # 'save_or_load', 'quit_save', 'quest_offer', 'journal', etc.
        self.prompt_response = None
        
        # Renown system - track renown with each settlement
        if saved_state:
            # Handle legacy saves that don't have renown data
            self.settlement_renown = saved_state.get('settlement_renown', {})
            # Ensure all current settlements have renown entries (for new settlements added to map)
            for settlement in settlements:
                settlement_key = (settlement.x, settlement.y)
                if settlement_key not in self.settlement_renown:
                    self.settlement_renown[settlement_key] = 0
        else:
            # Initialize renown to 0 for all settlements
            self.settlement_renown = {}
            for settlement in settlements:
                settlement_key = (settlement.x, settlement.y)
                self.settlement_renown[settlement_key] = 0
        
        # Quest state (restore from saved state if available)
        if saved_state:
            self.current_quest = saved_state.get('current_quest', None)
            # Restore quest location state if player was in a quest location
            self.in_quest_location = saved_state.get('in_quest_location', False)
            self.quest_location_size = saved_state.get('quest_location_size', 0)
            self.quest_location_approach_direction = saved_state.get('quest_location_approach_direction', None)
            # Restore quest archive
            self.quest_archive = saved_state.get('quest_archive', [])
            # Restore quest item location if available
            if self.current_quest and self.current_quest.get('item_location') and not self.current_quest.get('item_found', False):
                self.quest_item_location = tuple(self.current_quest['item_location'])
            else:
                self.quest_item_location = None
            # Quest location map will be recreated if needed when rendering
            if self.in_quest_location and self.quest_location_size > 0:
                # Recreate quest location map (fully grassland)
                self.quest_location_map = []
                for y in range(self.quest_location_size):
                    row = []
                    for x in range(self.quest_location_size):
                        row.append(Terrain(TerrainType.GRASSLAND))
                    self.quest_location_map.append(row)
            else:
                self.quest_location_map = None
        else:
            self.current_quest = None
            # Quest location state already initialized above
            self.quest_location_map = None
            self.quest_archive = []
        self.quest_offer_settlement = None  # Settlement that is currently offering a quest
        
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
        
        # Worldbuilding data (must be set before checking settlement position)
        self.worldbuilding_data = worldbuilding_data
        
        # Current settlement (settlement player is standing on)
        self.current_settlement: Optional[Settlement] = None
        self._check_settlement_at_position()
        
        # Status area scrolling
        self.status_scroll_offset = 0
        self.status_scroll_speed = 20
        
        # Tileset selection screen
        self.showing_tileset_selection = False
        self.tileset_selection_screen: Optional[TilesetSelectionScreen] = None
        # Current tileset info (for saving/loading)
        self.current_tileset_info: Optional[Dict] = None
        
    def _update_camera(self):
        """Update camera position to center on player, or position at edge for quest locations."""
        # Calculate viewport size in tiles
        viewport_width = self.map_view_width // self.tile_size
        viewport_height = self.map_view_height // self.tile_size
        
        if self.in_quest_location and hasattr(self, 'quest_location_approach_direction') and self.quest_location_approach_direction:
            # In quest location: position player at the correct edge of viewport (cardinal directions only)
            approach = self.quest_location_approach_direction
            map_width = self.quest_location_size
            map_height = self.quest_location_size
            
            if approach == 'north':
                # Traveling north (approaching from south): player at bottom of viewport
                # Player is at y = map_height - 1, should appear at bottom of screen (y = viewport_height - 1)
                # So: player_y - camera_y = viewport_height - 1
                # Therefore: camera_y = player_y - viewport_height + 1
                self.camera_x = max(0, min(map_width - viewport_width, self.player_x - viewport_width // 2))
                self.camera_y = max(0, min(map_height - viewport_height, self.player_y - viewport_height + 1))
            elif approach == 'south':
                # Traveling south (approaching from north): player at top of viewport initially
                # Player is at y = 0 initially, should appear at top of screen (y = 0)
                # But as player moves down, camera should follow (center on player when possible)
                # So: player_y - camera_y = 0 initially, but allow camera to scroll down
                self.camera_x = max(0, min(map_width - viewport_width, self.player_x - viewport_width // 2))
                # Start at top, but allow scrolling down as player moves
                # If player is near top, keep camera at top; otherwise center on player
                if self.player_y < viewport_height // 2:
                    # Player near top, keep camera at top
                    self.camera_y = 0
                else:
                    # Player moved down, center camera on player
                    self.camera_y = max(0, min(map_height - viewport_height, self.player_y - viewport_height // 2))
            elif approach == 'east':
                # Traveling east (approaching from west): player at left of viewport
                # Player is at x = 0, should appear at left of screen (x = 0)
                # So: player_x - camera_x = 0
                # Therefore: camera_x = player_x = 0
                self.camera_x = 0
                self.camera_y = max(0, min(map_height - viewport_height, self.player_y - viewport_height // 2))
            elif approach == 'west':
                # Traveling west (approaching from east): player at right of viewport
                # Player is at x = map_width - 1, should appear at right of screen (x = viewport_width - 1)
                # So: player_x - camera_x = viewport_width - 1
                # Therefore: camera_x = player_x - viewport_width + 1
                self.camera_x = max(0, min(map_width - viewport_width, self.player_x - viewport_width + 1))
                self.camera_y = max(0, min(map_height - viewport_height, self.player_y - viewport_height // 2))
            else:
                # Fallback: center on player
                self.camera_x = max(0, min(map_width - viewport_width, self.player_x - viewport_width // 2))
                self.camera_y = max(0, min(map_height - viewport_height, self.player_y - viewport_height // 2))
        else:
            # Normal overland map: center camera on player
            self.camera_x = self.player_x - viewport_width // 2
            self.camera_y = self.player_y - viewport_height // 2
            
            # Clamp camera to map bounds
            map_width = self.map_width
            map_height = self.map_height
            self.camera_x = max(0, min(map_width - viewport_width, self.camera_x))
            self.camera_y = max(0, min(map_height - viewport_height, self.camera_y))
    
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
        
        # Draw quest marker prominently (always visible, even if not explored) - only if quest is active
        if self.current_quest and not self.in_quest_location:
            quest_status = self.current_quest.get('quest_status', 'active')
            if quest_status == 'active':
                quest_x, quest_y = self.current_quest['quest_coordinates']
                if start_x <= quest_x < end_x and start_y <= quest_y < end_y:
                    quest_screen_x = (quest_x - self.map_view_camera_x) * self.map_view_tile_size
                    quest_screen_y = (quest_y - self.map_view_camera_y) * self.map_view_tile_size
                    quest_center_x = quest_screen_x + self.map_view_tile_size // 2
                    quest_center_y = quest_screen_y + self.map_view_tile_size // 2
                    
                    # Draw a large, prominent quest marker (star/pentagon)
                    size = max(12, self.map_view_tile_size * 2)  # Large size for prominence
                    quest_color = (255, 255, 0)  # Bright yellow
                    glow_color = (255, 200, 0)  # Orange-yellow glow
                    
                    # Draw glow effect (larger outer circle)
                    pygame.draw.circle(map_surface, glow_color, (quest_center_x, quest_center_y), size // 2 + 3)
                    
                    # Draw pentagon/star
                    points = []
                    for i in range(5):
                        angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                        px = quest_center_x + size // 2 * math.cos(angle)
                        py = quest_center_y + size // 2 * math.sin(angle)
                        points.append((px, py))
                    
                    pygame.draw.polygon(map_surface, quest_color, points)
                    pygame.draw.polygon(map_surface, (255, 255, 255), points, 2)  # White border for contrast
        
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
        
        # Handle quest location map boundaries
        if self.in_quest_location:
            # Calculate new position first
            new_x = self.player_x
            new_y = self.player_y
            
            if direction == 'north':
                new_y = max(0, self.player_y - 1)
            elif direction == 'south':
                new_y = min(self.quest_location_size - 1, self.player_y + 1)
            elif direction == 'east':
                new_x = min(self.quest_location_size - 1, self.player_x + 1)
            elif direction == 'west':
                new_x = max(0, self.player_x - 1)
            
            # Check if player is trying to exit by moving off any edge of the map
            # Allow exit from any edge (not just the entry edge)
            would_exit = False
            if direction == 'north' and self.player_y == 0:
                would_exit = True  # At top edge, moving north would exit
            elif direction == 'south' and self.player_y == self.quest_location_size - 1:
                would_exit = True  # At bottom edge, moving south would exit
            elif direction == 'east' and self.player_x == self.quest_location_size - 1:
                would_exit = True  # At right edge, moving east would exit
            elif direction == 'west' and self.player_x == 0:
                would_exit = True  # At left edge, moving west would exit
            
            if would_exit:
                # Check if we need confirmation to exit
                if not self.pending_exit_quest_confirmation:
                    # Prompt for confirmation
                    self.pending_exit_quest_confirmation = True
                    self.add_command_message("Leave quest location? (Y/N)")
                    return
                # If we get here, confirmation was already handled
                return
            
            # Use quest location map for terrain checks
            map_data = self.quest_location_map
            map_width = self.quest_location_size
            map_height = self.quest_location_size
            # new_x and new_y already calculated above, don't recalculate
        else:
            # Use overland map
            map_data = self.map_data
            map_width = self.map_width
            map_height = self.map_height
            
            # Calculate new position for overland map
            new_x = self.player_x
            new_y = self.player_y
            
            if direction == 'north':
                new_y = max(0, new_y - 1)
            elif direction == 'south':
                new_y = min(map_height - 1, new_y + 1)
            elif direction == 'east':
                new_x = min(map_width - 1, new_x + 1)
            elif direction == 'west':
                new_x = max(0, new_x - 1)
        
        # Check if movement is valid (not into impassable terrain)
        if 0 <= new_x < map_width and 0 <= new_y < map_height:
            terrain = map_data[new_y][new_x]
            # Check if terrain allows movement
            # In quest locations, shallow water is passable
            can_move = terrain.can_move_through()
            if self.in_quest_location and terrain.terrain_type == TerrainType.SHALLOW_WATER:
                can_move = True
            
            if can_move:
                # In quest location, all movement is instant (no slowed travel)
                if self.in_quest_location:
                    # Instant movement in quest location
                    # No time advancement in quest locations
                    # Check for quest item pickup before executing movement
                    if self.in_quest_location and self.quest_item_location and not self.current_quest.get('item_found', False):
                        if (new_x, new_y) == self.quest_item_location:
                            # Player found the item!
                            target_item = self.current_quest.get('target_item', 'item')
                            self.add_command_message(f"{target_item} found!")
                            self.current_quest['item_found'] = True
                            self.current_quest['quest_status'] = 'item_found'
                            self.quest_item_location = None  # Remove from map
                    
                    # Execute movement
                    self._execute_movement(new_x, new_y, terrain, direction)
                    # Clear any pending movement
                    self.pending_direction = None
                    self.pending_move_count = 0
                else:
                    # On overland map - check for slow terrain
                    is_slow_terrain = terrain.terrain_type in [TerrainType.FOREST, TerrainType.HILLS, TerrainType.FORESTED_HILL]
                    
                    if is_slow_terrain:
                        # For slow terrain, require 2 key presses
                        if self.pending_direction == direction:
                            # Second press - complete the movement
                            self.pending_move_count += 1
                            if self.pending_move_count >= 2:
                                # Complete movement
                                self._execute_movement(new_x, new_y, terrain, direction)
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
                        self._execute_movement(new_x, new_y, terrain, direction)
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
    
    def _execute_movement(self, new_x: int, new_y: int, terrain: Terrain, movement_direction: str = None):
        """
        Execute the actual movement to the new position.
        
        Args:
            new_x: Target X coordinate
            new_y: Target Y coordinate
            terrain: Terrain at destination
            movement_direction: Direction of movement ('north', 'south', 'east', 'west')
        """
        # Determine direction from position change if not provided
        if movement_direction is None:
            if new_y < self.player_y:
                movement_direction = 'north'
            elif new_y > self.player_y:
                movement_direction = 'south'
            elif new_x > self.player_x:
                movement_direction = 'east'
            elif new_x < self.player_x:
                movement_direction = 'west'
            else:
                movement_direction = None
        
        # Update player position
        self.player_x = new_x
        self.player_y = new_y
        self._update_camera()
        
        # Mark new position as explored
        self.explored_tiles.add((self.player_x, self.player_y))
        
        # Update visibility after movement
        self._update_visibility()
        
        # Check if player landed on a quest location (only if quest is active)
        if self.current_quest and not self.in_quest_location:
            quest_status = self.current_quest.get('quest_status', 'active')
            if quest_status == 'active':
                quest_x, quest_y = self.current_quest['quest_coordinates']
                if new_x == quest_x and new_y == quest_y:
                    # Enter quest location - use movement direction as approach direction
                    self._enter_quest_location(movement_direction)
                    return
        
        # Only advance time and update caravans on overland map (not in quest locations)
        # Quest locations handle time advancement in move_player() before calling _execute_movement
        if not self.in_quest_location:
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
        
        # Determine map dimensions based on whether we're in a quest location
        if self.in_quest_location:
            map_width = self.quest_location_size
            map_height = self.quest_location_size
            map_data = self.quest_location_map
            # In quest locations, check all tiles on the map (visibility travels with player)
            # Check all tiles on the map for line of sight
            for target_y in range(map_height):
                for target_x in range(map_width):
                    # Check line of sight (using appropriate map data)
                    if self._has_line_of_sight(self.player_x, self.player_y, target_x, target_y, map_data, map_width, map_height):
                        self.visible_tiles.add((target_x, target_y))
                        # Mark as explored when visible
                        self.explored_tiles.add((target_x, target_y))
        else:
            # On overland map, limit to viewport for performance
            map_width = self.map_width
            map_height = self.map_height
            map_data = self.map_data
            
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
                    if target_x < 0 or target_x >= map_width or target_y < 0 or target_y >= map_height:
                        continue
                    
                    # Check line of sight (using appropriate map data)
                    if self._has_line_of_sight(self.player_x, self.player_y, target_x, target_y, map_data, map_width, map_height):
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
    
    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int, 
                          map_data=None, map_width=None, map_height=None) -> bool:
        """
        Check if there's line of sight between two points.
        Uses Bresenham's line algorithm to check each tile along the path.
        
        Rules for overland map:
        - Forested hills block view like forests
        - When viewing from higher elevation to lower elevation, you can see everything
          at lower elevation with no blocking (except for blocking at your own elevation, like forests)
        - Mountains and forests block view (but you can see the first tile)
        
        Rules for quest locations:
        - Forest, mountain, and forested hill block sight
        - Uses terrain.can_see_through() directly
        
        Args:
            x1, y1: Starting position
            x2, y2: Target position
            map_data: Optional map data (uses self.map_data if None)
            map_width: Optional map width (uses self.map_width if None)
            map_height: Optional map height (uses self.map_height if None)
            
        Returns:
            True if line of sight exists
        """
        # Use provided map data or fall back to instance variables
        if map_data is None:
            map_data = self.map_data
        if map_width is None:
            map_width = self.map_width
        if map_height is None:
            map_height = self.map_height
        
        # If same tile, always visible
        if x1 == x2 and y1 == y2:
            return True
        
        # Check if we're in a quest location - use simpler rules
        is_quest_location = (hasattr(self, 'in_quest_location') and self.in_quest_location and 
                            map_data is self.quest_location_map)
        
        if is_quest_location:
            # Quest location: simple rules - use terrain.can_see_through()
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
                if 0 <= y < map_height and 0 <= x < map_width:
                    terrain_obj = map_data[y][x]
                    
                    # If this is the target tile, we can see it (first tile rule)
                    if x == x2 and y == y2:
                        return True
                    
                    # If not the first tile, check blocking using terrain.can_see_through()
                    if not first_tile:
                        if not terrain_obj.can_see_through():
                            return False
                
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
                
                first_tile = False
            
            return True
        
        # Overland map: use elevation-based rules
        # Get starting elevation
        start_elevation = 2  # Default
        if 0 <= y1 < map_height and 0 <= x1 < map_width:
            start_terrain = map_data[y1][x1].terrain_type
            start_elevation = self._get_terrain_elevation(start_terrain)
        
        # Get target elevation
        target_elevation = 2  # Default
        if 0 <= y2 < map_height and 0 <= x2 < map_width:
            target_terrain = map_data[y2][x2].terrain_type
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
            if 0 <= y < map_height and 0 <= x < map_width:
                terrain = map_data[y][x].terrain_type
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
        
        # A* algorithm with early exit for very long paths
        open_set = [(0, x1, y1)]  # (f_score, x, y)
        came_from = {}
        g_score = {(x1, y1): 0}
        f_score = {(x1, y1): heuristic(x1, y1)}
        visited = set()
        
        # Limit pathfinding to reasonable distance (prevent excessive computation)
        max_distance = abs(x2 - x1) + abs(y2 - y1)
        max_nodes_to_explore = max(5000, max_distance * 100)  # Reasonable limit
        nodes_explored = 0
        
        # 8-directional movement (including diagonals)
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        while open_set and nodes_explored < max_nodes_to_explore:
            current_f, current_x, current_y = heappop(open_set)
            
            if (current_x, current_y) in visited:
                continue
            
            visited.add((current_x, current_y))
            nodes_explored += 1
            
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
        prev_settlement = self.current_settlement
        self.current_settlement = None
        for settlement in self.settlements:
            sx, sy = settlement.get_position()
            if sx == self.player_x and sy == self.player_y:
                self.current_settlement = settlement
                
                # Check if player has a quest that's item_found and is at the quest giver settlement
                if (self.current_quest and 
                    self.current_quest.get('quest_status') == 'item_found' and
                    settlement != prev_settlement):
                    # Check if this is the quest giver settlement
                    quest_giver_coords = self.current_quest.get('quest_giver_coords')
                    if quest_giver_coords and (sx, sy) == tuple(quest_giver_coords):
                        # Complete the quest!
                        wb_data = self._find_settlement_worldbuilding_data(settlement)
                        leader_name = self.current_quest.get('leader_name', 'Unknown Leader')
                        if wb_data and 'leader' in wb_data and 'name' in wb_data['leader']:
                            leader_name = wb_data['leader']['name']
                        
                        target_item = self.current_quest.get('target_item', 'item')
                        self.add_command_message(f"{leader_name}: Thank you for retrieving the {target_item.lower()}! You have our gratitude.")
                        
                        # Update renown: +3 for completing quest (in addition to +2 for accepting = +5 total)
                        settlement_key = (sx, sy)
                        if settlement_key not in self.settlement_renown:
                            self.settlement_renown[settlement_key] = 0
                        self.settlement_renown[settlement_key] += 3
                        
                        # Archive the completed quest
                        completed_quest = self.current_quest.copy()
                        completed_quest['quest_status'] = 'completed'
                        completed_quest['status'] = 'completed'
                        completed_quest['completed_at'] = self.calendar.get_full_datetime_string()
                        self.quest_archive.append(completed_quest)
                        
                        # Clear current quest
                        self.current_quest = None
                        self.quest_item_location = None
                        break
                
                # Offer quest if player doesn't have one, just landed on this settlement, and it's a village
                if (not self.current_quest and settlement != prev_settlement and 
                    settlement.settlement_type == SettlementType.VILLAGE):
                    self.quest_offer_settlement = settlement
                    wb_data = self._find_settlement_worldbuilding_data(settlement)
                    leader_name = "Unknown Leader"
                    if wb_data and 'leader' in wb_data and 'name' in wb_data['leader']:
                        leader_name = wb_data['leader']['name']
                    self.add_command_message(f"{leader_name}: Will you help us by completing a quest? (Y/N)")
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
                # Disable map view in quest locations
                if self.in_quest_location:
                    self.add_command_message("> Map view disabled in quest locations")
                    command_executed = True
                else:
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
                
                # Check for exit quest confirmation FIRST - ignore all other input
                if self.pending_exit_quest_confirmation:
                    if event.key == pygame.K_y:
                        self.add_command_message("> Y")
                        self.pending_exit_quest_confirmation = False
                        self._exit_quest_location()
                        return None
                    elif event.key == pygame.K_n:
                        self.add_command_message("> N")
                        self.add_command_message("Cancelled")
                        self.pending_exit_quest_confirmation = False
                        return None
                    # Ignore all other keys when confirmation is pending
                    return None
                
                # Check for prompt responses (before movement commands) - ignore all other input
                if self.pending_prompt:
                    # Handle prompt responses
                    if self.pending_prompt == 'save_or_load':
                        if event.key == pygame.K_s:
                            self.add_command_message("> Save")
                            self.add_command_message("Saving...")
                            # Render immediately to show the message
                            self.render()
                            pygame.display.flip()
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
                                    self.current_tileset_info,
                                    self.current_quest,
                                    self.in_quest_location,
                                    self.quest_location_size,
                                    self.quest_location_approach_direction,
                                    self.quest_archive,
                                    self.settlement_renown
                                )
                                if saved_filepath:
                                    self.add_command_message(f"Game saved to {saved_filepath}")
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
                            self.add_command_message("> ESC")
                            self.add_command_message("Cancelled")
                            self.pending_prompt = None
                            command_executed = True
                    elif self.pending_prompt == 'quit':
                        if event.key == pygame.K_s:
                            self.add_command_message("> Save and quit")
                            self.add_command_message("Saving and quitting...")
                            # Render immediately to show the message
                            self.render()
                            pygame.display.flip()
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
                                    self.current_tileset_info,
                                    self.current_quest,
                                    self.in_quest_location,
                                    self.quest_location_size,
                                    self.quest_location_approach_direction,
                                    self.quest_archive,
                                    self.settlement_renown
                                )
                                if saved_filepath:
                                    self.add_command_message(f"Game saved to {saved_filepath}")
                                    self.add_command_message("Quitting...")
                                else:
                                    self.add_command_message("Error saving game. Quitting anyway...")
                            else:
                                self.add_command_message("Cannot save: no map file. Quitting...")
                            self.pending_prompt = None
                            # Force a render to show the save message before quitting
                            self.render()
                            pygame.display.flip()
                            return 'quit'
                        elif event.key == pygame.K_q:
                            self.add_command_message("> Quit")
                            self.add_command_message("Quitting without saving...")
                            self.pending_prompt = None
                            return 'quit'
                        elif event.key == pygame.K_c:
                            # Cancel quit
                            self.add_command_message("> C")
                            self.add_command_message("Cancelled")
                            self.pending_prompt = None
                            command_executed = True
                        elif event.key == pygame.K_ESCAPE:
                            # Cancel quit
                            self.add_command_message("> ESC")
                            self.add_command_message("Cancelled")
                            self.pending_prompt = None
                            command_executed = True
                    elif self.pending_prompt == 'journal':
                        if event.key == pygame.K_d:
                            # Drop quest (not allowed in quest location)
                            if self.in_quest_location:
                                self.add_command_message("Cannot drop quest while in quest location")
                                self.pending_prompt = None
                                command_executed = True
                            elif self.current_quest:
                                # Show confirmation dialog
                                from confirm_dialog import show_confirm_dialog
                                import pygame as pg
                                temp_clock = pg.time.Clock()
                                
                                # Get quest giver info for warning
                                leader_name = self.current_quest.get('leader_name', 'Unknown Leader')
                                settlement_name = self.current_quest.get('settlement_name', 'Unknown Settlement')
                                warning = f"Warning: You may lose some renown with {leader_name} of {settlement_name}."
                                
                                if show_confirm_dialog(self.screen, temp_clock, "Drop this quest?", warning):
                                    # Archive the quest as dropped
                                    archived_quest = self.current_quest.copy()
                                    archived_quest['status'] = 'dropped'
                                    archived_quest['archived_at'] = self.calendar.get_full_datetime_string()
                                    self.quest_archive.append(archived_quest)
                                    # Update renown: -2 for dropping quest
                                    quest_giver_coords = archived_quest.get('quest_giver_coords')
                                    if quest_giver_coords:
                                        settlement_key = tuple(quest_giver_coords)
                                        self._update_settlement_renown(settlement_key, -2)
                                    self.add_command_message("> D")
                                    self.add_command_message(f"Quest from {leader_name} dropped")
                                    self.current_quest = None
                                    self.quest_item_location = None
                            self.pending_prompt = None
                            command_executed = True
                        elif event.key == pygame.K_ESCAPE:
                            # Close journal
                            self.add_command_message("> ESC")
                            self.pending_prompt = None
                        command_executed = True
                    # Ignore all other keys when prompt is pending
                    if self.pending_prompt:
                        return None
                
                # Handle quest offer (Y/N keys) - ignore all other input when quest is offered
                if self.quest_offer_settlement and not self.current_quest:
                    if event.key == pygame.K_y:
                        self.add_command_message("> Y")
                        # Get leader name first (needed for error message)
                        wb_data = self._find_settlement_worldbuilding_data(self.quest_offer_settlement)
                        leader_name = "Unknown Leader"
                        if wb_data and 'leader' in wb_data and 'name' in wb_data['leader']:
                            leader_name = wb_data['leader']['name']
                        
                        # Accept quest - generate quest data
                        quest = generate_quest(
                            self.quest_offer_settlement,
                            self.map_data,
                            self.map_width,
                            self.map_height,
                            pathfinder=self._astar_path
                        )
                        
                        if quest:
                            
                            # Add leader info to quest
                            quest['leader_name'] = leader_name
                            quest['settlement_name'] = self.quest_offer_settlement.name if self.quest_offer_settlement.name else "Unnamed"
                            
                            # Remove quest_giver (Settlement object) as it's not pickleable - we'll restore it on load
                            quest['quest_giver_x'] = self.quest_offer_settlement.x
                            quest['quest_giver_y'] = self.quest_offer_settlement.y
                            quest['quest_giver_type'] = self.quest_offer_settlement.settlement_type.value
                            quest['quest_giver_coords'] = [self.quest_offer_settlement.x, self.quest_offer_settlement.y]
                            del quest['quest_giver']
                            
                            self.current_quest = quest
                            # Update renown: +2 for accepting quest
                            settlement_key = (self.quest_offer_settlement.x, self.quest_offer_settlement.y)
                            if settlement_key not in self.settlement_renown:
                                self.settlement_renown[settlement_key] = 0
                            self.settlement_renown[settlement_key] += 2
                            self.quest_offer_settlement = None
                            # Show journal dialog instead of messages
                            from journal_dialog import show_journal_dialog
                            import pygame as pg
                            temp_clock = pg.time.Clock()
                            result = show_journal_dialog(self.screen, temp_clock, self.current_quest, self.quest_archive)
                            # Handle drop result if user dropped quest immediately
                            if result == 'drop' and self.current_quest:
                                # Cannot drop quest while in quest location
                                if self.in_quest_location:
                                    self.add_command_message("Cannot drop quest while in quest location")
                                else:
                                    # Archive the quest as dropped
                                    archived_quest = self.current_quest.copy()
                                    archived_quest['status'] = 'dropped'
                                    archived_quest['archived_at'] = self.calendar.get_full_datetime_string()
                                    self.quest_archive.append(archived_quest)
                                    # Update renown: -2 for dropping quest
                                    if not hasattr(self, 'settlement_renown'):
                                        self.settlement_renown = {}
                                    quest_giver_coords = archived_quest.get('quest_giver_coords')
                                    if quest_giver_coords:
                                        settlement_key = tuple(quest_giver_coords)
                                        if settlement_key not in self.settlement_renown:
                                            self.settlement_renown[settlement_key] = 0
                                        self.settlement_renown[settlement_key] = max(0, self.settlement_renown[settlement_key] - 2)
                                    leader_name = self.current_quest.get('leader_name', 'Unknown Leader')
                                    self.add_command_message(f"Quest from {leader_name} dropped")
                                    self.current_quest = None
                                    self.quest_item_location = None
                        else:
                            # Quest generation failed - print console message
                            import sys
                            print(f"{leader_name} says that there are actually no quests at this time. Try again later!", file=sys.stderr, flush=True)
                            self.quest_offer_settlement = None
                        return None
                    elif event.key == pygame.K_n:
                        self.add_command_message("> N")
                        # Decline quest
                        self.add_command_message("Quest declined")
                        self.quest_offer_settlement = None
                        return None
                    # Ignore all other keys when quest offer is pending
                    return None
                
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
                        # Disable map view in quest locations
                        if self.in_quest_location:
                            self.add_command_message("> Map view disabled in quest locations")
                        else:
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
                    elif event.key == pygame.K_j:
                        # Journal - view current quest
                        self.add_command_message("> Journal")
                        # Show journal dialog (with or without quest, to view archive)
                        from journal_dialog import show_journal_dialog
                        import pygame as pg
                        temp_clock = pg.time.Clock()
                        result = show_journal_dialog(self.screen, temp_clock, quest=self.current_quest, quest_archive=self.quest_archive)
                        if result == 'drop' and self.current_quest:
                            # Cannot drop quest while in quest location
                            if self.in_quest_location:
                                self.add_command_message("Cannot drop quest while in quest location")
                            else:
                                # Archive the quest as dropped
                                archived_quest = self.current_quest.copy()
                                archived_quest['status'] = 'dropped'
                                archived_quest['archived_at'] = self.calendar.get_full_datetime_string()
                                self.quest_archive.append(archived_quest)
                                # Update renown: -2 for dropping quest
                                if not hasattr(self, 'settlement_renown'):
                                    self.settlement_renown = {}
                                quest_giver_coords = archived_quest.get('quest_giver_coords')
                                if quest_giver_coords:
                                    settlement_key = tuple(quest_giver_coords)
                                    if settlement_key not in self.settlement_renown:
                                        self.settlement_renown[settlement_key] = 0
                                    self.settlement_renown[settlement_key] = max(0, self.settlement_renown[settlement_key] - 2)
                                leader_name = self.current_quest.get('leader_name', 'Unknown Leader')
                                self.add_command_message(f"Quest from {leader_name} dropped")
                                self.current_quest = None
                                self.quest_item_location = None
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
                    
                    # Get paths directly (avoid double pathfinding)
                    path_to_town = self._get_path(village_x, village_y, town_x, town_y)
                    if not path_to_town:
                        continue  # No path to town, skip this caravan
                    
                    path_to_village = self._get_path(town_x, town_y, village_x, village_y)
                    if not path_to_village:
                        continue  # No return path, skip this caravan
                    
                    # Validate paths - ensure no water tiles
                    path_to_town = self._validate_path(path_to_town)
                    path_to_village = self._validate_path(path_to_village)
                    
                    if path_to_town and path_to_village:
                        caravan = Caravan(village, town, village_x, village_y)
                        caravan.set_path_to_town(path_to_town)
                        caravan.set_path_to_village(path_to_village)
                        
                        # Start journey to town
                        caravan.start_journey_to_town()
                        
                        self.caravans.append(caravan)
                    # Note: If path is not valid, caravan simply doesn't spawn (silent failure)
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
                        
                        # Check for trade good production (silently, no messages)
                        caravan.town.produce_trade_goods()
                        
                        # Check for trade good transfer to liege (silently, no messages)
                        caravan.town.transfer_trade_goods_to_liege()
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
        
        # Check if in quest location
        if self.in_quest_location and self.quest_location_map:
            # Render quest location map
            camera_x_int = int(self.camera_x)
            camera_y_int = int(self.camera_y)
            # Use normal explored/visible tiles for fog of war
            self.renderer.render_map(self.quest_location_map, map_surface, quest_marker=None,
                                    camera_x=camera_x_int, camera_y=camera_y_int, 
                                    settlements=[], explored_tiles=self.explored_tiles, visible_tiles=self.visible_tiles, caravans=[],
                                    is_quest_location=True)
            
            # Draw quest item marker if item hasn't been found
            if self.quest_item_location and not self.current_quest.get('item_found', False):
                item_x, item_y = self.quest_item_location
                import sys
                print(f"DEBUG RENDER: Quest item at ({item_x}, {item_y}), visible_tiles check: {(item_x, item_y) in self.visible_tiles}", file=sys.stderr, flush=True)
                print(f"DEBUG RENDER: visible_tiles count: {len(self.visible_tiles)}, explored_tiles count: {len(self.explored_tiles)}", file=sys.stderr, flush=True)
                print(f"DEBUG RENDER: Player at ({self.player_x}, {self.player_y}), camera at ({camera_x_int}, {camera_y_int})", file=sys.stderr, flush=True)
                # Only render if the tile is visible (not darkened by fog of war)
                if (item_x, item_y) in self.visible_tiles:
                    # Calculate screen position
                    screen_x = (item_x - camera_x_int) * self.tile_size
                    screen_y = (item_y - camera_y_int) * self.tile_size
                    import sys
                    print(f"DEBUG RENDER: Screen position: ({screen_x}, {screen_y}), viewport: {self.map_view_width}x{self.map_view_height}", file=sys.stderr, flush=True)
                    # Draw item marker (golden star/glow)
                    if 0 <= screen_x < self.map_view_width and 0 <= screen_y < self.map_view_height:
                        import sys
                        print(f"DEBUG RENDER: Rendering quest item marker at screen ({screen_x}, {screen_y})", file=sys.stderr, flush=True)
                        center_x = screen_x + self.tile_size // 2
                        center_y = screen_y + self.tile_size // 2
                        # Draw golden glow
                        import math
                        glow_size = self.tile_size // 2
                        for i in range(3):
                            alpha = 200 - i * 50
                            glow_radius = glow_size + i * 2
                            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                            pygame.draw.circle(glow_surface, (255, 215, 0, alpha), (glow_radius, glow_radius), glow_radius)
                            map_surface.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius), special_flags=pygame.BLEND_ALPHA_SDL2)
                        # Draw star/pentagon
                        star_size = self.tile_size // 3
                        star_color = (255, 255, 0)  # Bright yellow
                        points = []
                        for i in range(5):
                            angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                            px = center_x + star_size * math.cos(angle)
                            py = center_y + star_size * math.sin(angle)
                            points.append((px, py))
                        pygame.draw.polygon(map_surface, star_color, points)
                        pygame.draw.polygon(map_surface, (255, 200, 0), points, 2)  # Orange border
        else:
            # Render overland map
            # Convert camera position to integers for rendering (tiles are discrete)
            camera_x_int = int(self.camera_x)
            camera_y_int = int(self.camera_y)
            
            # Mark quest location if we have one (only if quest is active)
            quest_marker = None
            if self.current_quest and not self.in_quest_location:
                quest_status = self.current_quest.get('quest_status', 'active')
                if quest_status == 'active':
                    quest_x, quest_y = self.current_quest['quest_coordinates']
                    quest_marker = (quest_x, quest_y)
            
            self.renderer.render_map(self.map_data, map_surface, quest_marker=quest_marker,
                                    camera_x=camera_x_int, camera_y=camera_y_int, 
                                    settlements=self.settlements, explored_tiles=self.explored_tiles, 
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
        y_pos = 70
        if self.in_quest_location:
            terrain_text = "Terrain: Quest Location"
            terrain_surface = font.render(terrain_text, True, (255, 255, 100))  # Yellow
            self.screen.blit(terrain_surface, (self.map_view_width + 10, y_pos))
            y_pos += 30
        elif 0 <= self.player_y < self.map_height and 0 <= self.player_x < self.map_width:
            current_terrain = self.map_data[self.player_y][self.player_x]
            terrain_type = current_terrain.terrain_type
            # Format terrain type name (capitalize and replace underscores)
            terrain_name = terrain_type.value.replace('_', ' ').title()
            terrain_text = f"Terrain: {terrain_name}"
            terrain_surface = font.render(terrain_text, True, (200, 200, 255))  # Light blue
            self.screen.blit(terrain_surface, (self.map_view_width + 10, y_pos))
            y_pos += 30
        
        # Display quest status
        if self.current_quest:
            quest_status = self.current_quest.get('quest_status', 'active')
            if quest_status == 'item_found':
                # Show "active, pending return to {settlement}"
                settlement_name = self.current_quest.get('settlement_name', 'settlement')
                quest_text = f"Quest: Active, pending return to {settlement_name}"
            elif quest_status == 'active':
                quest_text = "Quest: Active"
            else:
                quest_text = f"Quest: {quest_status.title()}"
            quest_surface = font.render(quest_text, True, (255, 200, 100))  # Orange
            self.screen.blit(quest_surface, (self.map_view_width + 10, y_pos))
        else:
            quest_text = "Quest: None"
            quest_surface = font.render(quest_text, True, (150, 150, 150))  # Gray
            self.screen.blit(quest_surface, (self.map_view_width + 10, y_pos))
        y_pos += 30
        
        # Display settlement information if player is on a settlement
        # Create a clipping surface for scrollable content
        status_content_start_y = y_pos
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
            
            # Get worldbuilding data
            wb_data = self._find_settlement_worldbuilding_data(settlement)
            
            # Build formatted description based on settlement type
            desc_font = pygame.font.Font(None, 22)
            formatted_lines = []
            
            # Settlement name (header)
            formatted_lines.append((settlement_name, title_font, (255, 255, 0)))  # Yellow
            
            # Get description (tone and flavor)
            if wb_data and 'description' in wb_data:
                formatted_lines.append((wb_data['description'], desc_font, (200, 200, 200)))
            
            # Get leader info
            leader_name = "Unknown Leader"
            leader_bio = ""
            if wb_data and 'leader' in wb_data:
                leader = wb_data['leader']
                if 'name' in leader:
                    leader_name = leader['name']
                if 'biography' in leader:
                    leader_bio = leader['biography']
            
            # Format based on settlement type
            if settlement.settlement_type == SettlementType.VILLAGE:
                # Village format: "Their leader is {leader name}, who {leader description}."
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # Resource and town relationship
                resource = settlement.supplies_resource or "Unknown"
                town_name = settlement.vassal_to.name if settlement.vassal_to and settlement.vassal_to.name else "Unknown"
                resource_text = f"This village sends {resource} to {town_name} in return for protection."
                formatted_lines.append((resource_text, desc_font, (200, 200, 200)))
            
            elif settlement.settlement_type == SettlementType.TOWN:
                # Town format: "Their leader is {leader name}, who {leader description}. {leader name} kneels to {city leader} of {city name} and sends trade goods as tribute (or "kneels to no one" if it's a free city.)"
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # City relationship
                if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.CITY:
                    city = settlement.vassal_to
                    city_name = city.name if city.name else "Unknown"
                    # Get city leader name
                    city_wb_data = self._find_settlement_worldbuilding_data(city)
                    city_leader_name = "Unknown Leader"
                    if city_wb_data and 'leader' in city_wb_data and 'name' in city_wb_data['leader']:
                        city_leader_name = city_wb_data['leader']['name']
                    kneel_text = f"{leader_name} kneels to {city_leader_name} of {city_name} and sends trade goods as tribute."
                else:
                    kneel_text = f"{leader_name} kneels to no one."
                formatted_lines.append((kneel_text, desc_font, (200, 200, 200)))
                
                # Village resources
                if settlement.vassal_villages:
                    village_list = []
                    for village in settlement.vassal_villages:
                        village_name = village.name if village.name else "Unnamed"
                        resource = village.supplies_resource or "Unknown"
                        village_list.append(f"{village_name} ({resource})")
                    villages_text = f"This town receives resources from several villages: {', '.join(village_list)}."
                    formatted_lines.append((villages_text, desc_font, (200, 200, 200)))
            
            elif settlement.settlement_type == SettlementType.CITY:
                # City format: "Their leader is {leader name}, who {description}."
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # Towns under yoke
                if settlement.vassal_towns:
                    town_list = []
                    for town in settlement.vassal_towns:
                        town_name = town.name if town.name else "Unnamed"
                        town_list.append(town_name)
                    towns_text = f"This city has the following towns under its yoke, and extracts tribute in trade goods from each: {', '.join(town_list)}."
                    formatted_lines.append((towns_text, desc_font, (200, 200, 200)))
            
            # Renown statement (without number)
            settlement_key = (settlement.x, settlement.y)
            if not hasattr(self, 'settlement_renown'):
                self.settlement_renown = {}
            if settlement_key not in self.settlement_renown:
                self.settlement_renown[settlement_key] = 0
            renown = max(0, self.settlement_renown.get(settlement_key, 0))
            renown_description = self._get_renown_description(renown)
            formatted_lines.append((renown_description, desc_font, (255, 255, 150)))  # Yellow
            
            # Render all formatted lines with word wrapping
            for line_text, line_font, line_color in formatted_lines:
                # Word wrap the line
                words = line_text.split()
                lines = []
                current_line = []
                current_width = 0
                max_width = self.status_width - 30
                
                for word in words:
                    word_surface = line_font.render(word + ' ', True, line_color)
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
                
                # Render each wrapped line
                for line in lines:
                    line_surface = line_font.render(line, True, line_color)
                    content_surface.blit(line_surface, (10, y_offset))
                    y_offset += 22 if line_font == desc_font else 30
                y_offset += 5  # Small spacing between sections
            
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
        else:
            # Draw prompt-specific messages
            if self.pending_prompt == 'quest_offer' and self.quest_offer_settlement:
                wb_data = self._find_settlement_worldbuilding_data(self.quest_offer_settlement)
                leader_name = "Unknown Leader"
                if wb_data and 'leader' in wb_data and 'name' in wb_data['leader']:
                    leader_name = wb_data['leader']['name']
                prompt_text = f"{leader_name}: Will you help us by completing a quest? (Y/N)"
                prompt_surface = font.render(prompt_text, True, (255, 255, 100))  # Yellow
                self.screen.blit(prompt_surface, (10, y_offset))
            elif self.pending_prompt == 'journal':
                if self.current_quest:
                    # Display quest info
                    quest_lines = [
                        "=== JOURNAL ===",
                        f"Quest from: {self.current_quest.get('leader_name', 'Unknown')}",
                        f"Settlement: {self.current_quest.get('settlement_name', 'Unknown')}",
                        f"Type: {self.current_quest.get('quest_type', 'Unknown')}",
                        f"Location: {self.current_quest.get('location_terrain_type', 'Unknown')}",
                        f"Direction: {self.current_quest.get('quest_direction', 'Unknown')}",
                        f"Distance: {self.current_quest.get('distance_days', 0):.1f} days",
                        "",
                        "Drop quest? (D)"
                    ]
                    for line in quest_lines:
                        if line:
                            line_surface = font.render(line, True, (200, 200, 200))
                            self.screen.blit(line_surface, (10, y_offset))
                            y_offset += line_height
                else:
                    prompt_text = "No active quest. (ESC to close)"
                    prompt_surface = font.render(prompt_text, True, (150, 150, 150))
                    self.screen.blit(prompt_surface, (10, y_offset))
        
        pygame.display.flip()
    
    def _enter_quest_location(self, approach_direction: str = None):
        """
        Enter the quest location (zoomed-in map).
        
        Args:
            approach_direction: Direction player is approaching from ('north', 'south', 'east', 'west')
                                If None, will try to determine from quest_direction (fallback)
        """
        if not self.current_quest:
            return
        
        quest_x, quest_y = self.current_quest['quest_coordinates']
        self.in_quest_location = True
        
        # Determine approach direction
        if approach_direction is None:
            # Fallback: try to determine from player's position relative to quest location
            # This shouldn't normally happen, but handle it gracefully
            quest_dir = self.current_quest.get('quest_direction', 'north')
            # Convert to cardinal if needed (should already be cardinal, but just in case)
            if quest_dir in ['north', 'south', 'east', 'west']:
                # Invert: if quest is north of settlement, player approaches from south
                direction_map = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
                approach_direction = direction_map.get(quest_dir, 'south')
            else:
                approach_direction = 'south'  # Default fallback
        
        # Generate quest location map to fill the entire viewport
        # Calculate size based on viewport dimensions
        viewport_width_tiles = self.map_view_width // self.tile_size
        viewport_height_tiles = self.map_view_height // self.tile_size
        # Use the larger dimension to ensure it fills the viewport
        # This ensures the map is at least as large as the viewport in both dimensions
        self.quest_location_size = max(viewport_width_tiles, viewport_height_tiles)
        
        # Get terrain type and description from quest location
        location_terrain_type_str = self.current_quest.get('location_terrain_type', 'grassland')
        # Use original location description for map lookup (before item text was appended)
        location_description = self.current_quest.get('original_location_description') or self.current_quest.get('location_description', 'location')
        
        # Generate quest location map based on description
        from quest_location_maps import generate_quest_location_map
        self.quest_location_map = generate_quest_location_map(
            location_description, 
            location_terrain_type_str, 
            self.quest_location_size
        )
        
        # Set player position based on approach direction (cardinal directions only)
        # approach_direction is the direction the player was MOVING when they entered
        # If player was moving north, they're approaching from south → spawn at bottom (south edge)
        # If player was moving south, they're approaching from north → spawn at top (north edge)
        # If player was moving east, they're approaching from west → spawn at left (west edge)
        # If player was moving west, they're approaching from east → spawn at right (east edge)
        approach = approach_direction  # Use the actual movement direction
        
        if approach == 'north':
            # Traveling north (approaching from south), spawn at bottom (south edge), centered horizontally
            self.player_x = self.quest_location_size // 2
            self.player_y = self.quest_location_size - 1
        elif approach == 'south':
            # Traveling south (approaching from north), spawn at top (north edge), centered horizontally
            self.player_x = self.quest_location_size // 2
            self.player_y = 0
        elif approach == 'east':
            # Traveling east (approaching from west), spawn on left side (west edge), centered vertically
            self.player_x = 0
            self.player_y = self.quest_location_size // 2
        elif approach == 'west':
            # Traveling west (approaching from east), spawn on right side (east edge), centered vertically
            self.player_x = self.quest_location_size - 1
            self.player_y = self.quest_location_size // 2
        else:
            # Fallback: default to bottom (south edge)
            self.player_x = self.quest_location_size // 2
            self.player_y = self.quest_location_size - 1
        
        self.quest_location_approach_direction = approach
        
        # Place quest item on the map if this is a fetch quest
        import sys
        print(f"DEBUG ENTER: _enter_quest_location called. current_quest exists: {self.current_quest is not None}", file=sys.stderr, flush=True)
        if self.current_quest:
            print(f"DEBUG ENTER: quest_type: {self.current_quest.get('quest_type')}, target_item: {self.current_quest.get('target_item')}", file=sys.stderr, flush=True)
        if self.current_quest and self.current_quest.get('quest_type') == 'fetch' and self.current_quest.get('target_item'):
            import sys
            print(f"DEBUG: Placing quest item for fetch quest. target_item: {self.current_quest.get('target_item')}", file=sys.stderr, flush=True)
            # Restore item location from saved quest if available, otherwise find a new one
            saved_item_location = self.current_quest.get('item_location')
            if saved_item_location and not self.current_quest.get('item_found', False):
                # Restore saved location
                self.quest_item_location = tuple(saved_item_location)
                import sys
                print(f"DEBUG: Restored quest item location from save: {self.quest_item_location}", file=sys.stderr, flush=True)
            else:
                # Find a good location for the item
                self.quest_item_location = self._find_quest_item_location(self.quest_location_map, self.quest_location_size)
                if self.quest_item_location:
                    # Save the location in the quest
                    self.current_quest['item_location'] = list(self.quest_item_location)
                    import sys
                    print(f"DEBUG: Found new quest item location: {self.quest_item_location}", file=sys.stderr, flush=True)
                else:
                    import sys
                    print(f"DEBUG: WARNING - Could not find a location for quest item!", file=sys.stderr, flush=True)
            
            # Mark item location as explored and visible so it can be rendered and touched
            if self.quest_item_location:
                self.explored_tiles.add(self.quest_item_location)
                self.visible_tiles.add(self.quest_item_location)
                import sys
                print(f"DEBUG: Marked quest item location as explored and visible: {self.quest_item_location}", file=sys.stderr, flush=True)
            else:
                import sys
                print(f"DEBUG: WARNING - quest_item_location is None!", file=sys.stderr, flush=True)
        else:
            import sys
            print(f"DEBUG: Not a fetch quest or missing target_item. quest_type: {self.current_quest.get('quest_type') if self.current_quest else None}, target_item: {self.current_quest.get('target_item') if self.current_quest else None}", file=sys.stderr, flush=True)
            self.quest_item_location = None
        
        # Mark player position as explored and update visibility
        self.explored_tiles.add((self.player_x, self.player_y))
        self._update_visibility()
        
        self._update_camera()
    
    def _find_quest_item_location(self, map_data: List[List[Terrain]], map_size: int) -> Optional[Tuple[int, int]]:
        """
        Find a good location for the quest item on the quest location map.
        Prefers locations inside structures (GRASSLAND tiles adjacent to MOUNTAIN).
        
        Returns:
            (x, y) coordinates or None if no suitable location found
        """
        import random
        from terrain import TerrainType
        
        # First, try to find GRASSLAND tiles inside structures (adjacent to MOUNTAIN)
        structure_interior = []
        for y in range(1, map_size - 1):
            for x in range(1, map_size - 1):
                terrain = map_data[y][x]
                # Must be passable (GRASSLAND)
                if terrain.terrain_type == TerrainType.GRASSLAND and terrain.can_move_through():
                    # Check if adjacent to MOUNTAIN (inside a structure)
                    is_inside_structure = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < map_size and 0 <= ny < map_size:
                                adj_terrain = map_data[ny][nx]
                                if adj_terrain.terrain_type == TerrainType.MOUNTAIN:
                                    is_inside_structure = True
                                    break
                        if is_inside_structure:
                            break
                    if is_inside_structure:
                        structure_interior.append((x, y))
        
        # If we found structure interiors, prefer those
        if structure_interior:
            # Prefer locations away from edges and player spawn
            player_spawn_x = self.player_x
            player_spawn_y = self.player_y
            
            # Score locations (prefer center, away from spawn)
            scored_locations = []
            for x, y in structure_interior:
                # Distance from center
                center_x, center_y = map_size // 2, map_size // 2
                dist_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                # Distance from spawn
                dist_from_spawn = ((x - player_spawn_x) ** 2 + (y - player_spawn_y) ** 2) ** 0.5
                # Prefer locations that are near center but not too close to spawn
                score = dist_from_center * 0.5 + dist_from_spawn * 1.5
                scored_locations.append((score, x, y))
            
            # Sort by score (lower is better) and pick from top candidates
            scored_locations.sort()
            if scored_locations:
                # Pick randomly from top 5 candidates
                top_candidates = scored_locations[:min(5, len(scored_locations))]
                _, item_x, item_y = random.choice(top_candidates)
                return (item_x, item_y)
        
        # Fallback: find any passable location away from edges
        passable_locations = []
        for y in range(2, map_size - 2):
            for x in range(2, map_size - 2):
                terrain = map_data[y][x]
                if terrain.can_move_through():
                    passable_locations.append((x, y))
        
        if passable_locations:
            # Prefer center locations
            center_x, center_y = map_size // 2, map_size // 2
            scored = []
            for x, y in passable_locations:
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                scored.append((dist, x, y))
            scored.sort()
            if scored:
                _, item_x, item_y = random.choice(scored[:min(10, len(scored))])
                return (item_x, item_y)
        
        # Last resort: any passable tile
        for y in range(1, map_size - 1):
            for x in range(1, map_size - 1):
                if map_data[y][x].can_move_through():
                    return (x, y)
        
        return None
    
    def _exit_quest_location(self):
        """Exit the quest location and return to overland map."""
        if not self.in_quest_location:
            return
        
        # Get quest coordinates to return to
        quest_x, quest_y = self.current_quest['quest_coordinates'] if self.current_quest else (self.player_x, self.player_y)
        
        # Return to overland map at quest coordinates (don't complete quest yet)
        self.in_quest_location = False
        self.quest_location_map = None
        self.quest_location_size = 0
        self.quest_location_approach_direction = None
        
        # Restore player position on overland map
        self.player_x = quest_x
        self.player_y = quest_y
        
        # Mark position as explored and visible
        self.explored_tiles.add((self.player_x, self.player_y))
        self._update_visibility()
        
        # Update camera to center on player
        self._update_camera()
        
        # Add message about leaving quest area
        self.add_command_message("Leaving quest location...")
    
    def _update_settlement_renown(self, settlement_key: tuple, delta: int) -> None:
        """
        Update renown for a settlement, ensuring it never goes below 0.
        
        Args:
            settlement_key: Tuple of (x, y) coordinates for the settlement
            delta: Change in renown (positive or negative)
        """
        if not hasattr(self, 'settlement_renown'):
            self.settlement_renown = {}
        if settlement_key not in self.settlement_renown:
            self.settlement_renown[settlement_key] = 0
        self.settlement_renown[settlement_key] = max(0, self.settlement_renown[settlement_key] + delta)
    
    def _get_renown_description(self, renown: int) -> str:
        """
        Get a description of the player's renown level with a settlement.
        
        Args:
            renown: The renown value
            
        Returns:
            Description string
        """
        # Ensure renown is never negative
        renown = max(0, renown)
        if renown < 6:
            return "You are practically a stranger"
        elif renown <= 10:
            return "You are a friend"
        elif renown <= 15:
            return "You are an honorary clan member"
        else:
            return "You are a local hero"


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
        
        # Check if in quest location
        if self.in_quest_location and self.quest_location_map:
            # Render quest location map
            camera_x_int = int(self.camera_x)
            camera_y_int = int(self.camera_y)
            # Use normal explored/visible tiles for fog of war
            self.renderer.render_map(self.quest_location_map, map_surface, quest_marker=None,
                                    camera_x=camera_x_int, camera_y=camera_y_int, 
                                    settlements=[], explored_tiles=self.explored_tiles, visible_tiles=self.visible_tiles, caravans=[],
                                    is_quest_location=True)
            
            # Draw quest item marker if item hasn't been found
            if self.quest_item_location and not self.current_quest.get('item_found', False):
                item_x, item_y = self.quest_item_location
                import sys
                print(f"DEBUG RENDER: Quest item at ({item_x}, {item_y}), visible_tiles check: {(item_x, item_y) in self.visible_tiles}", file=sys.stderr, flush=True)
                print(f"DEBUG RENDER: visible_tiles count: {len(self.visible_tiles)}, explored_tiles count: {len(self.explored_tiles)}", file=sys.stderr, flush=True)
                print(f"DEBUG RENDER: Player at ({self.player_x}, {self.player_y}), camera at ({camera_x_int}, {camera_y_int})", file=sys.stderr, flush=True)
                # Only render if the tile is visible (not darkened by fog of war)
                if (item_x, item_y) in self.visible_tiles:
                    # Calculate screen position
                    screen_x = (item_x - camera_x_int) * self.tile_size
                    screen_y = (item_y - camera_y_int) * self.tile_size
                    import sys
                    print(f"DEBUG RENDER: Screen position: ({screen_x}, {screen_y}), viewport: {self.map_view_width}x{self.map_view_height}", file=sys.stderr, flush=True)
                    # Draw item marker (golden star/glow)
                    if 0 <= screen_x < self.map_view_width and 0 <= screen_y < self.map_view_height:
                        import sys
                        print(f"DEBUG RENDER: Rendering quest item marker at screen ({screen_x}, {screen_y})", file=sys.stderr, flush=True)
                        center_x = screen_x + self.tile_size // 2
                        center_y = screen_y + self.tile_size // 2
                        # Draw golden glow
                        import math
                        glow_size = self.tile_size // 2
                        for i in range(3):
                            alpha = 200 - i * 50
                            glow_radius = glow_size + i * 2
                            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                            pygame.draw.circle(glow_surface, (255, 215, 0, alpha), (glow_radius, glow_radius), glow_radius)
                            map_surface.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius), special_flags=pygame.BLEND_ALPHA_SDL2)
                        # Draw star/pentagon
                        star_size = self.tile_size // 3
                        star_color = (255, 255, 0)  # Bright yellow
                        points = []
                        for i in range(5):
                            angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                            px = center_x + star_size * math.cos(angle)
                            py = center_y + star_size * math.sin(angle)
                            points.append((px, py))
                        pygame.draw.polygon(map_surface, star_color, points)
                        pygame.draw.polygon(map_surface, (255, 200, 0), points, 2)  # Orange border
        else:
            # Render overland map
            # Convert camera position to integers for rendering (tiles are discrete)
            camera_x_int = int(self.camera_x)
            camera_y_int = int(self.camera_y)
            
            # Mark quest location if we have one (only if quest is active)
            quest_marker = None
            if self.current_quest and not self.in_quest_location:
                quest_status = self.current_quest.get('quest_status', 'active')
                if quest_status == 'active':
                    quest_x, quest_y = self.current_quest['quest_coordinates']
                    quest_marker = (quest_x, quest_y)
            
            self.renderer.render_map(self.map_data, map_surface, quest_marker=quest_marker,
                                    camera_x=camera_x_int, camera_y=camera_y_int, 
                                    settlements=self.settlements, explored_tiles=self.explored_tiles, 
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
        y_pos = 70
        if self.in_quest_location:
            terrain_text = "Terrain: Quest Location"
            terrain_surface = font.render(terrain_text, True, (255, 255, 100))  # Yellow
            self.screen.blit(terrain_surface, (self.map_view_width + 10, y_pos))
            y_pos += 30
        elif 0 <= self.player_y < self.map_height and 0 <= self.player_x < self.map_width:
            current_terrain = self.map_data[self.player_y][self.player_x]
            terrain_type = current_terrain.terrain_type
            # Format terrain type name (capitalize and replace underscores)
            terrain_name = terrain_type.value.replace('_', ' ').title()
            terrain_text = f"Terrain: {terrain_name}"
            terrain_surface = font.render(terrain_text, True, (200, 200, 255))  # Light blue
            self.screen.blit(terrain_surface, (self.map_view_width + 10, y_pos))
            y_pos += 30
        
        # Display quest status
        if self.current_quest:
            quest_status = self.current_quest.get('quest_status', 'active')
            if quest_status == 'item_found':
                # Show "active, pending return to {settlement}"
                settlement_name = self.current_quest.get('settlement_name', 'settlement')
                quest_text = f"Quest: Active, pending return to {settlement_name}"
            elif quest_status == 'active':
                quest_text = "Quest: Active"
            else:
                quest_text = f"Quest: {quest_status.title()}"
            quest_surface = font.render(quest_text, True, (255, 200, 100))  # Orange
            self.screen.blit(quest_surface, (self.map_view_width + 10, y_pos))
        else:
            quest_text = "Quest: None"
            quest_surface = font.render(quest_text, True, (150, 150, 150))  # Gray
            self.screen.blit(quest_surface, (self.map_view_width + 10, y_pos))
        y_pos += 30
        
        # Display settlement information if player is on a settlement
        # Create a clipping surface for scrollable content
        status_content_start_y = y_pos
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
            
            # Get worldbuilding data
            wb_data = self._find_settlement_worldbuilding_data(settlement)
            
            # Build formatted description based on settlement type
            desc_font = pygame.font.Font(None, 22)
            formatted_lines = []
            
            # Settlement name (header)
            formatted_lines.append((settlement_name, title_font, (255, 255, 0)))  # Yellow
            
            # Get description (tone and flavor)
            if wb_data and 'description' in wb_data:
                formatted_lines.append((wb_data['description'], desc_font, (200, 200, 200)))
            
            # Get leader info
            leader_name = "Unknown Leader"
            leader_bio = ""
            if wb_data and 'leader' in wb_data:
                leader = wb_data['leader']
                if 'name' in leader:
                    leader_name = leader['name']
                if 'biography' in leader:
                    leader_bio = leader['biography']
            
            # Format based on settlement type
            if settlement.settlement_type == SettlementType.VILLAGE:
                # Village format: "Their leader is {leader name}, who {leader description}."
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # Resource and town relationship
                resource = settlement.supplies_resource or "Unknown"
                town_name = settlement.vassal_to.name if settlement.vassal_to and settlement.vassal_to.name else "Unknown"
                resource_text = f"This village sends {resource} to {town_name} in return for protection."
                formatted_lines.append((resource_text, desc_font, (200, 200, 200)))
            
            elif settlement.settlement_type == SettlementType.TOWN:
                # Town format: "Their leader is {leader name}, who {leader description}. {leader name} kneels to {city leader} of {city name} and sends trade goods as tribute (or "kneels to no one" if it's a free city.)"
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # City relationship
                if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.CITY:
                    city = settlement.vassal_to
                    city_name = city.name if city.name else "Unknown"
                    # Get city leader name
                    city_wb_data = self._find_settlement_worldbuilding_data(city)
                    city_leader_name = "Unknown Leader"
                    if city_wb_data and 'leader' in city_wb_data and 'name' in city_wb_data['leader']:
                        city_leader_name = city_wb_data['leader']['name']
                    kneel_text = f"{leader_name} kneels to {city_leader_name} of {city_name} and sends trade goods as tribute."
                else:
                    kneel_text = f"{leader_name} kneels to no one."
                formatted_lines.append((kneel_text, desc_font, (200, 200, 200)))
                
                # Village resources
                if settlement.vassal_villages:
                    village_list = []
                    for village in settlement.vassal_villages:
                        village_name = village.name if village.name else "Unnamed"
                        resource = village.supplies_resource or "Unknown"
                        village_list.append(f"{village_name} ({resource})")
                    villages_text = f"This town receives resources from several villages: {', '.join(village_list)}."
                    formatted_lines.append((villages_text, desc_font, (200, 200, 200)))
            
            elif settlement.settlement_type == SettlementType.CITY:
                # City format: "Their leader is {leader name}, who {description}."
                leader_text = f"Their leader is {leader_name}, who {leader_bio}." if leader_bio else f"Their leader is {leader_name}."
                formatted_lines.append((leader_text, desc_font, (200, 200, 200)))
                
                # Towns under yoke
                if settlement.vassal_towns:
                    town_list = []
                    for town in settlement.vassal_towns:
                        town_name = town.name if town.name else "Unnamed"
                        town_list.append(town_name)
                    towns_text = f"This city has the following towns under its yoke, and extracts tribute in trade goods from each: {', '.join(town_list)}."
                    formatted_lines.append((towns_text, desc_font, (200, 200, 200)))
            
            # Renown statement (without number)
            settlement_key = (settlement.x, settlement.y)
            if not hasattr(self, 'settlement_renown'):
                self.settlement_renown = {}
            if settlement_key not in self.settlement_renown:
                self.settlement_renown[settlement_key] = 0
            renown = max(0, self.settlement_renown.get(settlement_key, 0))
            renown_description = self._get_renown_description(renown)
            formatted_lines.append((renown_description, desc_font, (255, 255, 150)))  # Yellow
            
            # Render all formatted lines with word wrapping
            for line_text, line_font, line_color in formatted_lines:
                # Word wrap the line
                words = line_text.split()
                lines = []
                current_line = []
                current_width = 0
                max_width = self.status_width - 30
                
                for word in words:
                    word_surface = line_font.render(word + ' ', True, line_color)
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
                
                # Render each wrapped line
                for line in lines:
                    line_surface = line_font.render(line, True, line_color)
                    content_surface.blit(line_surface, (10, y_offset))
                    y_offset += 22 if line_font == desc_font else 30
                y_offset += 5  # Small spacing between sections
            
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
        else:
            # Draw prompt-specific messages
            if self.pending_prompt == 'quest_offer' and self.quest_offer_settlement:
                wb_data = self._find_settlement_worldbuilding_data(self.quest_offer_settlement)
                leader_name = "Unknown Leader"
                if wb_data and 'leader' in wb_data and 'name' in wb_data['leader']:
                    leader_name = wb_data['leader']['name']
                prompt_text = f"{leader_name}: Will you help us by completing a quest? (Y/N)"
                prompt_surface = font.render(prompt_text, True, (255, 255, 100))  # Yellow
                self.screen.blit(prompt_surface, (10, y_offset))
            elif self.pending_prompt == 'journal':
                if self.current_quest:
                    # Display quest info
                    quest_lines = [
                        "=== JOURNAL ===",
                        f"Quest from: {self.current_quest.get('leader_name', 'Unknown')}",
                        f"Settlement: {self.current_quest.get('settlement_name', 'Unknown')}",
                        f"Type: {self.current_quest.get('quest_type', 'Unknown')}",
                        f"Location: {self.current_quest.get('location_terrain_type', 'Unknown')}",
                        f"Direction: {self.current_quest.get('quest_direction', 'Unknown')}",
                        f"Distance: {self.current_quest.get('distance_days', 0):.1f} days",
                        "",
                        "Drop quest? (D)"
                    ]
                    for line in quest_lines:
                        if line:
                            line_surface = font.render(line, True, (200, 200, 200))
                            self.screen.blit(line_surface, (10, y_offset))
                            y_offset += line_height
                else:
                    prompt_text = "No active quest. (ESC to close)"
                    prompt_surface = font.render(prompt_text, True, (150, 150, 150))
                    self.screen.blit(prompt_surface, (10, y_offset))
        
        pygame.display.flip()
    
    def _exit_quest_location(self):
        """Exit the quest location and return to overland map."""
        if not self.in_quest_location:
            return
        
        # Get quest coordinates to return to
        quest_x, quest_y = self.current_quest['quest_coordinates'] if self.current_quest else (self.player_x, self.player_y)
        
        # Return to overland map at quest coordinates (don't complete quest yet)
        self.in_quest_location = False
        self.quest_location_map = None
        self.quest_location_size = 0
        self.quest_location_approach_direction = None
        
        # Restore player position on overland map
        self.player_x = quest_x
        self.player_y = quest_y
        
        # Mark position as explored and visible
        self.explored_tiles.add((self.player_x, self.player_y))
        self._update_visibility()
        
        # Update camera to center on player
        self._update_camera()
        
        # Add message about leaving quest area
        self.add_command_message("Leaving quest location...")
    
    def _update_settlement_renown(self, settlement_key: tuple, delta: int) -> None:
        """
        Update renown for a settlement, ensuring it never goes below 0.
        
        Args:
            settlement_key: Tuple of (x, y) coordinates for the settlement
            delta: Change in renown (positive or negative)
        """
        if not hasattr(self, 'settlement_renown'):
            self.settlement_renown = {}
        if settlement_key not in self.settlement_renown:
            self.settlement_renown[settlement_key] = 0
        self.settlement_renown[settlement_key] = max(0, self.settlement_renown[settlement_key] + delta)
    
    def _get_renown_description(self, renown: int) -> str:
        """
        Get a description of the player's renown level with a settlement.
        
        Args:
            renown: The renown value
            
        Returns:
            Description string
        """
        # Ensure renown is never negative
        renown = max(0, renown)
        if renown < 6:
            return "You are practically a stranger"
        elif renown <= 10:
            return "You are a friend"
        elif renown <= 15:
            return "You are an honorary clan member"
        else:
            return "You are a local hero"

