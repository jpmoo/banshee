"""
Map rendering system using pygame.
Displays the map with colored tiles representing different terrain types.
"""
import pygame
import math
from typing import List, Optional
from terrain import Terrain
from settlements import Settlement, SettlementType


class MapRenderer:
    """Renders the map to a pygame surface."""
    
    def __init__(self, tile_size: int = 32):
        """
        Initialize the map renderer.
        
        Args:
            tile_size: Size of each tile in pixels
        """
        self.tile_size = tile_size
    
    def render_map(self, map_data: List[List[Terrain]], surface: pygame.Surface, 
                   camera_x: int = 0, camera_y: int = 0, 
                   settlements: Optional[List[Settlement]] = None,
                   selected_village: Optional[Settlement] = None,
                   selected_town: Optional[Settlement] = None,
                   selected_city: Optional[Settlement] = None):
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
                terrain = map_data[y][x]
                color = terrain.get_color()
                
                # Calculate screen position
                screen_x = (x - camera_x) * self.tile_size
                screen_y = (y - camera_y) * self.tile_size
                
                # Draw tile
                rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                pygame.draw.rect(surface, color, rect)
                
                # Draw border for better visibility
                pygame.draw.rect(surface, (0, 0, 0), rect, 1)
        
        # Draw settlements
        if settlements:
            for settlement in settlements:
                x, y = settlement.get_position()
                # Only draw if settlement is visible
                if start_x <= x < end_x and start_y <= y < end_y:
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
                           settlements: Optional[List[Settlement]] = None):
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
                            # Towns: Draw as a highlighted square in overview with bright border
                            if overview_tile_size >= 3:
                                size = max(3, int(overview_tile_size * 0.7))
                                town_rect = pygame.Rect(
                                    center_x - size // 2,
                                    center_y - size // 2,
                                    size,
                                    size
                                )
                                pygame.draw.rect(surface, (60, 60, 60), town_rect)  # Dark gray
                                pygame.draw.rect(surface, (255, 255, 0), town_rect, 2)  # Bright yellow border for highlighting
                            elif overview_tile_size >= 2:
                                # Smaller overview - still draw with highlight
                                size = 2
                                town_rect = pygame.Rect(
                                    center_x - size // 2,
                                    center_y - size // 2,
                                    size,
                                    size
                                )
                                pygame.draw.rect(surface, (60, 60, 60), town_rect)
                                pygame.draw.rect(surface, (255, 255, 0), town_rect, 1)  # Yellow border
                            else:
                                # For 1-pixel overview, use bright yellow to stand out
                                surface.set_at((center_x, center_y), (255, 255, 0))
                        elif settlement.settlement_type.value == "village":
                            # Villages: Draw as a small circle in overview (only if tile size is large enough)
                            if overview_tile_size >= 2:
                                radius = max(1, overview_tile_size // 3)
                                pygame.draw.circle(surface, (160, 120, 80), 
                                                 (center_x, center_y), radius)  # Medium brown
                        elif settlement.settlement_type.value == "city":
                            # Cities: Draw as a star/pentagon in overview
                            if overview_tile_size >= 3:
                                size = 16  # Fixed size for cities in overview
                                # Draw pentagon/star
                                points = []
                                for i in range(5):
                                    angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                                    px = center_x + size // 2 * math.cos(angle)
                                    py = center_y + size // 2 * math.sin(angle)
                                    points.append((px, py))
                                # Gold glow effect
                                glow_points = []
                                for i in range(5):
                                    angle = (i * 2 * math.pi / 5) - (math.pi / 2)
                                    px = center_x + (size // 2 + 4) * math.cos(angle)
                                    py = center_y + (size // 2 + 4) * math.sin(angle)
                                    glow_points.append((px, py))
                                pygame.draw.polygon(surface, (255, 215, 0), glow_points)  # Gold glow
                                pygame.draw.polygon(surface, (205, 127, 50), points)  # Bronze city
                                pygame.draw.polygon(surface, (255, 255, 255), points, 2)  # White border
                            elif overview_tile_size >= 2:
                                # Smaller overview - still draw city
                                size = 4
                                pygame.draw.circle(surface, (255, 215, 0), (center_x, center_y), size + 1)  # Gold glow
                                pygame.draw.circle(surface, (205, 127, 50), (center_x, center_y), size)  # Bronze
                            else:
                                # For 1-pixel overview, use bright gold
                                surface.set_at((center_x, center_y), (255, 215, 0))
        
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
        
        # Clip line to screen bounds using Liang-Barsky algorithm (simplified)
        # Calculate intersection with screen edges
        t0 = 0.0
        t1 = 1.0
        
        # Check each edge
        if dx != 0:
            t_left = -screen_x1 / dx
            t_right = (screen_width - screen_x1) / dx
            if dx < 0:
                t0 = max(t0, t_left)
                t1 = min(t1, t_right)
            else:
                t0 = max(t0, t_right)
                t1 = min(t1, t_left)
        
        if dy != 0:
            t_top = -screen_y1 / dy
            t_bottom = (screen_height - screen_y1) / dy
            if dy < 0:
                t0 = max(t0, t_top)
                t1 = min(t1, t_bottom)
            else:
                t0 = max(t0, t_bottom)
                t1 = min(t1, t_top)
        
        # If line doesn't intersect screen, don't draw
        if t0 >= t1:
            return
        
        # Calculate clipped endpoints
        clip_x1 = screen_x1 + t0 * dx
        clip_y1 = screen_y1 + t0 * dy
        clip_x2 = screen_x1 + t1 * dx
        clip_y2 = screen_y1 + t1 * dy
        
        # Draw line (pygame will clip automatically, but we've pre-clipped for arrowhead)
        pygame.draw.line(surface, color, (clip_x1, clip_y1), (clip_x2, clip_y2), 2)
        
        # Draw arrowhead at target end (slightly before the end to avoid overlap)
        arrow_size = 8
        angle = math.atan2(dy, dx)
        
        # Position arrowhead slightly before the target
        arrow_offset = min(self.tile_size // 2, length * 0.1)
        arrow_x = clip_x2 - dx_norm * arrow_offset
        arrow_y = clip_y2 - dy_norm * arrow_offset
        
        # Draw arrowhead
        arrow_points = [
            (arrow_x, arrow_y),
            (arrow_x - arrow_size * math.cos(angle - math.pi / 6),
             arrow_y - arrow_size * math.sin(angle - math.pi / 6)),
            (arrow_x - arrow_size * math.cos(angle + math.pi / 6),
             arrow_y - arrow_size * math.sin(angle + math.pi / 6))
        ]
        pygame.draw.polygon(surface, color, arrow_points)
        
        # Draw label at midpoint (only if visible)
        mid_x = int((clip_x1 + clip_x2) / 2)
        mid_y = int((clip_y1 + clip_y2) / 2)
        
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
        
        dialog_width = 300
        dialog_height = 400
        dialog_x = 10  # Lower-left corner
        dialog_y = screen_height - dialog_height - 10
        
        # Draw background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, (40, 40, 40), dialog_rect)
        pygame.draw.rect(surface, (200, 200, 200), dialog_rect, 2)
        
        # Draw title
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        town_name = town.name if town.name else "Unnamed Town"
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
        
        dialog_width = 300
        dialog_height = 400
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
        town_count = 0
        max_towns_visible = (dialog_height - 120) // 60  # Space for towns and some villages
        
        for town in city.vassal_towns:
            if town_count >= max_towns_visible:
                remaining = len(city.vassal_towns) - town_count
                more_text = small_font.render(f"... and {remaining} more towns", 
                                            True, (150, 150, 150))
                surface.blit(more_text, (dialog_x + 20, y_offset))
                break
            
            town_name = town.name if town.name else "Unnamed Town"
            town_text = small_font.render(f"• {town_name}", True, (255, 255, 255))
            surface.blit(town_text, (dialog_x + 30, y_offset))
            y_offset += 20
            
            # Show up to 3 vassal villages for this town
            village_sub_count = 0
            for village in town.vassal_villages:
                if village_sub_count >= 3:  # Limit villages shown per town
                    break
                village_name = village.name if village.name else "Unnamed Village"
                resource = village.supplies_resource if village.supplies_resource else "Unknown"
                village_text = small_font.render(f"  - {village_name} ({resource})", True, (180, 180, 180))
                surface.blit(village_text, (dialog_x + 40, y_offset))
                y_offset += 18
                village_sub_count += 1
            
            y_offset += 10  # Spacing between towns
            town_count += 1
        
        # Draw close instruction
        close_text = small_font.render("Click again to close", True, (150, 150, 150))
        surface.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 25))
    
    def draw_settlement_status(self, surface: pygame.Surface, settlement: Settlement):
        """
        Draw a status window showing settlement information.
        This is shown when the player (camera center) is on a settlement.
        
        Args:
            surface: Pygame surface to draw on
            settlement: The settlement to display information for
        """
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Status window size and position (top-right corner)
        status_width = 350
        status_height = 400
        status_x = screen_width - status_width - 10
        status_y = 10
        
        # Draw background
        status_rect = pygame.Rect(status_x, status_y, status_width, status_height)
        pygame.draw.rect(surface, (40, 40, 40), status_rect)
        pygame.draw.rect(surface, (200, 200, 200), status_rect, 2)
        
        # Fonts
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        y_offset = status_y + 20
        
        # Settlement name
        settlement_name = settlement.name if settlement.name else f"Unnamed {settlement.settlement_type.value.title()}"
        if settlement.settlement_type.value == "city":
            title_color = (255, 215, 0)  # Gold
        elif settlement.settlement_type.value == "town":
            title_color = (255, 255, 255)  # White
        else:
            title_color = (200, 200, 200)  # Light gray
        
        title_text = title_font.render(settlement_name, True, title_color)
        surface.blit(title_text, (status_x + 20, y_offset))
        y_offset += 40
        
        # Village display
        if settlement.settlement_type.value == "village":
            if settlement.vassal_to:
                town_name = settlement.vassal_to.name if settlement.vassal_to.name else "Unnamed Town"
                resource = settlement.supplies_resource or "Unknown"
                # Normalize resource name for display
                from settlements import normalize_resource_name
                normalized_resource = normalize_resource_name(resource)
                status_text = small_font.render(
                    f"Sends {normalized_resource} to {town_name} in return for protection.",
                    True, (200, 200, 200)
                )
                surface.blit(status_text, (status_x + 20, y_offset))
            return  # Villages don't have resources or trade goods
        
        # Vassal relationships
        if settlement.vassal_to:
            liege_name = settlement.vassal_to.name if settlement.vassal_to.name else "Unnamed"
            liege_type = settlement.vassal_to.settlement_type.value.title()
            vassal_text = body_font.render(f"Vassal to: {liege_name} ({liege_type})", True, (200, 200, 100))
            surface.blit(vassal_text, (status_x + 20, y_offset))
            y_offset += 30
        
        # Show vassals (downward relationships)
        if settlement.settlement_type.value == "town" and settlement.vassal_villages:
            vassal_count = len(settlement.vassal_villages)
            vassals_text = small_font.render(f"Has {vassal_count} vassal village(s)", True, (180, 180, 180))
            surface.blit(vassals_text, (status_x + 20, y_offset))
            y_offset += 25
        elif settlement.settlement_type.value == "city" and settlement.vassal_towns:
            vassal_count = len(settlement.vassal_towns)
            vassals_text = small_font.render(f"Has {vassal_count} vassal town(s)", True, (180, 180, 180))
            surface.blit(vassals_text, (status_x + 20, y_offset))
            y_offset += 25
        
        y_offset += 10  # Spacing
        
        # Resources (for towns only)
        if settlement.settlement_type.value == "town":
            resources_header = body_font.render("Resources:", True, (200, 200, 200))
            surface.blit(resources_header, (status_x + 20, y_offset))
            y_offset += 30
            
            from settlements import RESOURCES
            for resource in RESOURCES:
                amount = settlement.resources.get(resource, 0)
                resource_text = small_font.render(f"  {resource.title()}: {amount}", True, (255, 255, 255))
                surface.blit(resource_text, (status_x + 30, y_offset))
                y_offset += 22
        
        # Trade goods (for towns and cities)
        if settlement.settlement_type.value in ("town", "city"):
            trade_goods_text = body_font.render(f"Trade Goods: {settlement.trade_goods}", True, (200, 200, 200))
            surface.blit(trade_goods_text, (status_x + 20, y_offset))
            y_offset += 30
        
        # Money (placeholder)
        money_text = small_font.render(f"Money: {settlement.money}", True, (150, 150, 150))
        surface.blit(money_text, (status_x + 20, y_offset))

