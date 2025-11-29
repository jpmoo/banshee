"""
Text utility functions for word wrapping.
"""
import pygame
from typing import List


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """
    Wrap text to fit within a maximum width.
    
    Args:
        text: The text to wrap
        font: The pygame font to use for measuring text
        max_width: Maximum width in pixels
        
    Returns:
        List of text lines
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        # Measure word width
        word_surface = font.render(word, True, (255, 255, 255))
        word_width = word_surface.get_width()
        
        # If adding this word would exceed max_width, start a new line
        if current_line and current_width + word_width + font.size(' ')[0] > max_width:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
        else:
            # Add space width if not first word
            if current_line:
                current_width += font.size(' ')[0]
            current_line.append(word)
            current_width += word_width
    
    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else ['']


def render_wrapped_text(text: str, font: pygame.font.Font, color: tuple, 
                       max_width: int) -> List[pygame.Surface]:
    """
    Render text with word wrapping.
    
    Args:
        text: The text to render
        font: The pygame font to use
        color: Text color (RGB tuple)
        max_width: Maximum width in pixels
        
    Returns:
        List of rendered text surfaces
    """
    lines = wrap_text(text, font, max_width)
    return [font.render(line, True, color) for line in lines]

Text utility functions for word wrapping.
"""
import pygame
from typing import List


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """
    Wrap text to fit within a maximum width.
    
    Args:
        text: The text to wrap
        font: The pygame font to use for measuring text
        max_width: Maximum width in pixels
        
    Returns:
        List of text lines
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        # Measure word width
        word_surface = font.render(word, True, (255, 255, 255))
        word_width = word_surface.get_width()
        
        # If adding this word would exceed max_width, start a new line
        if current_line and current_width + word_width + font.size(' ')[0] > max_width:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
        else:
            # Add space width if not first word
            if current_line:
                current_width += font.size(' ')[0]
            current_line.append(word)
            current_width += word_width
    
    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else ['']


def render_wrapped_text(text: str, font: pygame.font.Font, color: tuple, 
                       max_width: int) -> List[pygame.Surface]:
    """
    Render text with word wrapping.
    
    Args:
        text: The text to render
        font: The pygame font to use
        color: Text color (RGB tuple)
        max_width: Maximum width in pixels
        
    Returns:
        List of rendered text surfaces
    """
    lines = wrap_text(text, font, max_width)
    return [font.render(line, True, color) for line in lines]

