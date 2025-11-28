"""
Map menu screen for choosing to load or generate a new map.
"""
import pygame
import os
from typing import Optional, List
from map_saver import get_saved_maps


class MapMenuScreen:
    """Displays a menu for loading or generating a map."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the map menu screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.selected_option = 0  # 0 = Generate New, 1 = Load Existing
        self.saved_maps = get_saved_maps()
        self.selected_map_index = 0 if self.saved_maps else -1
        self.show_map_list = False
        
        # Load title image
        self.title_image = None
        try:
            title_img = pygame.image.load("title.png")
            # Scale to fit nicely at the top (about 30% of screen width)
            target_width = int(self.width * 0.3)
            aspect_ratio = title_img.get_height() / title_img.get_width()
            target_height = int(target_width * aspect_ratio)
            self.title_image = pygame.transform.scale(title_img, (target_width, target_height))
        except (pygame.error, FileNotFoundError):
            self.title_image = None
        
    def render(self):
        """Render the map menu screen."""
        # Clear screen with dark background
        self.screen.fill((20, 20, 30))
        
        # Title image or text - fixed top position (top edge at 60px from top)
        title_top = 60
        if self.title_image:
            title_rect = self.title_image.get_rect(midtop=(self.width // 2, title_top))
            self.screen.blit(self.title_image, title_rect)
            title_bottom = title_rect.bottom
        else:
            # Fallback to text if image not found
            title_font = pygame.font.Font(None, 72)
            title_text = title_font.render("BANSHEE RPG", True, (200, 50, 50))
            title_rect = title_text.get_rect(midtop=(self.width // 2, title_top))
            self.screen.blit(title_text, title_rect)
            title_bottom = title_rect.bottom
        
        # Subtitle - positioned below title with spacing
        subtitle_font = pygame.font.Font(None, 36)
        subtitle_text = subtitle_font.render("Map Selection", True, (150, 150, 150))
        subtitle_y = title_bottom + 50
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, subtitle_y))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options - positioned below subtitle with proper spacing
        option_font = pygame.font.Font(None, 48)
        small_font = pygame.font.Font(None, 32)
        
        y_start = subtitle_y + 80  # Start menu options below subtitle
        
        # Option 1: Generate New Map
        option1_text = "Generate New Map"
        option1_color = (255, 255, 255) if self.selected_option == 0 else (150, 150, 150)
        option1_surface = option_font.render(option1_text, True, option1_color)
        option1_rect = option1_surface.get_rect(center=(self.width // 2, y_start))
        
        # Highlight selected option
        if self.selected_option == 0:
            highlight_rect = pygame.Rect(
                option1_rect.x - 20,
                option1_rect.y - 10,
                option1_rect.width + 40,
                option1_rect.height + 20
            )
            pygame.draw.rect(self.screen, (50, 50, 80), highlight_rect)
            pygame.draw.rect(self.screen, (100, 100, 150), highlight_rect, 2)
        
        self.screen.blit(option1_surface, option1_rect)
        
        # Option 2: Load Existing Map
        option2_text = "Load Existing Map"
        option2_color = (255, 255, 255) if self.selected_option == 1 else (150, 150, 150)
        option2_surface = option_font.render(option2_text, True, option2_color)
        option2_rect = option2_surface.get_rect(center=(self.width // 2, y_start + 80))
        
        # Highlight selected option
        if self.selected_option == 1:
            highlight_rect = pygame.Rect(
                option2_rect.x - 20,
                option2_rect.y - 10,
                option2_rect.width + 40,
                option2_rect.height + 20
            )
            pygame.draw.rect(self.screen, (50, 50, 80), highlight_rect)
            pygame.draw.rect(self.screen, (100, 100, 150), highlight_rect, 2)
        
        self.screen.blit(option2_surface, option2_rect)
        
        # Show map list if "Load Existing Map" is selected
        if self.selected_option == 1:
            if not self.saved_maps:
                no_maps_text = small_font.render("No saved maps found", True, (200, 200, 200))
                no_maps_rect = no_maps_text.get_rect(center=(self.width // 2, y_start + 160))
                self.screen.blit(no_maps_text, no_maps_rect)
            else:
                # Show map list
                list_y = y_start + 160
                list_font = pygame.font.Font(None, 28)
                
                list_title = small_font.render("Saved Maps (UP/DOWN to select, ENTER to load):", 
                                              True, (200, 200, 200))
                self.screen.blit(list_title, (self.width // 2 - list_title.get_width() // 2, list_y))
                list_y += 40
                
                # Show up to 8 maps
                visible_maps = self.saved_maps[:8]
                for i, map_path in enumerate(visible_maps):
                    map_name = os.path.basename(map_path)
                    if i == self.selected_map_index:
                        map_color = (255, 255, 100)
                        # Highlight selected map
                        map_rect = pygame.Rect(
                            self.width // 2 - 200,
                            list_y - 5,
                            400,
                            30
                        )
                        pygame.draw.rect(self.screen, (50, 50, 80), map_rect)
                        pygame.draw.rect(self.screen, (100, 100, 150), map_rect, 2)
                    else:
                        map_color = (200, 200, 200)
                    
                    map_text = list_font.render(f"{i + 1}. {map_name}", True, map_color)
                    self.screen.blit(map_text, (self.width // 2 - map_text.get_width() // 2, list_y))
                    list_y += 35
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "UP/DOWN: Navigate options",
            "ENTER: Select",
            "ESC: Back to main menu"
        ]
        y_offset = self.height - 100
        for instruction in instructions:
            instruction_text = instruction_font.render(instruction, True, (120, 120, 120))
            instruction_rect = instruction_text.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(instruction_text, instruction_rect)
            y_offset += 25
        
        # Update display
        pygame.display.flip()
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle a pygame event.
        
        Args:
            event: Pygame event
            
        Returns:
            'generate' if generate new map selected,
            'load' if load map selected (with filepath),
            'back' if ESC pressed,
            None if no action taken
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'back'
            elif event.key == pygame.K_UP:
                if self.selected_option == 1 and self.saved_maps:
                    # Navigate map list
                    self.selected_map_index = max(0, self.selected_map_index - 1)
                else:
                    # Switch to previous option
                    self.selected_option = (self.selected_option - 1) % 2
                    if self.selected_option == 1 and self.saved_maps:
                        self.selected_map_index = 0
            elif event.key == pygame.K_DOWN:
                if self.selected_option == 1 and self.saved_maps:
                    # Navigate map list
                    max_index = min(len(self.saved_maps) - 1, 7)  # Show up to 8 maps
                    self.selected_map_index = min(max_index, self.selected_map_index + 1)
                else:
                    # Switch to next option
                    self.selected_option = (self.selected_option + 1) % 2
                    if self.selected_option == 1 and self.saved_maps:
                        self.selected_map_index = 0
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.selected_option == 0:
                    return 'generate'
                elif self.selected_option == 1 and self.saved_maps:
                    if 0 <= self.selected_map_index < len(self.saved_maps):
                        return ('load', self.saved_maps[self.selected_map_index])
        
        return None


