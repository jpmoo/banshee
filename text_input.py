"""
Text input functionality for getting user input in pygame.
"""
import pygame
from typing import Optional


def get_text_input(screen: pygame.Surface, prompt: str, default: str = "", 
                   max_length: int = 50) -> Optional[str]:
    """
    Get text input from the user.
    
    Args:
        screen: Pygame surface to draw on
        prompt: Prompt message to display
        default: Default text value
        max_length: Maximum length of input
        
    Returns:
        Entered text string, or None if cancelled
    """
    clock = pygame.time.Clock()
    input_text = default
    cursor_visible = True
    cursor_timer = 0
    
    # Fonts
    prompt_font = pygame.font.Font(None, 36)
    input_font = pygame.font.Font(None, 32)
    
    running = True
    result = None
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Update cursor blink
        cursor_timer += dt
        if cursor_timer >= 0.5:  # Blink every 0.5 seconds
            cursor_visible = not cursor_visible
            cursor_timer = 0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Enter pressed - confirm input
                    result = input_text
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    # Escape pressed - cancel
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    # Backspace - remove last character
                    input_text = input_text[:-1]
                elif event.unicode and len(input_text) < max_length:
                    # Add character if printable and within max length
                        if event.unicode.isprintable() and ord(event.unicode) < 128:
                            input_text += event.unicode
        
        # Render
        screen.fill((20, 20, 30))
        
        # Draw prompt (handle line breaks)
        prompt_lines = prompt.split('\n')
        prompt_y = screen.get_height() // 2 - 50 - (len(prompt_lines) - 1) * 20
        for i, line in enumerate(prompt_lines):
            prompt_surface = prompt_font.render(line, True, (255, 255, 255))
        prompt_rect = prompt_surface.get_rect(center=(screen.get_width() // 2, 
                                                          prompt_y + i * 40))
        screen.blit(prompt_surface, prompt_rect)
        
        # Draw input box
        input_box_width = min(600, screen.get_width() - 100)
        input_box_height = 50
        input_box_x = (screen.get_width() - input_box_width) // 2
        input_box_y = screen.get_height() // 2
        
        input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
        pygame.draw.rect(screen, (40, 40, 50), input_box_rect)
        pygame.draw.rect(screen, (150, 150, 150), input_box_rect, 2)
        
        # Draw input text - handle long text by showing the end
        text_surface = input_font.render(input_text, True, (255, 255, 255))
        text_x = input_box_x + 10
        text_y = input_box_y + (input_box_height - text_surface.get_height()) // 2
        
        # If text is too long, show the end (right side) of the text
        if text_surface.get_width() > input_box_width - 20:
            # Calculate how much text we can show
            available_width = input_box_width - 20
            # Show the end of the text by adjusting x position
            text_x = input_box_x + input_box_width - text_surface.get_width() - 10
            # But don't let it go negative - clip the surface if needed
            if text_x < input_box_x + 10:
                # Create a subsurface showing the right portion
                clip_x = text_surface.get_width() - (input_box_width - 20)
                clip_rect = pygame.Rect(clip_x, 0, input_box_width - 20, text_surface.get_height())
                text_surface = text_surface.subsurface(clip_rect)
                text_x = input_box_x + 10
        
        screen.blit(text_surface, (text_x, text_y))
        
        # Draw cursor
        if cursor_visible:
            cursor_x = text_x + text_surface.get_width()
            if cursor_x > input_box_x + input_box_width - 10:
                cursor_x = input_box_x + input_box_width - 10
            cursor_rect = pygame.Rect(cursor_x, text_y, 2, text_surface.get_height())
            pygame.draw.rect(screen, (255, 255, 255), cursor_rect)
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "Enter: Confirm",
            "ESC: Cancel"
        ]
        y_offset = input_box_y + input_box_height + 20
        for instruction in instructions:
            inst_surface = instruction_font.render(instruction, True, (150, 150, 150))
            inst_rect = inst_surface.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(inst_surface, inst_rect)
            y_offset += 25
        
        pygame.display.flip()
    
    return result

