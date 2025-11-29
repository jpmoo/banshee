"""
Map rendering system using pygame.
Displays the map with colored tiles representing different terrain types.
"""
import pygame
import math
import os
import json
from typing import List, Optional, Dict, Tuple
from terrain import Terrain, TerrainType
from settlements import Settlement, SettlementType


class MapRenderer:
    """Renders the map to a pygame surface."""
    
    def __init__(self, tile_size: int = 32, tileset_path: Optional[str] = None, use_tileset: bool = True):
        """
        Initialize the map renderer.
        
        Args:
            tile_size: Size of each tile in pixels for display (will scale tileset to this size)
            tileset_path: Path to the tileset image file (None for color-based rendering)
            use_tileset: Whether to use tileset (False for color-based rendering)
        """
        self.tile_size = tile_size  # Display tile size
        self.tileset = None
        self.tileset_path = tileset_path
        self.json_path = None  # Path to JSON mappings file
        self.use_tileset = use_tileset
        self.tileset_tile_size = None  # Native tileset tile size (will be detected)
        self.tiles_per_row = 0  # Will be calculated when tileset is loaded
        self.transparency_color = None  # RGB color to make transparent (chroma key)
        
        # Load tileset if available and enabled
        if self.use_tileset and self.tileset_path:
            self._load_tileset()
        else:
            self.use_tileset = False
            print("Using color-based rendering (no tileset)")
        
        # Load terrain to tile mappings from file, or use defaults
        if self.use_tileset:
            self.terrain_tile_map = self._load_tile_mappings()
        else:
            self.terrain_tile_map = {}
    
    def switch_tileset(self, tileset_info: Optional[Dict]):
        """
        Switch to a different tileset or color-based rendering.
        
        Args:
            tileset_info: Dictionary with 'type' ('tileset' or 'color'), 'path' (PNG), and 'json_path' (JSON)
        """
        if tileset_info is None or tileset_info.get('type') == 'color':
            # Switch to color-based rendering
            self.use_tileset = False
            self.tileset = None
            self.tileset_path = None
            self.json_path = None
            self.terrain_tile_map = {}
            print("Switched to color-based rendering")
        else:
            # Switch to tileset
            new_path = tileset_info.get('path')  # PNG path
            json_path = tileset_info.get('json_path')  # JSON path
            
            if new_path and os.path.exists(new_path):
                if json_path and os.path.exists(json_path):
                    self.use_tileset = True
                    self.tileset_path = new_path
                    self.json_path = json_path
                    self._load_tileset()
                    self.terrain_tile_map = self._load_tile_mappings()
                    print(f"Switched to tileset: {tileset_info.get('name', 'Unknown')}")
                else:
                    print(f"Error: Tileset JSON file not found: {json_path}")
            else:
                print(f"Error: Tileset PNG file not found: {new_path}")
    
    def _load_tileset(self):
        """Load the tileset image and detect its native tile size."""
        try:
            if os.path.exists(self.tileset_path):
                # Load with alpha channel preserved
                self.tileset = pygame.image.load(self.tileset_path).convert_alpha()
                tileset_width = self.tileset.get_width()
                tileset_height = self.tileset.get_height()
                
                # First, try to infer from filename (most reliable)
                import re
                detected_size = None
                match = re.search(r'(\d+)x\d+', self.tileset_path, re.IGNORECASE)
                if match:
                    filename_size = int(match.group(1))
                    # Verify that the detected size from filename works
                    if tileset_width % filename_size == 0 and tileset_height % filename_size == 0:
                        detected_size = filename_size
                
                # If filename didn't help, try to detect native tile size (common sizes: 8, 16, 32, 64)
                if detected_size is None:
                    possible_sizes = [16, 32, 64, 8]  # Prefer larger sizes first
                    for size in possible_sizes:
                        if tileset_width % size == 0 and tileset_height % size == 0:
                            # Check if it looks like a reasonable grid (at least 4 tiles)
                            if tileset_width // size >= 4:
                                detected_size = size
                                break
                
                # If we still couldn't detect, use 16 as default
                if detected_size is None:
                    detected_size = 16  # Default assumption
                
                self.tileset_tile_size = detected_size
                self.tiles_per_row = tileset_width // self.tileset_tile_size
                tiles_per_col = tileset_height // self.tileset_tile_size
                
                print(f"Loaded tileset: {self.tileset_path}")
                print(f"  Dimensions: {tileset_width}x{tileset_height} pixels")
                print(f"  Native tile size: {self.tileset_tile_size}x{self.tileset_tile_size}")
                print(f"  Grid: {self.tiles_per_row} tiles wide x {tiles_per_col} tiles tall")
                print(f"  Total tiles: {self.tiles_per_row * tiles_per_col}")
                if self.tileset_tile_size != self.tile_size:
                    print(f"  Scaling tiles from {self.tileset_tile_size}px to {self.tile_size}px for display")
            else:
                print(f"Tileset not found: {self.tileset_path}, using colored rectangles")
                self.tileset = None
                self.tileset_tile_size = None
        except Exception as e:
            print(f"Error loading tileset: {e}")
            self.tileset = None
            self.tileset_tile_size = None
    
    def _load_tile_mappings(self) -> dict:
        """
        Load terrain to tile mappings from JSON file.
        Uses json_path if available, otherwise derives from tileset_path.
        
        Returns:
            Dictionary mapping TerrainType to list of (tile_x, tile_y) tuples (single or double layer)
        """
        # Use json_path if set (from tileset selection), otherwise derive from PNG path
        if self.json_path and os.path.exists(self.json_path):
            mappings_file = self.json_path
        elif self.tileset_path:
            # Derive JSON path from PNG path
            tilesets_dir = "tilesets"
            png_basename = os.path.splitext(os.path.basename(self.tileset_path))[0]
            json_filename = png_basename + ".json"
            mappings_file = os.path.join(tilesets_dir, json_filename)
            
            # Fallback to old format/location for backward compatibility
            if not os.path.exists(mappings_file):
                mappings_file = "tileset_mappings.json"
        else:
            return {}
        
        # Default mappings (fallback)
        default_mappings = {
            # Water tiles (typically early in row 0)
            TerrainType.DEEP_WATER: (0, 0),
            TerrainType.SHALLOW_WATER: (1, 0),
            TerrainType.RIVER: (2, 0),
            
            # Land terrain (typically after water in row 0)
            TerrainType.GRASSLAND: (4, 0),
            TerrainType.HILLS: (8, 0),
            TerrainType.MOUNTAIN: (12, 0),
            TerrainType.FOREST: (16, 0),
            TerrainType.FORESTED_HILL: (20, 0),
        }
        
        # Try to load from file
        if os.path.exists(mappings_file):
            try:
                with open(mappings_file, 'r') as f:
                    json_data = json.load(f)
                
                mappings = {}
                transparency_color = None
                
                for terrain_name, layers in json_data.items():
                    # Check for transparency color metadata
                    if terrain_name == '_transparency_color':
                        transparency_color = tuple(layers) if isinstance(layers, list) and len(layers) >= 3 else None
                        continue
                    
                    # Find matching TerrainType
                    for terrain_type in TerrainType:
                        if terrain_type.value == terrain_name:
                            # Handle both old format (single [x, y]) and new format ([[x, y]] or [[x1, y1], [x2, y2]])
                            if isinstance(layers, list) and len(layers) > 0:
                                if isinstance(layers[0], list):
                                    # New format: list of [x, y] lists
                                    mappings[terrain_type] = [tuple(layer) for layer in layers]
                                else:
                                    # Old format: single [x, y] - convert to new format
                                    mappings[terrain_type] = [tuple(layers)]
                            break
                
                # Store transparency color for use in compositing
                if transparency_color:
                    self.transparency_color = transparency_color
                    print(f"  Transparency color: RGB{transparency_color}")
                else:
                    self.transparency_color = None
                
                # Don't merge defaults - only use what's in the file
                # If a terrain type is missing, it will use color-based rendering
                
                print(f"  Loaded terrain mappings from {mappings_file}")
                print(f"  Terrain mappings:")
                for terrain_type, layers in sorted(mappings.items(), key=lambda x: x[0].value):
                    if isinstance(layers, list) and len(layers) > 0:
                        if len(layers) == 1:
                            print(f"    {terrain_type.value}: tile {layers[0]}")
                        else:
                            print(f"    {terrain_type.value}: layer 1 {layers[0]}, layer 2 {layers[1]}")
                    else:
                        print(f"    {terrain_type.value}: tile {layers}")
                
                return mappings
            except Exception as e:
                print(f"  Error loading mappings from {mappings_file}: {e}")
                print(f"  Terrain types will use color-based rendering")
                return {}
        else:
            print(f"  Mappings file not found: {mappings_file}")
            print(f"  Terrain types will use color-based rendering")
            return {}
    
    def _get_tile_surface(self, terrain_type: TerrainType) -> Optional[pygame.Surface]:
        """
        Get the tile surface for a terrain type from the tileset.
        Supports single layer or two-layer tiles (base + overlay).
        Extracts at native tileset size and scales to display size.
        
        Args:
            terrain_type: The terrain type
            
        Returns:
            pygame.Surface of the tile scaled to display size, or None if tileset not available (color-based rendering)
        """
        # If not using tileset, return None to use colored rectangles
        if not self.use_tileset:
            return None
        
        if not self.tileset or self.tileset_tile_size is None:
            return None
        
        if terrain_type not in self.terrain_tile_map:
            return None
        
        layers = self.terrain_tile_map[terrain_type]
        
        # Handle both old format (single tuple) and new format (list of layers)
        if isinstance(layers, tuple):
            # Old format: single (x, y) tuple
            layers = [layers]
        elif not isinstance(layers, list):
            return None
        
        # Create composite surface (start with transparent background)
        composite = pygame.Surface((self.tileset_tile_size, self.tileset_tile_size), pygame.SRCALPHA)
        
        # Draw each layer (first layer is base, subsequent layers are overlays)
        for layer_index, layer in enumerate(layers):
            if isinstance(layer, (list, tuple)) and len(layer) >= 2:
                tile_x, tile_y = layer[0], layer[1]
                
                # Calculate source rect in tileset (using native tileset tile size)
                source_x = tile_x * self.tileset_tile_size
                source_y = tile_y * self.tileset_tile_size
                
                # Bounds check
                if source_x + self.tileset_tile_size > self.tileset.get_width() or \
                   source_y + self.tileset_tile_size > self.tileset.get_height():
                    continue  # Skip invalid tile coordinates
                
                source_rect = pygame.Rect(source_x, source_y, self.tileset_tile_size, self.tileset_tile_size)
                
                # Extract tile from tileset at native size
                native_tile = pygame.Surface((self.tileset_tile_size, self.tileset_tile_size), pygame.SRCALPHA)
                native_tile.blit(self.tileset, (0, 0), source_rect)
                
                # Composite onto base
                if layer_index == 0:
                    # Base layer: draw directly (fully opaque)
                    composite.blit(native_tile, (0, 0))
                else:
                    # Overlay layer: composite with transparency color support
                    overlay_copy = native_tile.copy()
                    
                    # If transparency color is set, make matching pixels transparent
                    if self.transparency_color:
                        # Convert surface to array for pixel manipulation
                        try:
                            # Try using surfarray for faster pixel manipulation
                            import pygame.surfarray as surfarray
                            # Get pixel array
                            pixel_array = surfarray.pixels3d(overlay_copy)
                            alpha_array = surfarray.pixels_alpha(overlay_copy)
                            
                            # Find pixels matching transparency color (with small tolerance)
                            tolerance = 5  # Allow slight color variation
                            r, g, b = self.transparency_color
                            
                            # Create mask for matching pixels
                            mask = (
                                (pixel_array[:, :, 0] >= r - tolerance) & (pixel_array[:, :, 0] <= r + tolerance) &
                                (pixel_array[:, :, 1] >= g - tolerance) & (pixel_array[:, :, 1] <= g + tolerance) &
                                (pixel_array[:, :, 2] >= b - tolerance) & (pixel_array[:, :, 2] <= b + tolerance)
                            )
                            
                            # Set alpha to 0 for matching pixels
                            alpha_array[mask] = 0
                            
                            # Clean up
                            del pixel_array
                            del alpha_array
                        except Exception:
                            # Fallback: manual pixel-by-pixel approach
                            for y in range(overlay_copy.get_height()):
                                for x in range(overlay_copy.get_width()):
                                    pixel = overlay_copy.get_at((x, y))
                                    r, g, b, a = pixel
                                    # Check if pixel matches transparency color (with tolerance)
                                    if (abs(r - self.transparency_color[0]) <= 5 and
                                        abs(g - self.transparency_color[1]) <= 5 and
                                        abs(b - self.transparency_color[2]) <= 5):
                                        overlay_copy.set_at((x, y), (r, g, b, 0))  # Make transparent
                    
                    # Composite overlay onto base (alpha blending)
                    composite.blit(overlay_copy, (0, 0))
        
        # Scale to display size if needed
        if self.tileset_tile_size != self.tile_size:
            tile_surface = pygame.transform.scale(composite, (self.tile_size, self.tile_size))
        else:
            tile_surface = composite
        
        return tile_surface
    
    def render_map(self, map_data: List[List[Terrain]], surface: pygame.Surface, 
                   quest_marker: Optional[Tuple[int, int]] = None, 
                   camera_x: int = 0, camera_y: int = 0, 
                   settlements: Optional[List[Settlement]] = None,
                   selected_village: Optional[Settlement] = None,
                   selected_town: Optional[Settlement] = None,
                   selected_city: Optional[Settlement] = None,
                   explored_tiles: Optional[set] = None,
                   visible_tiles: Optional[set] = None,
                   caravans: Optional[List] = None):
        """
        Render the map to a pygame surface.
        
        Args:
            map_data: 2D list of Terrain objects
            surface: Pygame surface to render to
            camera_x: Camera X offset in tiles
            camera_y: Camera Y offset in tiles
            settlements: Optional list of settlements to render
            selected_village: Currently selected village (for showing connections)
            selected_town: Currently selected town (for showing connections)
            selected_city: Currently selected city (for showing connections)
            explored_tiles: Set of (x, y) tuples for explored tiles (for fog of war)
            visible_tiles: Set of (x, y) tuples for currently visible tiles (for fog of war)
        """
        map_height = len(map_data)
        map_width = len(map_data[0]) if map_height > 0 else 0
        
        screen_height = surface.get_height()
        screen_width = surface.get_width()
        
        # Calculate visible tile range
        tiles_visible_y = (screen_height // self.tile_size) + 2
        tiles_visible_x = (screen_width // self.tile_size) + 2
        
        start_y = max(0, camera_y)
        end_y = min(map_height, camera_y + tiles_visible_y)
        start_x = max(0, camera_x)
        end_x = min(map_width, camera_x + tiles_visible_x)
        
        # Draw each visible tile
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Check fog of war
                is_explored = explored_tiles is None or (x, y) in explored_tiles
                is_visible = visible_tiles is None or (x, y) in visible_tiles
                
                terrain = map_data[y][x]
                
                # Calculate screen position
                screen_x = (x - camera_x) * self.tile_size
                screen_y = (y - camera_y) * self.tile_size
                
                # Draw tile
                rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                
                # Try to use tileset image, fall back to colored rectangle
                tile_surface = self._get_tile_surface(terrain.terrain_type)
                
                if tile_surface:
                    # Use tileset tile
                # Fog of war logic:
                    if is_visible:
                        # Visible tiles: show normal tile
                        surface.blit(tile_surface, (screen_x, screen_y))
                    elif not is_explored:
                        # Unexplored: completely black
                        pygame.draw.rect(surface, (0, 0, 0), rect)
                    else:
                        # Explored but not visible: darken the tile
                        darkened_tile = tile_surface.copy()
                        darkened_tile.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
                        surface.blit(darkened_tile, (screen_x, screen_y))
                else:
                    # Fall back to colored rectangles
                    color = terrain.get_color()
                    
                    # Fog of war logic for color-based rendering:
                # 1. Visible tiles: normal color (not darkened)
                # 2. Unexplored tiles: completely black
                # 3. Explored but not visible tiles: darkened
                if is_visible:
                    # Visible tiles: always show normal color (never darkened)
                    pygame.draw.rect(surface, color, rect)
                elif not is_explored:
                    # Unexplored: completely black
                    pygame.draw.rect(surface, (0, 0, 0), rect)
                else:
                    # Explored but not visible: darken the color (fog of war)
                    # Darken by 70% (keep 30% of original brightness)
                    fog_color = tuple(max(0, int(c * 0.3)) for c in color)
                    pygame.draw.rect(surface, fog_color, rect)
                
                    # Draw border for better visibility (only if explored and using colored rectangles)
                if is_explored:
                    border_color = (0, 0, 0) if is_visible else (20, 20, 20)
                    pygame.draw.rect(surface, border_color, rect, 1)
        
        # Draw quest marker if provided (always visible, even in unexplored areas)
        if quest_marker:
            qx, qy = quest_marker
            # Only draw if quest marker is on screen (ignore fog of war)
            if start_x <= qx < end_x and start_y <= qy < end_y:
                screen_x = (qx - camera_x) * self.tile_size
                screen_y = (qy - camera_y) * self.tile_size
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_size // 2
                
                # Draw quest marker as a yellow star/pentagon
                size = int(self.tile_size * 0.7)
                quest_color = (255, 255, 0)  # Yellow
                # Draw pentagon
                points = []
                for i in range(5):
                    angle = (i * 2 * math.pi / 5) - (math.pi / 2)  # Start at top
                    px = center_x + size // 2 * math.cos(angle)
                    py = center_y + size // 2 * math.sin(angle)
                    points.append((px, py))
                pygame.draw.polygon(surface, quest_color, points)
                pygame.draw.polygon(surface, (255, 200, 0), points, 2)  # Orange border
        
        # Draw settlements (only if visible)
        if settlements:
            for settlement in settlements:
                x, y = settlement.get_position()
                # Only draw if settlement is on screen and visible
                if start_x <= x < end_x and start_y <= y < end_y:
                    # Check if settlement is visible (fog of war)
                    is_visible = visible_tiles is None or (x, y) in visible_tiles
                    if not is_visible:
                        continue  # Skip drawing if not visible
                    screen_x = (x - camera_x) * self.tile_size
                    screen_y = (y - camera_y) * self.tile_size
                    
                    # Draw settlement with appropriate shape and color
                    center_x = screen_x + self.tile_size // 2
                    center_y = screen_y + self.tile_size // 2
                    
                    if settlement.settlement_type.value == "town":
                        # Towns: Draw as a square/rectangle (like a fortified settlement)
                        size = int(self.tile_size * 0.6)  # Make towns larger (60% of tile size)
                        town_rect = pygame.Rect(
                            center_x - size // 2,
                            center_y - size // 2,
                            size,
                            size
                        )
                        # Dark gray color for towns (distinct from hills)
                        pygame.draw.rect(surface, (60, 60, 60), town_rect)  # Dark gray
                        pygame.draw.rect(surface, (255, 255, 255), town_rect, 3)  # Bright white border for visibility
                        # Add a bright center dot to make it more visible
                        pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 3)
                    elif settlement.settlement_type.value == "village":
                        # Villages: Draw as a small circle (simpler settlement)
                        radius = self.tile_size // 5
                        # Light brown/tan color for villages
                        pygame.draw.circle(surface, (160, 120, 80), (center_x, center_y), radius)  # Medium brown
                        pygame.draw.circle(surface, (255, 255, 200), (center_x, center_y), radius, 1)  # Light border
                        # Highlight selected village
                        if settlement == selected_village:
                            pygame.draw.circle(surface, (255, 255, 0), (center_x, center_y), radius + 2, 2)
                    elif settlement.settlement_type.value == "city":
                        # Cities: Draw as a pentagon/star shape (larger and more prominent)
                        size = int(self.tile_size * 0.8)  # 80% of tile size
                        # Bronze/gold color for cities
                        city_color = (205, 127, 50)  # Bronze
                        # Draw pentagon
                        points = []
                        for i in range(5):
                            angle = (i * 2 * math.pi / 5) - (math.pi / 2)  # Start at top
                            px = center_x + size // 2 * math.cos(angle)
                            py = center_y + size // 2 * math.sin(angle)
                            points.append((px, py))
                        pygame.draw.polygon(surface, city_color, points)
                        pygame.draw.polygon(surface, (255, 255, 255), points, 3)  # White border
                        # Add center dot
                        pygame.draw.circle(surface, (255, 215, 0), (center_x, center_y), 4)  # Gold center
        
        # Draw caravans
        if caravans:
            for caravan in caravans:
                # Only draw if caravan is visible (in explored/visible tiles)
                caravan_x, caravan_y = caravan.get_tile_position()
                if explored_tiles is None or (caravan_x, caravan_y) in explored_tiles:
                    # Check if caravan is on screen
                    if start_x <= caravan_x < end_x and start_y <= caravan_y < end_y:
                        screen_x = (caravan_x - camera_x) * self.tile_size
                        screen_y = (caravan_y - camera_y) * self.tile_size
                        
                        # Draw caravan as a small brown rectangle with a border
                        caravan_size = self.tile_size // 3
                        center_x = screen_x + self.tile_size // 2
                        center_y = screen_y + self.tile_size // 2
                        
                        # Draw caravan (brown/beige color)
                        caravan_rect = pygame.Rect(
                            center_x - caravan_size // 2,
                            center_y - caravan_size // 2,
                            caravan_size,
                            caravan_size
                        )
                        pygame.draw.rect(surface, (139, 90, 43), caravan_rect)  # Brown
                        pygame.draw.rect(surface, (255, 255, 200), caravan_rect, 2)  # Light border
        
        # Draw arrows for selected settlements
        if selected_village and selected_village.vassal_to:
            # Draw arrow from village to its town
            self._draw_arrow_between_settlements(surface, selected_village, selected_village.vassal_to,
                                                 camera_x, camera_y, (255, 255, 0),  # Yellow
                                                 selected_village.supplies_resource or "Unknown")
        
        if selected_town:
            # Draw arrows from all vassal villages to the town
            for village in selected_town.vassal_villages:
                resource = village.supplies_resource or "Unknown"
                self._draw_arrow_between_settlements(surface, village, selected_town,
                                                     camera_x, camera_y, (255, 255, 0),  # Yellow
                                                     resource)
            # Draw arrow to city if town is vassal to a city
            if selected_town.vassal_to and selected_town.vassal_to.settlement_type == SettlementType.CITY:
                self._draw_arrow_between_settlements(surface, selected_town, selected_town.vassal_to,
                                                     camera_x, camera_y, (200, 100, 255),  # Purple
                                                     "Vassal")
        
        if selected_city:
            # Draw entire network: villages to towns, towns to city
            for town in selected_city.vassal_towns:
                # Draw arrow from town to city
                self._draw_arrow_between_settlements(surface, town, selected_city,
                                                     camera_x, camera_y, (200, 100, 255),  # Purple
                                                     "Vassal")
                # Draw arrows from town's villages to town
                for village in town.vassal_villages:
                    resource = village.supplies_resource or "Unknown"
                    self._draw_arrow_between_settlements(surface, village, town,
                                                         camera_x, camera_y, (255, 255, 0),  # Yellow
                                                         resource)
    
    def get_map_pixel_size(self, map_data: List[List[Terrain]]) -> tuple:
        """
        Get the pixel dimensions of the full map.
        
        Args:
            map_data: 2D list of Terrain objects
            
        Returns:
            (width, height) in pixels
        """
        map_height = len(map_data)
        map_width = len(map_data[0]) if map_height > 0 else 0
        
        return (map_width * self.tile_size, map_height * self.tile_size)
    
    def render_map_overview(self, map_data: List[List[Terrain]], surface: pygame.Surface,
                           overview_tile_size: int = 1, camera_x: int = 0, camera_y: int = 0,
                           settlements: Optional[List[Settlement]] = None,
                           quest_marker: Optional[Tuple[int, int]] = None):
        """
        Render the entire map at a zoomed-out scale for overview.
        
        Args:
            map_data: 2D list of Terrain objects
            surface: Pygame surface to render to
            overview_tile_size: Size of each tile in overview (typically 1-2 pixels)
            camera_x: Camera X offset in overview tiles
            camera_y: Camera Y offset in overview tiles
        """
        map_height = len(map_data)
        map_width = len(map_data[0]) if map_height > 0 else 0
        
        screen_height = surface.get_height()
        screen_width = surface.get_width()
        
        # Calculate visible tile range in overview
        tiles_visible_y = (screen_height // overview_tile_size) + 2
        tiles_visible_x = (screen_width // overview_tile_size) + 2
        
        start_y = max(0, camera_y)
        end_y = min(map_height, camera_y + tiles_visible_y)
        start_x = max(0, camera_x)
        end_x = min(map_width, camera_x + tiles_visible_x)
        
        # Draw each visible tile at overview scale
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                terrain = map_data[y][x]
                color = terrain.get_color()
                
                # Calculate screen position
                screen_x = (x - camera_x) * overview_tile_size
                screen_y = (y - camera_y) * overview_tile_size
                
                # Draw tile (no border for overview to save space)
                if overview_tile_size > 1:
                    rect = pygame.Rect(screen_x, screen_y, overview_tile_size, overview_tile_size)
                    pygame.draw.rect(surface, color, rect)
                else:
                    # For 1-pixel tiles, just set the pixel
                    if 0 <= screen_x < screen_width and 0 <= screen_y < screen_height:
                        surface.set_at((screen_x, screen_y), color)
        
        # Draw settlements in overview - always draw, even if overview_tile_size is small
        if settlements:
            for settlement in settlements:
                x, y = settlement.get_position()
                # Only draw if settlement is visible
                if start_x <= x < end_x and start_y <= y < end_y:
                    screen_x = (x - camera_x) * overview_tile_size
                    screen_y = (y - camera_y) * overview_tile_size
                    
                    # Draw settlements in overview
                    if 0 <= screen_x < screen_width and 0 <= screen_y < screen_height:
                        center_x = screen_x + overview_tile_size // 2
                        center_y = screen_y + overview_tile_size // 2
                        
                        if settlement.settlement_type.value == "town":
                            # Towns: Always draw as large, prominent squares in overview (10x10 pixels with glow)
                            size = 10  # Fixed large size for visibility
                            # Draw yellow glow first
                            glow_rect = pygame.Rect(
                                center_x - size // 2 - 2,
                                center_y - size // 2 - 2,
                                size + 4,
                                size + 4
                            )
                            pygame.draw.rect(surface, (255, 255, 0), glow_rect)  # Bright yellow glow
                            # Draw town square
                            town_rect = pygame.Rect(
                                center_x - size // 2,
                                center_y - size // 2,
                                size,
                                size
                            )
                            pygame.draw.rect(surface, (60, 60, 60), town_rect)  # Dark gray
                            pygame.draw.rect(surface, (255, 255, 255), town_rect, 2)  # Bright white border
                        elif settlement.settlement_type.value == "village":
                            # Villages: Draw as a small circle in overview (only if tile size is large enough)
                            if overview_tile_size >= 2:
                                radius = max(1, overview_tile_size // 3)
                                pygame.draw.circle(surface, (160, 120, 80), 
                                                 (center_x, center_y), radius)  # Medium brown
                        elif settlement.settlement_type.value == "city":
                            # Cities: Always draw as large, prominent star/pentagon in overview (16x16 with glow)
                            size = 16  # Fixed large size for visibility
                            # Draw pentagon/star
                            points = []
                            for i in range(5):
                                angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                                px = center_x + size // 2 * math.cos(angle)
                                py = center_y + size // 2 * math.sin(angle)
                                points.append((px, py))
                            # Gold glow effect (larger)
                            glow_points = []
                            for i in range(5):
                                angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                                px = center_x + (size // 2 + 4) * math.cos(angle)
                                py = center_y + (size // 2 + 4) * math.sin(angle)
                                glow_points.append((px, py))
                            pygame.draw.polygon(surface, (255, 215, 0), glow_points)  # Bright gold glow
                            pygame.draw.polygon(surface, (205, 127, 50), points)  # Bronze city
                            pygame.draw.polygon(surface, (255, 255, 255), points, 2)  # White border
        
        # Draw quest marker prominently in overview
        if quest_marker:
            qx, qy = quest_marker
            # Only draw if quest marker is visible in overview
            if start_x <= qx < end_x and start_y <= qy < end_y:
                screen_x = (qx - camera_x) * overview_tile_size
                screen_y = (qy - camera_y) * overview_tile_size
                
                if 0 <= screen_x < screen_width and 0 <= screen_y < screen_height:
                    center_x = screen_x + overview_tile_size // 2
                    center_y = screen_y + overview_tile_size // 2
                    
                    # Draw a large, prominent quest marker (star/pentagon)
                    # Use a fixed large size for visibility regardless of overview_tile_size
                    size = 20  # Large size for prominence
                    quest_color = (255, 255, 0)  # Bright yellow
                    glow_color = (255, 200, 0)  # Orange-yellow glow
                    
                    # Draw glow effect (larger outer circle)
                    pygame.draw.circle(surface, glow_color, (center_x, center_y), size // 2 + 4)
                    
                    # Draw pentagon/star
                    points = []
                    for i in range(5):
                        angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                        px = center_x + size // 2 * math.cos(angle)
                        py = center_y + size // 2 * math.sin(angle)
                        points.append((px, py))
                    
                    pygame.draw.polygon(surface, quest_color, points)
                    pygame.draw.polygon(surface, (255, 255, 255), points, 2)  # White border for contrast
    
    def _draw_arrow_between_settlements(self, surface: pygame.Surface, 
                                       settlement1: Settlement, settlement2: Settlement,
                                       camera_x: int, camera_y: int, color: tuple, label: str):
        """
        Draw an arrow between two settlements, even if they're off-screen.
        
        Args:
            surface: Pygame surface to draw on
            settlement1: Source settlement
            settlement2: Target settlement
            camera_x: Camera X offset in tiles
            camera_y: Camera Y offset in tiles
            color: Arrow color (RGB tuple)
            label: Text label to display along the arrow
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Get positions in tiles
        x1, y1 = settlement1.get_position()
        x2, y2 = settlement2.get_position()
        
        # Convert to screen coordinates
        screen_x1 = (x1 - camera_x) * self.tile_size + self.tile_size // 2
        screen_y1 = (y1 - camera_y) * self.tile_size + self.tile_size // 2
        screen_x2 = (x2 - camera_x) * self.tile_size + self.tile_size // 2
        screen_y2 = (y2 - camera_y) * self.tile_size + self.tile_size // 2
        
        # Calculate direction
        dx = screen_x2 - screen_x1
        dy = screen_y2 - screen_y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize direction
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Draw line - always draw, even if off-screen (pygame will clip)
        pygame.draw.line(surface, color, (int(screen_x1), int(screen_y1)), (int(screen_x2), int(screen_y2)), 3)
        
        # Draw arrowhead at target end
        arrow_size = 10
        angle = math.atan2(dy, dx)
        
        # Position arrowhead slightly before the target (on the line, closer to target)
        arrow_offset = min(self.tile_size // 2 + 5, length * 0.15)
        arrow_x = screen_x2 - dx_norm * arrow_offset
        arrow_y = screen_y2 - dy_norm * arrow_offset
        
        # Draw arrowhead (always draw, even if partially off-screen)
        arrow_points = [
            (arrow_x, arrow_y),
            (arrow_x - arrow_size * math.cos(angle - math.pi / 6),
             arrow_y - arrow_size * math.sin(angle - math.pi / 6)),
            (arrow_x - arrow_size * math.cos(angle + math.pi / 6),
             arrow_y - arrow_size * math.sin(angle + math.pi / 6))
        ]
        pygame.draw.polygon(surface, color, arrow_points)
        
        # Draw label at midpoint (only if visible)
        mid_x = int((screen_x1 + screen_x2) / 2)
        mid_y = int((screen_y1 + screen_y2) / 2)
        
        if 0 <= mid_x < screen_width and 0 <= mid_y < screen_height:
            font = pygame.font.Font(None, 20)
            text_surface = font.render(label, True, color)
            text_rect = text_surface.get_rect(center=(mid_x, mid_y))
            # Draw semi-transparent background for text
            bg_surface = pygame.Surface((text_rect.width + 4, text_rect.height + 2), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))
            surface.blit(bg_surface, (text_rect.x - 2, text_rect.y - 1))
            surface.blit(text_surface, text_rect)
    
    def draw_town_dialogue(self, surface: pygame.Surface, town: Settlement):
        """
        Draw a dialogue box showing town information and vassal villages.
        
        Args:
            surface: Pygame surface to draw on
            town: The town to display information for
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Fonts
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Calculate required width
        town_name = town.name if town.name else "Unnamed Town"
        title_width = title_font.size(town_name)[0]
        
        # Calculate width for status line
        if town.vassal_to and town.vassal_to.settlement_type == SettlementType.CITY:
            city_name = town.vassal_to.name if town.vassal_to.name else "Unnamed City"
            status_width = small_font.size(f"Vassal to: {city_name}")[0]
        else:
            status_width = small_font.size("Status: Independent")[0]
        
        # Calculate width for villages
        max_village_width = 0
        for village in town.vassal_villages:
            village_name = village.name if village.name else "Unnamed Village"
            resource = village.supplies_resource if village.supplies_resource else "Unknown"
            village_line_width = small_font.size(f"• {village_name}")[0]
            resource_line_width = small_font.size(f"  Supplies: {resource}")[0]
            max_village_width = max(max_village_width, village_line_width, resource_line_width)
        
        header_width = body_font.size("Vassal Villages:")[0]
        close_width = small_font.size("Click again to close")[0]
        
        # Calculate dialog width (padding: 20 on each side, plus 40 for indentation)
        dialog_width = max(300, max(title_width, status_width, max_village_width + 40, header_width, close_width) + 40)
        dialog_width = min(dialog_width, int(screen_width * 0.9))  # Max 90% of screen width
        
        # Calculate required height
        base_height = 80  # Title + spacing
        status_height = 25  # Status line
        header_height = 30  # Header + spacing
        village_height = 45  # Per village (name + resource + spacing)
        close_height = 30  # Close instruction + spacing
        content_height = base_height + status_height + header_height + len(town.vassal_villages) * village_height + close_height
        dialog_height = min(max(200, content_height), int(screen_height * 0.9))  # Min 200, max 90% of screen
        
        dialog_x = 10  # Lower-left corner
        dialog_y = screen_height - dialog_height - 10
        
        # Draw background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)
        
        # Draw title
        title_text = title_font.render(town_name, True, (255, 255, 255))
        surface.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        # Show vassal status if town is vassal to a city
        y_offset = dialog_y + 60
        if town.vassal_to and town.vassal_to.settlement_type == SettlementType.CITY:
            city_name = town.vassal_to.name if town.vassal_to.name else "Unnamed City"
            vassal_text = small_font.render(f"Vassal to: {city_name}", True, (200, 200, 100))
            surface.blit(vassal_text, (dialog_x + 20, y_offset))
            y_offset += 25
        else:
            # Independent town
            independent_text = small_font.render("Status: Independent", True, (150, 150, 150))
            surface.blit(independent_text, (dialog_x + 20, y_offset))
            y_offset += 25
        
        # Draw "Vassal Villages:" header
        header_text = body_font.render("Vassal Villages:", True, (200, 200, 200))
        surface.blit(header_text, (dialog_x + 20, y_offset))
        y_offset += 30
        
        # Draw vassal villages with their resources
        for village in town.vassal_villages:
            village_name = village.name if village.name else "Unnamed Village"
            resource = village.supplies_resource if village.supplies_resource else "Unknown"
            village_text = small_font.render(f"• {village_name}", True, (255, 255, 255))
            surface.blit(village_text, (dialog_x + 30, y_offset))
            y_offset += 20
            resource_text = small_font.render(f"  Supplies: {resource}", True, (180, 180, 180))
            surface.blit(resource_text, (dialog_x + 40, y_offset))
            y_offset += 25
        
        # Draw close instruction
        close_text = small_font.render("Click again to close", True, (150, 150, 150))
        surface.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 25))
    
    def draw_city_dialogue(self, surface: pygame.Surface, city: Settlement):
        """
        Draw a dialogue box showing city information and vassal towns.
        
        Args:
            surface: Pygame surface to draw on
            city: The city to display information for
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Fonts
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Calculate required width
        city_name = city.name if city.name else "Unnamed City"
        title_width = title_font.size(city_name)[0]
        
        # Calculate width for towns and villages
        max_town_width = 0
        max_village_width = 0
        for town in city.vassal_towns:
            town_name = town.name if town.name else "Unnamed Town"
            town_line_width = small_font.size(f"• {town_name}")[0]
            max_town_width = max(max_town_width, town_line_width)
            
            # Check village widths
            for village in town.vassal_villages[:3]:  # Check first 3 villages
                village_name = village.name if village.name else "Unnamed Village"
                resource = village.supplies_resource if village.supplies_resource else "Unknown"
                village_line_width = small_font.size(f"  - {village_name} ({resource})")[0]
                max_village_width = max(max_village_width, village_line_width)
        
        header_width = body_font.size("Vassal Towns:")[0]
        close_width = small_font.size("Click again to close")[0]
        
        # Calculate dialog width (padding: 20 on each side, plus 40 for indentation)
        dialog_width = max(300, max(title_width, max_town_width, max_village_width + 40, header_width, close_width) + 40)
        dialog_width = min(dialog_width, int(screen_width * 0.9))  # Max 90% of screen width
        
        # Calculate required height
        base_height = 80  # Title + spacing
        header_height = 30  # Header + spacing
        close_height = 30  # Close instruction + spacing
        
        # Calculate height needed for all towns and their villages
        town_height = 0
        for town in city.vassal_towns:
            town_height += 20  # Town name
            # Show up to 3 villages per town, or all if less than 3
            villages_to_show = min(3, len(town.vassal_villages))
            town_height += villages_to_show * 18  # Village lines
            if len(town.vassal_villages) > 3:
                town_height += 18  # "... and X more" line
            town_height += 10  # Spacing between towns
        
        content_height = base_height + header_height + town_height + close_height
        dialog_height = min(max(200, content_height), int(screen_height * 0.9))  # Min 200, max 90% of screen
        
        dialog_x = screen_width - dialog_width - 10  # Lower-right corner
        dialog_y = screen_height - dialog_height - 10
        
        # Draw background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)
        
        # Draw title
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        city_name = city.name if city.name else "Unnamed City"
        title_text = title_font.render(city_name, True, (255, 215, 0))  # Gold color
        surface.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        # Draw "Vassal Towns:" header
        header_text = body_font.render("Vassal Towns:", True, (200, 200, 200))
        surface.blit(header_text, (dialog_x + 20, dialog_y + 60))
        
        # Draw vassal towns and their villages
        y_offset = dialog_y + 90
        towns_drawn = 0
        
        for town in city.vassal_towns:
            # Check if we have room for this town (at least town name + close instruction space)
            if y_offset + 50 > dialog_y + dialog_height - 30:
                # Not enough room, show "more" message
                remaining = len(city.vassal_towns) - towns_drawn
                more_text = small_font.render(f"... and {remaining} more towns", 
                                            True, (150, 150, 150))
                surface.blit(more_text, (dialog_x + 20, y_offset))
                break
            
            towns_drawn += 1
            
            town_name = town.name if town.name else "Unnamed Town"
            town_text = small_font.render(f"• {town_name}", True, (255, 255, 255))
            surface.blit(town_text, (dialog_x + 30, y_offset))
            y_offset += 20
            
            # Show up to 3 vassal villages for this town (or all if there's room)
            village_sub_count = 0
            for village in town.vassal_villages:
                # Check if we have room for more villages
                if y_offset + 20 > dialog_y + dialog_height - 30:
                    break
                if village_sub_count >= 3:  # Limit to 3 villages per town for readability
                    if len(town.vassal_villages) > 3:
                        more_villages = small_font.render(f"  ... and {len(town.vassal_villages) - 3} more villages", 
                                                         True, (120, 120, 120))
                        surface.blit(more_villages, (dialog_x + 40, y_offset))
                        y_offset += 18
                    break
                village_name = village.name if village.name else "Unnamed Village"
                resource = village.supplies_resource if village.supplies_resource else "Unknown"
                village_text = small_font.render(f"  - {village_name} ({resource})", True, (180, 180, 180))
                surface.blit(village_text, (dialog_x + 40, y_offset))
                y_offset += 18
                village_sub_count += 1
            
            y_offset += 10  # Spacing between towns
        
        # Draw close instruction
        close_text = small_font.render("Click again to close", True, (150, 150, 150))
        surface.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 25))
    
    def draw_village_dialogue(self, surface: pygame.Surface, village: Settlement):
        """
        Draw a dialogue box showing village information.
        
        Args:
            surface: Pygame surface to draw on
            village: The village to display information for
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Fonts
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Calculate required width
        village_name = village.name if village.name else "Unnamed Village"
        title_width = title_font.size(village_name)[0]
        
        resource = village.supplies_resource if village.supplies_resource else "Unknown"
        resource_label_width = body_font.size("Produces:")[0]
        resource_text_width = small_font.size(f"• {resource}")[0]
        
        # Calculate width for town and city lines
        max_line_width = 0
        if village.vassal_to:
            town_name = village.vassal_to.name if village.vassal_to.name else "Unnamed Town"
            town_label_width = body_font.size("Supplies to:")[0]
            town_text_width = small_font.size(f"• {town_name}")[0]
            max_line_width = max(max_line_width, town_label_width, town_text_width)
            
            # Check city if applicable
            if village.vassal_to.vassal_to and village.vassal_to.vassal_to.settlement_type == SettlementType.CITY:
                city_name = village.vassal_to.vassal_to.name if village.vassal_to.vassal_to.name else "Unnamed City"
                city_label_width = body_font.size("Ultimate Liege:")[0]
                city_text_width = small_font.size(f"• {city_name}")[0]
                max_line_width = max(max_line_width, city_label_width, city_text_width)
        
        close_width = small_font.size("Click again to close")[0]
        
        # Calculate dialog width (padding: 20 on each side, plus 30 for indentation)
        dialog_width = max(300, max(title_width, resource_label_width, resource_text_width + 30, max_line_width + 30, close_width) + 40)
        dialog_width = min(dialog_width, int(screen_width * 0.9))  # Max 90% of screen width
        
        # Calculate required height
        base_height = 80  # Title + spacing
        resource_section_height = 70  # Label + text + spacing
        town_section_height = 70 if village.vassal_to else 0  # Label + text + spacing
        city_section_height = 70 if (village.vassal_to and village.vassal_to.vassal_to and 
                                     village.vassal_to.vassal_to.settlement_type == SettlementType.CITY) else 0
        close_height = 30  # Close instruction + spacing
        
        content_height = base_height + resource_section_height + town_section_height + city_section_height + close_height
        dialog_height = min(max(200, content_height), int(screen_height * 0.9))  # Min 200, max 90% of screen
        
        dialog_x = 10  # Lower-left corner
        dialog_y = screen_height - dialog_height - 10
        
        # Draw background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)
        
        # Draw title
        title_text = title_font.render(village_name, True, (255, 255, 255))
        surface.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        y_offset = dialog_y + 60
        
        # Show resource being produced
        resource_label = body_font.render("Produces:", True, (200, 200, 200))
        surface.blit(resource_label, (dialog_x + 20, y_offset))
        y_offset += 30
        
        resource_text = small_font.render(f"• {resource}", True, (255, 255, 255))
        surface.blit(resource_text, (dialog_x + 30, y_offset))
        y_offset += 40
        
        # Show town it's producing for
        if village.vassal_to:
            town_label = body_font.render("Supplies to:", True, (200, 200, 200))
            surface.blit(town_label, (dialog_x + 20, y_offset))
            y_offset += 30
            
            town_name = village.vassal_to.name if village.vassal_to.name else "Unnamed Town"
            town_text = small_font.render(f"• {town_name}", True, (255, 255, 255))
            surface.blit(town_text, (dialog_x + 30, y_offset))
            y_offset += 40
            
            # Show city if town is vassal to a city
            if village.vassal_to.vassal_to and village.vassal_to.vassal_to.settlement_type == SettlementType.CITY:
                city_label = body_font.render("Ultimate Liege:", True, (200, 200, 200))
                surface.blit(city_label, (dialog_x + 20, y_offset))
                y_offset += 30
                
                city_name = village.vassal_to.vassal_to.name if village.vassal_to.vassal_to.name else "Unnamed City"
                city_text = small_font.render(f"• {city_name}", True, (255, 215, 0))  # Gold color for city
                surface.blit(city_text, (dialog_x + 30, y_offset))
        
        # Draw close instruction
        close_text = small_font.render("Click again to close", True, (150, 150, 150))
        surface.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 25))


        town_section_height = 70 if village.vassal_to else 0  # Label + text + spacing
        city_section_height = 70 if (village.vassal_to and village.vassal_to.vassal_to and 
                                     village.vassal_to.vassal_to.settlement_type == SettlementType.CITY) else 0
        close_height = 30  # Close instruction + spacing
        
        content_height = base_height + resource_section_height + town_section_height + city_section_height + close_height
        dialog_height = min(max(200, content_height), int(screen_height * 0.9))  # Min 200, max 90% of screen
        
        dialog_x = 10  # Lower-left corner
        dialog_y = screen_height - dialog_height - 10
        
        # Draw background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)
        
        # Draw title
        title_text = title_font.render(village_name, True, (255, 255, 255))
        surface.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        y_offset = dialog_y + 60
        
        # Show resource being produced
        resource_label = body_font.render("Produces:", True, (200, 200, 200))
        surface.blit(resource_label, (dialog_x + 20, y_offset))
        y_offset += 30
        
        resource_text = small_font.render(f"• {resource}", True, (255, 255, 255))
        surface.blit(resource_text, (dialog_x + 30, y_offset))
        y_offset += 40
        
        # Show town it's producing for
        if village.vassal_to:
            town_label = body_font.render("Supplies to:", True, (200, 200, 200))
            surface.blit(town_label, (dialog_x + 20, y_offset))
            y_offset += 30
            
            town_name = village.vassal_to.name if village.vassal_to.name else "Unnamed Town"
            town_text = small_font.render(f"• {town_name}", True, (255, 255, 255))
            surface.blit(town_text, (dialog_x + 30, y_offset))
            y_offset += 40
            
            # Show city if town is vassal to a city
            if village.vassal_to.vassal_to and village.vassal_to.vassal_to.settlement_type == SettlementType.CITY:
                city_label = body_font.render("Ultimate Liege:", True, (200, 200, 200))
                surface.blit(city_label, (dialog_x + 20, y_offset))
                y_offset += 30
                
                city_name = village.vassal_to.vassal_to.name if village.vassal_to.vassal_to.name else "Unnamed City"
                city_text = small_font.render(f"• {city_name}", True, (255, 215, 0))  # Gold color for city
                surface.blit(city_text, (dialog_x + 30, y_offset))
        
        # Draw close instruction
        close_text = small_font.render("Click again to close", True, (150, 150, 150))
        surface.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 25))

