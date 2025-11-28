"""
Save list screen for selecting saved games.
"""
import pygame
import os
from typing import List, Optional, Tuple
from save_game import get_saved_games, load_game
from settlements import Settlement, SettlementType
from celtic_calendar import CelticCalendar
from datetime import datetime


def find_nearest_settlement(player_x: int, player_y: int, settlements: List[Settlement]) -> Optional[Tuple[Settlement, str]]:
    """
    Find the nearest city or town to the player position.
    
    Args:
        player_x: Player X position
        player_y: Player Y position
        settlements: List of all settlements
        
    Returns:
        Tuple of (nearest_settlement, description) or None if no settlements
    """
    if not settlements:
        return None
    
    # Filter to cities and towns only
    cities_and_towns = [s for s in settlements if s.settlement_type in (SettlementType.CITY, SettlementType.TOWN)]
    
    if not cities_and_towns:
        return None
    
    # Find nearest
    nearest = None
    min_distance = float('inf')
    
    for settlement in cities_and_towns:
        sx, sy = settlement.get_position()
        # Use Manhattan distance
        distance = abs(sx - player_x) + abs(sy - player_y)
        if distance < min_distance:
            min_distance = distance
            nearest = settlement
    
    if not nearest:
        return None
    
    # Create description
    if nearest.settlement_type == SettlementType.CITY:
        description = f"Near the city of {nearest.name}"
    elif nearest.vassal_to is None:
        # Independent town
        description = f"Near the free town of {nearest.name}"
    else:
        # Town with a city
        description = f"Near the town of {nearest.name}"
    
    return (nearest, description)


class SaveListScreen:
    """Displays a list of saved games for selection."""
    
    def __init__(self, screen: pygame.Surface, settlements: List[Settlement] = None):
        """
        Initialize the save list screen.
        
        Args:
            screen: Pygame surface to draw on
            settlements: List of settlements (for finding nearest city/town)
        """
        self.screen = screen
        self.settlements = settlements or []
        self.saved_games = []
        self.selected_save_index = 0
        self.save_rects = []  # List of (rect, index) tuples for click detection
        
        # Back button
        self.back_button_rect = None
        
        # Load saved games immediately
        self._load_saved_games()
    
    def set_settlements(self, settlements: List[Settlement]):
        """Update settlements list (called after map is loaded)."""
        self.settlements = settlements
        # Reload saved games to update location info
        self._load_saved_games()
    
    def _load_saved_games(self):
        """Load the list of saved games."""
        try:
            self.saved_games = get_saved_games()
            print(f"Debug: Found {len(self.saved_games)} saved games")
        except Exception as e:
            print(f"Error getting saved games: {e}")
            self.saved_games = []
            return
        
        # Add metadata for display
        for filepath, save_data in self.saved_games:
            try:
                # Get game date/time
                calendar = CelticCalendar(
                    year=save_data.get('calendar_year', 1),
                    month=save_data.get('calendar_month', 1),
                    day=save_data.get('calendar_day', 1),
                    hour=save_data.get('calendar_hour', 6)
                )
                game_datetime = calendar.get_full_datetime_string()
                
                # Get save timestamp
                save_timestamp = save_data.get('save_timestamp', '')
                if save_timestamp:
                    try:
                        dt = datetime.fromisoformat(save_timestamp)
                        save_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        save_datetime = "Unknown"
                else:
                    save_datetime = "Unknown"
                
                # Find nearest settlement
                player_x = save_data.get('player_x', 0)
                player_y = save_data.get('player_y', 0)
                nearest_info = find_nearest_settlement(player_x, player_y, self.settlements)
                
                if nearest_info:
                    nearest_settlement, description = nearest_info
                    location_text = description
                else:
                    location_text = "Unknown location"
                
                # Store display info
                save_data['display_game_datetime'] = game_datetime
                save_data['display_save_datetime'] = save_datetime
                save_data['display_location'] = location_text
            except Exception as e:
                print(f"Error processing save file {filepath}: {e}")
                import traceback
                traceback.print_exc()
                # Set default values if processing fails
                save_data['display_game_datetime'] = "Unknown"
                save_data['display_save_datetime'] = "Unknown"
                save_data['display_location'] = "Unknown location"
    
    def render(self):
        """Render the save list screen."""
        self.screen.fill((20, 20, 30))
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Load Saved Game", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen_width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        font = pygame.font.Font(None, 24)
        instruction_text = font.render("Select a saved game to load", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Back button
        back_font = pygame.font.Font(None, 32)
        back_text = back_font.render("BACK (ESC)", True, (255, 255, 255))
        back_width = back_text.get_width() + 20
        back_height = back_text.get_height() + 10
        back_x = 20
        back_y = screen_height - back_height - 20
        self.back_button_rect = pygame.Rect(back_x, back_y, back_width, back_height)
        pygame.draw.rect(self.screen, (60, 60, 80), self.back_button_rect)
        pygame.draw.rect(self.screen, (150, 150, 150), self.back_button_rect, 2)
        self.screen.blit(back_text, (back_x + 10, back_y + 5))
        
        # List of saved games
        if not self.saved_games:
            no_saves_font = pygame.font.Font(None, 32)
            no_saves_text = no_saves_font.render("No saved games found", True, (150, 150, 150))
            no_saves_rect = no_saves_text.get_rect(center=(screen_width // 2, screen_height // 2))
            self.screen.blit(no_saves_text, no_saves_rect)
            # Debug: show count
            debug_font = pygame.font.Font(None, 20)
            debug_text = debug_font.render(f"Debug: saved_games list has {len(self.saved_games)} items", True, (100, 100, 100))
            self.screen.blit(debug_text, (10, screen_height - 40))
            return
        
        # Display saves
        item_font = pygame.font.Font(None, 28)
        detail_font = pygame.font.Font(None, 20)
        
        start_y = 150
        item_height = 80
        spacing = 10
        max_items = (screen_height - start_y - 100) // (item_height + spacing)
        
        # Show items around selected index
        visible_start = max(0, self.selected_save_index - max_items // 2)
        visible_end = min(len(self.saved_games), visible_start + max_items)
        
        self.save_rects = []
        y_offset = start_y
        
        for i in range(visible_start, visible_end):
            filepath, save_data = self.saved_games[i]
            
            # Highlight selected item
            is_selected = (i == self.selected_save_index)
            bg_color = (80, 80, 100) if is_selected else (40, 40, 50)
            border_color = (255, 255, 0) if is_selected else (100, 100, 100)
            
            # Item rectangle
            item_rect = pygame.Rect(50, y_offset, screen_width - 100, item_height)
            pygame.draw.rect(self.screen, bg_color, item_rect)
            pygame.draw.rect(self.screen, border_color, item_rect, 2)
            
            self.save_rects.append((item_rect, i))
            
            # Game date/time (main text)
            game_datetime = save_data.get('display_game_datetime', 'Unknown')
            game_text = item_font.render(game_datetime, True, (255, 255, 255))
            self.screen.blit(game_text, (item_rect.x + 10, item_rect.y + 5))
            
            # Save date/time (in parentheses)
            save_datetime = save_data.get('display_save_datetime', 'Unknown')
            save_text = detail_font.render(f"({save_datetime})", True, (180, 180, 180))
            self.screen.blit(save_text, (item_rect.x + 10, item_rect.y + 35))
            
            # Location
            location_text = save_data.get('display_location', 'Unknown location')
            location_surface = detail_font.render(location_text, True, (200, 200, 255))
            self.screen.blit(location_surface, (item_rect.x + 10, item_rect.y + 55))
            
            y_offset += item_height + spacing
        
        # Scroll indicators
        if visible_start > 0:
            up_arrow = detail_font.render("↑", True, (150, 150, 150))
            self.screen.blit(up_arrow, (screen_width - 30, start_y))
        if visible_end < len(self.saved_games):
            down_arrow = detail_font.render("↓", True, (150, 150, 150))
            self.screen.blit(down_arrow, (screen_width - 30, screen_height - 100))
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Tuple[str, str]]:
        """
        Handle pygame events.
        
        Returns:
            ('load', filepath) if a save should be loaded,
            'back' if should go back,
            None otherwise
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'back'
            elif event.key == pygame.K_UP:
                if self.selected_save_index > 0:
                    self.selected_save_index -= 1
            elif event.key == pygame.K_DOWN:
                if self.selected_save_index < len(self.saved_games) - 1:
                    self.selected_save_index += 1
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Load selected save
                if self.saved_games and 0 <= self.selected_save_index < len(self.saved_games):
                    filepath, save_data = self.saved_games[self.selected_save_index]
                    return ('load', filepath)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = event.pos
                
                # Check BACK button
                if self.back_button_rect and self.back_button_rect.collidepoint(mouse_x, mouse_y):
                    return 'back'
                
                # Check save items
                for save_rect, index in self.save_rects:
                    if save_rect.collidepoint(mouse_x, mouse_y):
                        # Select this save and load it
                        self.selected_save_index = index
                        if self.saved_games and 0 <= index < len(self.saved_games):
                            filepath, save_data = self.saved_games[index]
                            return ('load', filepath)
        
        return None

