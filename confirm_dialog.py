"""
Confirmation dialog for various actions.
"""
import pygame
from typing import Optional


def show_confirm_dialog(screen: pygame.Surface, clock: pygame.time.Clock,
                        message: str, warning: Optional[str] = None) -> bool:
    """
    Show a confirmation dialog with a message and optional warning.
    
    Args:
        screen: Pygame surface to draw on
        clock: Pygame clock for timing
        message: Main message to display
        warning: Optional warning message to display
        
    Returns:
        True if confirmed, False if cancelled
    """
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Dialog dimensions
    dialog_width = min(500, int(screen_width * 0.7))
    dialog_height = min(200, int(screen_height * 0.3))
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    # Fonts
    title_font = pygame.font.Font(None, 32)
    body_font = pygame.font.Font(None, 22)
    warning_font = pygame.font.Font(None, 20)
    
    waiting = True
    confirmed = False
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y or event.key == pygame.K_RETURN:
                    confirmed = True
                    waiting = False
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    confirmed = False
                    waiting = False
        
        # Draw dialog
        screen.fill((20, 20, 30))  # Dark background
        
        # Dialog background
        pygame.draw.rect(screen, (40, 40, 50), dialog_rect)
        pygame.draw.rect(screen, (200, 200, 200), dialog_rect, 2)
        
        # Message
        y_offset = dialog_y + 30
        message_surface = body_font.render(message, True, (200, 200, 200))
        message_rect = message_surface.get_rect(center=(dialog_x + dialog_width // 2, y_offset))
        screen.blit(message_surface, message_rect)
        y_offset += 40
        
        # Warning if provided
        if warning:
            warning_surface = warning_font.render(warning, True, (255, 200, 100))
            warning_rect = warning_surface.get_rect(center=(dialog_x + dialog_width // 2, y_offset))
            screen.blit(warning_surface, warning_rect)
            y_offset += 30
        
        # Instructions
        instruction_text = "Press Y/ENTER to confirm, N/ESC to cancel"
        instruction_surface = warning_font.render(instruction_text, True, (150, 150, 150))
        instruction_rect = instruction_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + dialog_height - 30))
        screen.blit(instruction_surface, instruction_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return confirmed

