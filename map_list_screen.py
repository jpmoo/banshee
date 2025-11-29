"""
Map list screen for selecting saved maps.
"""
import pygame
import os
from typing import List, Optional, Tuple
from map_saver import get_saved_maps
from save_game import get_saved_games
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
        
        # Delete confirmation dialog
        self.pending_delete_index = None
        self.confirm_dialog_rect = None
        self.confirm_yes_rect = None
        self.confirm_no_rect = None
        
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
        # Handle confirmation dialog first
        if self.pending_delete_index is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    # Confirm delete
                    self._delete_map_file(self.pending_delete_index)
                    self.pending_delete_index = None
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    # Cancel delete
                    self.pending_delete_index = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    if self.confirm_yes_rect and self.confirm_yes_rect.collidepoint(mouse_x, mouse_y):
                        # Confirm delete
                        self._delete_map_file(self.pending_delete_index)
                        self.pending_delete_index = None
                    elif self.confirm_no_rect and self.confirm_no_rect.collidepoint(mouse_x, mouse_y):
                        # Cancel delete
                        self.pending_delete_index = None
            return None  # Don't process other events while dialog is open
        
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
            elif event.key == pygame.K_x:
                # Delete selected map
                if self.saved_maps and 0 <= self.selected_map_index < len(self.saved_maps):
                    self.pending_delete_index = self.selected_map_index
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
    
    def _get_saves_using_map(self, map_filepath: str) -> List[str]:
        """Get list of save file paths that use the specified map file."""
        saves_using_map = []
        try:
            saved_games = get_saved_games()
            game_dir = os.getcwd()
            
            # Normalize the map filepath for comparison
            if not os.path.isabs(map_filepath):
                map_filepath_abs = os.path.join(game_dir, map_filepath)
            else:
                map_filepath_abs = map_filepath
            
            for save_filepath, save_data in saved_games:
                if 'map_filepath' in save_data:
                    save_map_path = save_data['map_filepath']
                    # Convert to absolute for comparison
                    if not os.path.isabs(save_map_path):
                        save_map_path_abs = os.path.join(game_dir, save_map_path)
                    else:
                        save_map_path_abs = save_map_path
                    
                    # Compare normalized paths
                    if os.path.normpath(save_map_path_abs) == os.path.normpath(map_filepath_abs):
                        saves_using_map.append(save_filepath)
        except Exception as e:
            print(f"Error checking saves for map: {e}")
        
        return saves_using_map
    
    def _draw_delete_confirmation_dialog(self):
        """Draw the delete confirmation dialog."""
        if self.pending_delete_index is None or self.pending_delete_index >= len(self.saved_maps):
            return
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        filepath, map_name, seed = self.saved_maps[self.pending_delete_index]
        
        # Check for saves using this map
        saves_using_map = self._get_saves_using_map(filepath)
        num_saves = len(saves_using_map)
        
        # Dialog dimensions - make taller if there are saves to warn about
        dialog_width = 600
        dialog_height = 250 if num_saves > 0 else 200
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        self.confirm_dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw dialog background
        pygame.draw.rect(self.screen, (40, 40, 50), self.confirm_dialog_rect)
        pygame.draw.rect(self.screen, (255, 100, 100), self.confirm_dialog_rect, 3)
        
        # Dialog text
        font = pygame.font.Font(None, 28)
        title_font = pygame.font.Font(None, 32)
        warning_font = pygame.font.Font(None, 24)
        
        title_text = title_font.render("Delete Map?", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 40))
        self.screen.blit(title_text, title_rect)
        
        confirm_text = font.render(f"Delete map '{map_name}'?", True, (200, 200, 200))
        confirm_rect = confirm_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 80))
        self.screen.blit(confirm_text, confirm_rect)
        
        # Warning about saves
        if num_saves > 0:
            warning_text = warning_font.render(
                f"WARNING: This will also delete {num_saves} save file(s) using this map!",
                True, (255, 150, 150)
            )
            warning_rect = warning_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 120))
            self.screen.blit(warning_text, warning_rect)
        
        # Yes button
        yes_text = font.render("Yes (Y)", True, (255, 255, 255))
        yes_width = 120
        yes_height = 40
        yes_x = dialog_x + dialog_width // 2 - yes_width - 10
        yes_y = dialog_y + dialog_height - yes_height - 20
        self.confirm_yes_rect = pygame.Rect(yes_x, yes_y, yes_width, yes_height)
        pygame.draw.rect(self.screen, (200, 60, 60), self.confirm_yes_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.confirm_yes_rect, 2)
        yes_text_rect = yes_text.get_rect(center=self.confirm_yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_text = font.render("No (N)", True, (255, 255, 255))
        no_width = 120
        no_height = 40
        no_x = dialog_x + dialog_width // 2 + 10
        no_y = dialog_y + dialog_height - no_height - 20
        self.confirm_no_rect = pygame.Rect(no_x, no_y, no_width, no_height)
        pygame.draw.rect(self.screen, (60, 60, 80), self.confirm_no_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.confirm_no_rect, 2)
        no_text_rect = no_text.get_rect(center=self.confirm_no_rect.center)
        self.screen.blit(no_text, no_text_rect)
    
    def _delete_map_file(self, index: int):
        """Delete a map file and any associated save files."""
        if index < 0 or index >= len(self.saved_maps):
            return
        
        filepath, map_name, seed = self.saved_maps[index]
        
        # Get saves using this map
        saves_using_map = self._get_saves_using_map(filepath)
        
        try:
            # Delete associated save files first
            for save_filepath in saves_using_map:
                if os.path.exists(save_filepath):
                    os.remove(save_filepath)
                    print(f"Deleted save file: {save_filepath}")
            
            # Delete the map file
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted map file: {filepath}")
                if saves_using_map:
                    print(f"Also deleted {len(saves_using_map)} associated save file(s)")
            
            # Reload saved maps
            self._load_saved_maps()
            # Adjust selected index if needed
            if self.selected_map_index >= len(self.saved_maps):
                self.selected_map_index = max(0, len(self.saved_maps) - 1)
        except Exception as e:
            print(f"Error deleting map file: {e}")
    
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
                
                # Delete/Open note
                note_text = "[X] Delete or [ENTER] to Open"
                note_surface = seed_font.render(note_text, True, (150, 150, 150))
                note_x = item_rect.right - note_surface.get_width() - 10
                self.screen.blit(note_surface, (note_x, y_pos + 30))
        
        # Draw confirmation dialog if pending delete
        if self.pending_delete_index is not None:
            self._draw_delete_confirmation_dialog()
        
        # Update display
        pygame.display.flip()

