"""
Tileset selection screen for choosing which tileset to use in the game.
"""
import pygame
import os
import json
from typing import List, Optional, Tuple, Dict
import glob


class TilesetSelectionScreen:
    """Screen for selecting a tileset."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the tileset selection screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.screen = screen
        self.tilesets = []
        self.selected_index = 0
        self.tileset_rects = []  # List of (rect, index) tuples for click detection
        self.showing_preview = False
        self.preview_surface = None
        self.preview_tileset_index = None
        
        # Load available tilesets
        self._load_tilesets()
    
    def _load_tilesets(self):
        """Load available tilesets from the tilesets directory (JSON files only)."""
        self.tilesets = []
        
        # Add "Original Color-Based" option first
        self.tilesets.append({
            'name': 'Original Color-Based',
            'type': 'color',
            'path': None,
            'json_path': None,
            'info': 'Use colored rectangles (no tileset)',
            'preview_path': None
        })
        
        # Load tilesets from tilesets directory (only JSON files directly in folder, not subfolders)
        tilesets_dir = "tilesets"
        if os.path.exists(tilesets_dir):
            # Look for JSON files directly in tilesets folder (not subdirectories)
            json_files = glob.glob(os.path.join(tilesets_dir, "*.json"))
            json_files.extend(glob.glob(os.path.join(tilesets_dir, "*.JSON")))
            
            for json_path in json_files:
                # Get tileset name from JSON filename
                tileset_name = os.path.splitext(os.path.basename(json_path))[0]
                
                # Derive PNG path from JSON filename (same name, different extension)
                png_path = os.path.join(tilesets_dir, tileset_name + ".png")
                # Try uppercase extension too
                if not os.path.exists(png_path):
                    png_path = os.path.join(tilesets_dir, tileset_name + ".PNG")
                
                # Only add if PNG exists (tileset is complete)
                if os.path.exists(png_path):
                    # Read JSON to determine if it has single or double layer tiles
                    try:
                        with open(json_path, 'r') as f:
                            json_data = json.load(f)
                        
                        # Count layers for info display
                        layer_info = []
                        for terrain_name, layers in json_data.items():
                            if isinstance(layers, list) and len(layers) > 0:
                                if len(layers) == 1:
                                    layer_info.append("single")
                                else:
                                    layer_info.append("double")
                        
                        has_double = "double" in layer_info
                        layer_desc = "single/double layer" if has_double else "single layer"
                        
                        self.tilesets.append({
                            'name': tileset_name,
                            'type': 'tileset',
                            'path': png_path,  # PNG path for image loading
                            'json_path': json_path,  # JSON path for mappings
                            'info': f"Tileset: {tileset_name} ({layer_desc})",
                            'preview_path': png_path
                        })
                    except Exception as e:
                        print(f"Error reading tileset JSON {json_path}: {e}")
                        continue
    
    def render(self):
        """Render the tileset selection screen."""
        self.screen.fill((20, 20, 30))
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Select Tileset", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen_width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        font = pygame.font.Font(None, 24)
        instruction_text = font.render("Select a tileset to use", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(instruction_text, instruction_rect)
        
        # List of tilesets
        if not self.tilesets:
            no_tilesets_font = pygame.font.Font(None, 32)
            no_tilesets_text = no_tilesets_font.render("No tilesets found", True, (150, 150, 150))
            no_tilesets_rect = no_tilesets_text.get_rect(center=(screen_width // 2, screen_height // 2))
            self.screen.blit(no_tilesets_text, no_tilesets_rect)
            return
        
        # Display tilesets
        item_font = pygame.font.Font(None, 28)
        detail_font = pygame.font.Font(None, 20)
        
        start_y = 150
        item_height = 60
        spacing = 10
        max_items = (screen_height - start_y - 100) // (item_height + spacing)
        
        # Show items around selected index
        visible_start = max(0, self.selected_index - max_items // 2)
        visible_end = min(len(self.tilesets), visible_start + max_items)
        
        self.tileset_rects = []
        y_offset = start_y
        
        for i in range(visible_start, visible_end):
            tileset = self.tilesets[i]
            
            # Highlight selected item
            is_selected = (i == self.selected_index)
            bg_color = (80, 80, 100) if is_selected else (40, 40, 50)
            border_color = (255, 255, 0) if is_selected else (100, 100, 100)
            
            # Item rectangle
            item_rect = pygame.Rect(50, y_offset, screen_width - 100, item_height)
            pygame.draw.rect(self.screen, bg_color, item_rect)
            pygame.draw.rect(self.screen, border_color, item_rect, 2)
            
            self.tileset_rects.append((item_rect, i))
            
            # Tileset name
            name_text = item_font.render(tileset['name'], True, (255, 255, 255))
            self.screen.blit(name_text, (item_rect.x + 10, item_rect.y + 5))
            
            # Tileset info
            info_text = detail_font.render(tileset['info'], True, (180, 180, 180))
            self.screen.blit(info_text, (item_rect.x + 10, item_rect.y + 35))
            
            y_offset += item_height + spacing
        
        # Scroll indicators
        if visible_start > 0:
            up_arrow = detail_font.render("↑", True, (150, 150, 150))
            self.screen.blit(up_arrow, (screen_width - 30, start_y))
        if visible_end < len(self.tilesets):
            down_arrow = detail_font.render("↓", True, (150, 150, 150))
            self.screen.blit(down_arrow, (screen_width - 30, screen_height - 100))
        
        # Instructions at bottom
        bottom_font = pygame.font.Font(None, 20)
        if self.showing_preview:
            bottom_text = bottom_font.render("[P] Close Preview | [ENTER] Select | [ESC] Cancel", True, (150, 150, 150))
        else:
            bottom_text = bottom_font.render("[P] Preview | [ENTER] Select | [ESC] Cancel", True, (150, 150, 150))
        bottom_rect = bottom_text.get_rect(center=(screen_width // 2, screen_height - 30))
        self.screen.blit(bottom_text, bottom_rect)
        
        # Draw preview if active
        if self.showing_preview and self.preview_surface:
            self._draw_preview()
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Dict]:
        """
        Handle pygame events.
        
        Returns:
            Dictionary with 'tileset' key if a tileset was selected, None otherwise
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {'action': 'cancel'}
            elif event.key == pygame.K_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
            elif event.key == pygame.K_DOWN:
                if self.selected_index < len(self.tilesets) - 1:
                    self.selected_index += 1
            elif event.key == pygame.K_p:
                # Toggle preview
                if self.showing_preview:
                    self.showing_preview = False
                    self.preview_surface = None
                    self.preview_tileset_index = None
                else:
                    # Load preview for selected tileset
                    if self.tilesets and 0 <= self.selected_index < len(self.tilesets):
                        tileset = self.tilesets[self.selected_index]
                        if tileset.get('preview_path'):
                            self.preview_surface = self._load_preview(self.selected_index)
                            self.preview_tileset_index = self.selected_index
                            self.showing_preview = True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Select tileset
                if self.tilesets and 0 <= self.selected_index < len(self.tilesets):
                    selected = self.tilesets[self.selected_index]
                    return {'action': 'select', 'tileset': selected}
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = event.pos
                
                # Check tileset items
                for tileset_rect, index in self.tileset_rects:
                    if tileset_rect.collidepoint(mouse_x, mouse_y):
                        # Select this tileset
                        self.selected_index = index
                        if self.tilesets and 0 <= index < len(self.tilesets):
                            selected = self.tilesets[index]
                            return {'action': 'select', 'tileset': selected}
        
        return None
    
    def _draw_preview(self):
        """Draw a preview of the selected tileset."""
        if not self.preview_surface:
            return
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Calculate preview size (centered, max 80% of screen)
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        preview_width, preview_height = self.preview_surface.get_size()
        
        # Scale to fit
        scale = min(max_width / preview_width, max_height / preview_height, 1.0)
        if scale < 1.0:
            scaled_width = int(preview_width * scale)
            scaled_height = int(preview_height * scale)
            preview = pygame.transform.scale(self.preview_surface, (scaled_width, scaled_height))
        else:
            preview = self.preview_surface
            scaled_width = preview_width
            scaled_height = preview_height
        
        # Center on screen
        preview_x = (screen_width - scaled_width) // 2
        preview_y = (screen_height - scaled_height) // 2
        
        # Draw semi-transparent background
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw preview
        self.screen.blit(preview, (preview_x, preview_y))
        
        # Draw title
        title_font = pygame.font.Font(None, 36)
        if self.preview_tileset_index is not None and self.preview_tileset_index < len(self.tilesets):
            tileset = self.tilesets[self.preview_tileset_index]
            title_text = title_font.render(f"Preview: {tileset['name']}", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(screen_width // 2, preview_y - 30))
            self.screen.blit(title_text, title_rect)
    
    def _load_preview(self, tileset_index: int):
        """Load preview image for a tileset."""
        if tileset_index < 0 or tileset_index >= len(self.tilesets):
            return None
        
        tileset = self.tilesets[tileset_index]
        preview_path = tileset.get('preview_path')
        
        if preview_path and os.path.exists(preview_path):
            try:
                preview = pygame.image.load(preview_path).convert_alpha()
                return preview
            except Exception as e:
                print(f"Error loading preview: {e}")
                return None
        return None

