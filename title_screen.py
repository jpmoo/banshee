"""
Title screen with progress bar for map generation.
"""
import pygame
from typing import Callable, Optional


class TitleScreen:
    """Displays a title screen with progress updates."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the title screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.progress = 0.0
        self.message = "Initializing..."
        
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
        
    def update_progress(self, progress: float, message: str):
        """
        Update the progress bar and message.
        
        Args:
            progress: Progress value from 0.0 to 1.0
            message: Status message to display
        """
        self.progress = max(0.0, min(1.0, progress))
        self.message = message
    
    def render(self):
        """Render the title screen."""
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
        subtitle_font = pygame.font.Font(None, 32)
        subtitle_text = subtitle_font.render("Map Generation", True, (150, 150, 150))
        subtitle_y = title_bottom + 30
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, subtitle_y))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Progress message - positioned below subtitle
        message_font = pygame.font.Font(None, 28)
        message_text = message_font.render(self.message, True, (255, 255, 255))
        message_y = subtitle_y + 80
        message_rect = message_text.get_rect(center=(self.width // 2, message_y))
        self.screen.blit(message_text, message_rect)
        
        # Progress bar background - positioned below message
        bar_width = self.width * 0.6
        bar_height = 30
        bar_x = (self.width - bar_width) // 2
        bar_y = message_y + 50
        
        # Draw progress bar background
        bar_bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bar_bg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), bar_bg_rect, 2)
        
        # Draw progress bar fill
        fill_width = int(bar_width * self.progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            # Gradient effect
            for i in range(fill_width):
                color_ratio = i / bar_width if bar_width > 0 else 0
                r = int(50 + (200 - 50) * color_ratio)
                g = int(50 + (150 - 50) * color_ratio)
                b = int(50 + (255 - 50) * color_ratio)
                pygame.draw.line(self.screen, (r, g, b), 
                               (bar_x + i, bar_y), (bar_x + i, bar_y + bar_height))
        
        # Progress percentage
        percent_font = pygame.font.Font(None, 24)
        percent_text = percent_font.render(f"{int(self.progress * 100)}%", True, (200, 200, 200))
        percent_rect = percent_text.get_rect(center=(self.width // 2, bar_y + bar_height + 30))
        self.screen.blit(percent_text, percent_rect)
        
        # Instructions - positioned well below progress bar to avoid overlap
        instruction_font = pygame.font.Font(None, 20)
        instruction_text = instruction_font.render("Please wait while the map is being generated...", 
                                                 True, (120, 120, 120))
        # Position below progress percentage with good spacing
        instruction_y = bar_y + bar_height + 80
        instruction_rect = instruction_text.get_rect(center=(self.width // 2, instruction_y))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Update display
        pygame.display.flip()


