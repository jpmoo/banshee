"""
Simple dialog functions for user notifications.
"""
import pygame


def show_message_dialog(screen: pygame.Surface, clock: pygame.time.Clock, 
                       title: str, message: str, button_text: str = "OK") -> bool:
    """
    Show a simple message dialog and wait for user to press a key or click.
    
    Args:
        screen: Pygame surface to draw on
        clock: Pygame clock for timing
        title: Dialog title
        message: Dialog message (can be multi-line, use \\n)
        button_text: Text for the button/key prompt
        
    Returns:
        True when user dismisses the dialog
    """
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Dialog dimensions
    dialog_width = min(600, int(screen_width * 0.8))
    dialog_height = min(400, int(screen_height * 0.6))
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    # Fonts
    title_font = pygame.font.Font(None, 36)
    message_font = pygame.font.Font(None, 24)
    button_font = pygame.font.Font(None, 20)
    
    # Split message into lines
    message_lines = message.split('\n')
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if dialog_rect.collidepoint(event.pos):
                    waiting = False
        
        # Draw dialog
        screen.fill((20, 20, 30))  # Dark background
        
        # Dialog background
        pygame.draw.rect(screen, (40, 40, 50), dialog_rect)
        pygame.draw.rect(screen, (200, 200, 200), dialog_rect, 2)
        
        # Title
        title_surface = title_font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 40))
        screen.blit(title_surface, title_rect)
        
        # Message lines
        y_offset = dialog_y + 80
        for line in message_lines:
            if line.strip():  # Skip empty lines
                line_surface = message_font.render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(dialog_x + dialog_width // 2, y_offset))
                screen.blit(line_surface, line_rect)
                y_offset += 30
        
        # Button prompt
        button_surface = button_font.render(f"Press {button_text} to continue", True, (150, 150, 150))
        button_rect = button_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + dialog_height - 40))
        screen.blit(button_surface, button_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

