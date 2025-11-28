"""
Map list screen for selecting saved maps.
"""
import pygame
import os
from typing import List, Optional, Tuple
from map_saver import get_saved_maps
from datetime import datetime


class MapListScreen:
    """Displays a list of saved maps for selection."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the map list screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.screen = screen
        self.saved_maps = []
        self.selected_map_index = 0
        self.map_rects = []  # List of (rect, index) tuples for click detection
        
        # Back button
        self.back_button_rect = None
        
        # Load saved maps immediately
        self._load_saved_maps()
    
    def _load_saved_maps(self):
        """Load the list of saved maps."""
        try:
            self.saved_maps = get_saved_maps()
            print(f"Debug: Found {len(self.saved_maps)} saved maps")
        except Exception as e:
            print(f"Error getting saved maps: {e}")
            self.saved_maps = []
            return
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle a pygame event.
        
        Args:
            event: Pygame event
            
        Returns:
            'back' if user wants to go back,
            ('load', filepath) if user selected a map,
            None if event was handled but no action needed
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'back'
            elif event.key == pygame.K_UP:
                if self.selected_map_index > 0:
                    self.selected_map_index -= 1
            elif event.key == pygame.K_DOWN:
                if self.selected_map_index < len(self.saved_maps) - 1:
                    self.selected_map_index += 1
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.saved_maps:
                    filepath, map_name, seed = self.saved_maps[self.selected_map_index]
                    return ('load', filepath)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = event.pos
                
                # Check back button
                if self.back_button_rect and self.back_button_rect.collidepoint(mouse_x, mouse_y):
                    return 'back'
                
                # Check map list items
                for rect, index in self.map_rects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.selected_map_index = index
                        filepath, map_name, seed = self.saved_maps[index]
                        return ('load', filepath)
        
        return None
    
    def render(self):
        """Render the map list screen."""
        self.screen.fill((20, 20, 30))
        
        # Fonts
        title_font = pygame.font.Font(None, 48)
        item_font = pygame.font.Font(None, 32)
        info_font = pygame.font.Font(None, 24)
        seed_font = pygame.font.Font(None, 20)
        
        # Title
        title_text = title_font.render("Load Map", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        instructions = [
            "Arrow Keys: Navigate",
            "Enter/Space: Load selected map",
            "ESC: Back to menu"
        ]
        y_offset = 100
        for instruction in instructions:
            inst_text = info_font.render(instruction, True, (180, 180, 180))
            self.screen.blit(inst_text, (50, y_offset))
            y_offset += 25
        
        # Back button
        button_font = pygame.font.Font(None, 32)
        back_text = button_font.render("BACK (ESC)", True, (200, 200, 200))
        back_button_width = 150
        back_button_height = 40
        back_button_x = 20
        back_button_y = 20
        self.back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        
        # Draw button background
        pygame.draw.rect(self.screen, (60, 60, 80), self.back_button_rect)
        pygame.draw.rect(self.screen, (150, 150, 150), self.back_button_rect, 2)
        
        # Draw button text
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_text_rect)
        
        # List of saved maps
        self.map_rects = []
        if not self.saved_maps:
            no_maps_text = item_font.render("No saved maps found", True, (150, 150, 150))
            no_maps_rect = no_maps_text.get_rect(center=(self.screen.get_width() // 2, 
                                                         self.screen.get_height() // 2))
            self.screen.blit(no_maps_text, no_maps_rect)
        else:
            start_y = 200
            item_height = 60
            visible_items = min(8, len(self.saved_maps))
            
            # Calculate which items to show (scroll if needed)
            start_index = max(0, min(self.selected_map_index - visible_items // 2, 
                                    len(self.saved_maps) - visible_items))
            
            for i in range(start_index, min(start_index + visible_items, len(self.saved_maps))):
                filepath, map_name, seed = self.saved_maps[i]
                y_pos = start_y + (i - start_index) * item_height
                
                # Create clickable rect
                item_rect = pygame.Rect(50, y_pos - 5, self.screen.get_width() - 100, item_height)
                self.map_rects.append((item_rect, i))
                
                # Highlight selected item
                if i == self.selected_map_index:
                    pygame.draw.rect(self.screen, (60, 60, 80), item_rect)
                    pygame.draw.rect(self.screen, (100, 150, 255), item_rect, 2)
                
                # Render map name
                map_text = item_font.render(map_name, True, (255, 255, 255))
                self.screen.blit(map_text, (70, y_pos))
                
                # Render seed info if available
                if seed is not None:
                    seed_text = seed_font.render(f"Seed: {seed}", True, (150, 150, 150))
                    self.screen.blit(seed_text, (70, y_pos + 30))
                else:
                    seed_text = seed_font.render("Seed: Random", True, (150, 150, 150))
                    self.screen.blit(seed_text, (70, y_pos + 30))
        
        # Update display
        pygame.display.flip()

