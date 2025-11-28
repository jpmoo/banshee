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
        # Store rects for mouse click detection
        self.option1_rect = None
        self.option2_rect = None
        self.back_button_rect = None
        
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
        self.option1_rect = option1_surface.get_rect(center=(self.width // 2, y_start))
        # Expand rect for easier clicking
        clickable_rect1 = pygame.Rect(
            self.option1_rect.x - 20,
            self.option1_rect.y - 10,
            self.option1_rect.width + 40,
            self.option1_rect.height + 20
        )
        
        # Highlight selected option
        if self.selected_option == 0:
            pygame.draw.rect(self.screen, (50, 50, 80), clickable_rect1)
            pygame.draw.rect(self.screen, (100, 100, 150), clickable_rect1, 2)
        
        self.screen.blit(option1_surface, self.option1_rect)
        
        # Option 2: Load Existing Map
        option2_text = "Load Existing Map"
        option2_color = (255, 255, 255) if self.selected_option == 1 else (150, 150, 150)
        option2_surface = option_font.render(option2_text, True, option2_color)
        self.option2_rect = option2_surface.get_rect(center=(self.width // 2, y_start + 80))
        # Expand rect for easier clicking
        clickable_rect2 = pygame.Rect(
            self.option2_rect.x - 20,
            self.option2_rect.y - 10,
            self.option2_rect.width + 40,
            self.option2_rect.height + 20
        )
        
        # Highlight selected option
        if self.selected_option == 1:
            pygame.draw.rect(self.screen, (50, 50, 80), clickable_rect2)
            pygame.draw.rect(self.screen, (100, 100, 150), clickable_rect2, 2)
        
        self.screen.blit(option2_surface, self.option2_rect)
        
        # Draw BACK/ESC button
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
            'load_maps' if load existing map selected (to show map list screen),
            'back' if ESC pressed or BACK button clicked,
            None if no action taken
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'back'
            elif event.key == pygame.K_UP:
                # Switch to previous option
                self.selected_option = (self.selected_option - 1) % 2
            elif event.key == pygame.K_DOWN:
                # Switch to next option
                self.selected_option = (self.selected_option + 1) % 2
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.selected_option == 0:
                    return 'generate'
                elif self.selected_option == 1:
                    # Load existing map - go to map list screen
                    return 'load_maps'
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = event.pos
                
                # Check BACK button
                if self.back_button_rect and self.back_button_rect.collidepoint(mouse_x, mouse_y):
                    return 'back'
                
                # Check option 1
                if self.option1_rect:
                    clickable_rect1 = pygame.Rect(
                        self.option1_rect.x - 20,
                        self.option1_rect.y - 10,
                        self.option1_rect.width + 40,
                        self.option1_rect.height + 20
                    )
                    if clickable_rect1.collidepoint(mouse_x, mouse_y):
                        return 'generate'
                
                # Check option 2
                if self.option2_rect:
                    clickable_rect2 = pygame.Rect(
                        self.option2_rect.x - 20,
                        self.option2_rect.y - 10,
                        self.option2_rect.width + 40,
                        self.option2_rect.height + 20
                    )
                    if clickable_rect2.collidepoint(mouse_x, mouse_y):
                        return 'load_maps'
        
        return None


