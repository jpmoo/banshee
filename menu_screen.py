"""
Main menu screen for the game with Celtic styling.
"""
import pygame
import math
from typing import Optional


class MenuScreen:
    """Displays the main game menu."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the main menu screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.selected_option = 0  # 0 = Start New Game, 1 = Continue Saved Game
        
        # Load background image if it exists
        self.background_image = None
        try:
            bg_image = pygame.image.load("image.png")
            # Stretch to fill the entire screen
            self.background_image = pygame.transform.scale(bg_image, (self.width, self.height))
        except (pygame.error, FileNotFoundError):
            # If image doesn't exist, continue without it
            self.background_image = None
        
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
        
    def draw_celtic_knot(self, surface, center_x, center_y, size, color, thickness=2, complexity=1):
        """Draw a Celtic knot pattern with varying complexity."""
        points = []
        steps = 24 * (complexity + 1)
        for i in range(steps):
            angle = math.radians(i * 360 / steps)
            # Create interwoven pattern
            if complexity == 0:
                # Simple figure-8
                if i < steps // 2:
                    radius = size * (0.5 + 0.3 * math.sin(angle * 2))
                else:
                    radius = size * (0.5 - 0.3 * math.sin(angle * 2))
            else:
                # More complex interweaving
                radius = size * (0.5 + 0.25 * math.sin(angle * 3) + 0.15 * math.sin(angle * 5))
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((int(x), int(y)))
        
        if len(points) > 2:
            pygame.draw.lines(surface, color, True, points, thickness)
    
    def draw_celtic_spiral(self, surface, center_x, center_y, size, color, thickness=2, turns=3):
        """Draw a Celtic spiral pattern."""
        points = []
        steps = 100
        for i in range(steps):
            t = i / steps
            angle = t * turns * 2 * math.pi
            radius = size * t * 0.8
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((int(x), int(y)))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, thickness)
    
    def draw_celtic_dragon(self, surface, center_x, center_y, size, color, thickness=2):
        """Draw a stylized Celtic dragon/serpent."""
        # Body (sinuous curve)
        body_points = []
        for i in range(50):
            t = i / 50.0
            x = center_x + size * (t - 0.5) * 1.5
            y = center_y + size * 0.3 * math.sin(t * math.pi * 3)
            body_points.append((int(x), int(y)))
        
        if len(body_points) > 1:
            pygame.draw.lines(surface, color, False, body_points, thickness)
        
        # Head (at one end)
        head_x, head_y = body_points[-1]
        # Draw head as a small circle with decorative elements
        pygame.draw.circle(surface, color, (head_x, head_y), size // 4, thickness)
        # Eye
        pygame.draw.circle(surface, color, (head_x + size // 8, head_y - size // 8), 2, 0)
        
        # Tail (at other end)
        tail_x, tail_y = body_points[0]
        # Draw tail as spiral
        self.draw_celtic_spiral(surface, tail_x, tail_y, size // 3, color, thickness, 2)
    
    def draw_celtic_bird(self, surface, center_x, center_y, size, color, thickness=2):
        """Draw a stylized Celtic bird."""
        # Body
        pygame.draw.ellipse(surface, color, 
                          (center_x - size // 4, center_y - size // 6, size // 2, size // 3), thickness)
        
        # Wings (stylized curves)
        wing_points = []
        for i in range(20):
            t = i / 20.0
            x = center_x - size // 3 + size * 0.4 * t
            y = center_y - size // 4 + size * 0.3 * math.sin(t * math.pi)
            wing_points.append((int(x), int(y)))
        if len(wing_points) > 1:
            pygame.draw.lines(surface, color, False, wing_points, thickness)
        
        # Mirror wing
        wing_points2 = []
        for i in range(20):
            t = i / 20.0
            x = center_x - size // 3 + size * 0.4 * t
            y = center_y + size // 4 - size * 0.3 * math.sin(t * math.pi)
            wing_points2.append((int(x), int(y)))
        if len(wing_points2) > 1:
            pygame.draw.lines(surface, color, False, wing_points2, thickness)
        
        # Head and beak
        head_x = center_x + size // 3
        head_y = center_y
        pygame.draw.circle(surface, color, (head_x, head_y), size // 6, thickness)
        # Beak
        beak_points = [(head_x + size // 6, head_y), (head_x + size // 3, head_y - size // 12), 
                      (head_x + size // 3, head_y + size // 12)]
        pygame.draw.lines(surface, color, True, beak_points, thickness)
    
    def draw_interlacing_pattern(self, surface, x, y, width, height, color, thickness=1):
        """Draw an interlacing Celtic pattern."""
        # Create a grid of interwoven lines
        grid_size = 8
        cell_w = width / grid_size
        cell_h = height / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                cx = x + (i + 0.5) * cell_w
                cy = y + (j + 0.5) * cell_h
                # Draw small knot at grid intersection
                if (i + j) % 2 == 0:
                    self.draw_celtic_knot(surface, cx, cy, min(cell_w, cell_h) * 0.3, color, thickness, 0)
    
    def draw_celtic_border(self, surface, x, y, width, height, color, thickness=2):
        """Draw an elaborate Celtic-style border with knotwork."""
        # Draw corner decorations with spirals
        corner_size = 50
        # Top-left corner
        pygame.draw.arc(surface, color, (x, y, corner_size, corner_size), math.pi, math.pi * 1.5, thickness)
        self.draw_celtic_spiral(surface, x + corner_size // 2, y + corner_size // 2, corner_size // 2, color, thickness, 2)
        # Top-right corner
        pygame.draw.arc(surface, color, (x + width - corner_size, y, corner_size, corner_size), math.pi * 1.5, 0, thickness)
        self.draw_celtic_spiral(surface, x + width - corner_size // 2, y + corner_size // 2, corner_size // 2, color, thickness, 2)
        # Bottom-left corner
        pygame.draw.arc(surface, color, (x, y + height - corner_size, corner_size, corner_size), math.pi * 0.5, math.pi, thickness)
        self.draw_celtic_spiral(surface, x + corner_size // 2, y + height - corner_size // 2, corner_size // 2, color, thickness, 2)
        # Bottom-right corner
        pygame.draw.arc(surface, color, (x + width - corner_size, y + height - corner_size, corner_size, corner_size), 0, math.pi * 0.5, thickness)
        self.draw_celtic_spiral(surface, x + width - corner_size // 2, y + height - corner_size // 2, corner_size // 2, color, thickness, 2)
        
        # Draw side decorations with knots and creatures
        # Top border
        for i in range(5):
            px = x + width // 6 + i * (width // 6)
            if i % 2 == 0:
                self.draw_celtic_knot(surface, px, y + 20, 30, color, 1, 1)
            else:
                self.draw_celtic_spiral(surface, px, y + 20, 25, color, 1, 2)
        # Bottom border
        for i in range(5):
            px = x + width // 6 + i * (width // 6)
            if i % 2 == 0:
                self.draw_celtic_knot(surface, px, y + height - 20, 30, color, 1, 1)
            else:
                self.draw_celtic_spiral(surface, px, y + height - 20, 25, color, 1, 2)
        # Left border
        for i in range(4):
            py = y + height // 5 + i * (height // 5)
            if i % 2 == 0:
                self.draw_celtic_knot(surface, x + 20, py, 30, color, 1, 1)
            else:
                self.draw_celtic_spiral(surface, x + 20, py, 25, color, 1, 2)
        # Right border
        for i in range(4):
            py = y + height // 5 + i * (height // 5)
            if i % 2 == 0:
                self.draw_celtic_knot(surface, x + width - 20, py, 30, color, 1, 1)
            else:
                self.draw_celtic_spiral(surface, x + width - 20, py, 25, color, 1, 2)
    
    def render(self):
        """Render the main menu screen with background image."""
        # Draw background image if available, otherwise use solid color
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            # Clear screen with dark background
            self.screen.fill((10, 10, 20))
        
        # Title image or text
        if self.title_image:
            title_rect = self.title_image.get_rect(center=(self.width // 2, self.height // 3))
            self.screen.blit(self.title_image, title_rect)
        else:
            # Fallback to text if image not found
            title_font = pygame.font.Font(None, 96)
            title_text = title_font.render("BANSHEE RPG", True, (220, 60, 60))
        
            # Render title with shadow for readability
            shadow_offset = 3
            title_text_shadow = title_font.render("BANSHEE RPG", True, (0, 0, 0))
            title_rect = title_text.get_rect(center=(self.width // 2 + shadow_offset, self.height // 3 + shadow_offset))
            self.screen.blit(title_text_shadow, title_rect)
        
            title_rect = title_text.get_rect(center=(self.width // 2, self.height // 3))
            self.screen.blit(title_text, title_rect)
        
        # Menu options
        option_font = pygame.font.Font(None, 48)
        
        y_start = self.height // 2
        
        # Option 1: Start New Game
        option1_text = "Start a New Game"
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
        
        # Option 2: Continue Saved Game
        option2_text = "Continue a Saved Game"
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
        
        # Show message for Continue if selected
        if self.selected_option == 1:
            message_font = pygame.font.Font(None, 28)
            message_text = message_font.render("(Feature coming soon)", True, (150, 150, 150))
            message_rect = message_text.get_rect(center=(self.width // 2, y_start + 160))
            self.screen.blit(message_text, message_rect)
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "UP/DOWN: Navigate options",
            "ENTER: Select",
            "ESC: Quit"
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
            'new_game' if start new game selected,
            'continue' if continue saved game selected,
            'quit' if ESC pressed,
            None if no action taken
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'quit'
            elif event.key == pygame.K_UP:
                # Switch to previous option
                self.selected_option = (self.selected_option - 1) % 2
            elif event.key == pygame.K_DOWN:
                # Switch to next option
                self.selected_option = (self.selected_option + 1) % 2
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.selected_option == 0:
                    return 'new_game'
                elif self.selected_option == 1:
                    return 'continue'  # Placeholder - does nothing yet
        
        return None

