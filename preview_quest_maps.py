"""
Preview script for viewing quest location maps and descriptions.
Shows maps with color-coded terrain and allows browsing through all locations.
"""
import json
import os
import pygame
import sys
from typing import List, Tuple
from data_quest_locations import quest_location_descriptions
from terrain import Terrain, TerrainType

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
TILE_SIZE = 8  # Size of each tile in pixels
MAP_PREVIEW_SIZE = 200  # Size of map preview area (square)

# Colors
BG_COLOR = (30, 30, 40)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (100, 150, 255)
BORDER_COLOR = (150, 150, 150)

def load_maps_data() -> dict:
    """Load maps data from JSON file."""
    maps_file = "quest_location_maps_data.json"
    if not os.path.exists(maps_file):
        print(f"Error: Quest location maps file not found: {maps_file}")
        print("Please run generate_quest_maps_v2.py first to generate the maps.")
        sys.exit(1)
    
    try:
        with open(maps_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading quest location maps: {e}")
        sys.exit(1)


def render_map_preview(surface: pygame.Surface, map_data: List[List[str]], 
                       x: int, y: int, size: int):
    """
    Render a map preview on the surface.
    
    Args:
        surface: Pygame surface to draw on
        map_data: A list of lists of terrain type strings
        x, y: Top-left position
        size: Size of preview area (square)
    """
    if not map_data or len(map_data) == 0:
        return
    
    map_height = len(map_data)
    map_width = len(map_data[0]) if map_data else 0
    
    if map_width == 0:
        return
    
    # Calculate tile size to fit in preview area
    tile_size = min(size // map_width, size // map_height, TILE_SIZE)
    
    # Center the map in the preview area
    map_pixel_width = map_width * tile_size
    map_pixel_height = map_height * tile_size
    offset_x = x + (size - map_pixel_width) // 2
    offset_y = y + (size - map_pixel_height) // 2
    
    # Draw map
    for row_idx, row in enumerate(map_data):
        for col_idx, terrain_str in enumerate(row):
            try:
                terrain_type = TerrainType(terrain_str)
                terrain = Terrain(terrain_type)
                color = terrain.get_color()
            except ValueError:
                color = (100, 100, 100)  # Gray for unknown
            
            rect = pygame.Rect(
                offset_x + col_idx * tile_size,
                offset_y + row_idx * tile_size,
                tile_size,
                tile_size
            )
            pygame.draw.rect(surface, color, rect)
    
    # Draw border
    border_rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surface, BORDER_COLOR, border_rect, 2)


def main():
    """Main preview loop."""
    # Ask user which terrain type to view
    print("\nQuest Location Maps Preview")
    print("=" * 40)
    print("Available terrain types:")
    terrain_types = list(quest_location_descriptions.keys())
    for i, terrain_type in enumerate(terrain_types, 1):
        count = len(quest_location_descriptions[terrain_type])
        print(f"  {i}. {terrain_type} ({count} locations)")
    print(f"  {len(terrain_types) + 1}. All terrain types")
    print()
    
    while True:
        try:
            choice = input(f"Select terrain type (1-{len(terrain_types) + 1}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(terrain_types):
                selected_terrain = terrain_types[choice_num - 1]
                print(f"\nShowing locations for: {selected_terrain}")
                break
            elif choice_num == len(terrain_types) + 1:
                selected_terrain = None  # Show all
                print(f"\nShowing all terrain types")
                break
            else:
                print(f"Please enter a number between 1 and {len(terrain_types) + 1}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Quest Location Maps Preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    title_font = pygame.font.Font(None, 32)
    
    # Load maps data
    maps_data = load_maps_data()
    
    # Flatten locations into a list for navigation (filtered by terrain type if selected)
    all_locations = []
    if selected_terrain:
        # Only show selected terrain type
        for description in quest_location_descriptions[selected_terrain]:
            all_locations.append((selected_terrain, description))
    else:
        # Show all terrain types
        for terrain_type, descriptions in quest_location_descriptions.items():
            for description in descriptions:
                all_locations.append((terrain_type, description))
    
    if not all_locations:
        print("No locations found!")
        return
    
    current_index = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                    current_index = (current_index - 1) % len(all_locations)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                    current_index = (current_index + 1) % len(all_locations)
                elif event.key == pygame.K_HOME:
                    current_index = 0
                elif event.key == pygame.K_END:
                    current_index = len(all_locations) - 1
        
        # Get current location
        terrain_type, description = all_locations[current_index]
        map_array = maps_data.get(terrain_type, {}).get(description, [])
        
        # Clear screen
        screen.fill(BG_COLOR)
        
        # Title
        title_text = title_font.render("Quest Location Maps Preview", True, TEXT_COLOR)
        screen.blit(title_text, (20, 20))
        
        # Navigation info
        nav_text = small_font.render(
            f"Location {current_index + 1} of {len(all_locations)} | "
            f"Use ←/→ or ↑/↓ to navigate | ESC to quit",
            True, (150, 150, 150)
        )
        screen.blit(nav_text, (20, 60))
        
        # Terrain type
        terrain_text = font.render(f"Terrain Type: {terrain_type}", True, HIGHLIGHT_COLOR)
        screen.blit(terrain_text, (20, 100))
        
        # Description
        desc_y = 140
        desc_text = font.render("Description:", True, TEXT_COLOR)
        screen.blit(desc_text, (20, desc_y))
        
        # Word wrap description
        words = description.split()
        lines = []
        current_line = ""
        max_width = SCREEN_WIDTH - 40
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = font.render(test_line, True, TEXT_COLOR)
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, TEXT_COLOR)
            screen.blit(line_surface, (20, desc_y + 35 + i * 30))
        
        # Map preview
        map_x = SCREEN_WIDTH - MAP_PREVIEW_SIZE - 40
        map_y = 100
        
        # Map preview label
        map_label = font.render("Map Preview:", True, TEXT_COLOR)
        screen.blit(map_label, (map_x, map_y - 30))
        
        if map_array:
            render_map_preview(screen, map_array, map_x, map_y, MAP_PREVIEW_SIZE)
        else:
            # No map data
            no_map_text = font.render("No map data", True, (150, 150, 150))
            no_map_rect = no_map_text.get_rect(center=(map_x + MAP_PREVIEW_SIZE // 2, 
                                                       map_y + MAP_PREVIEW_SIZE // 2))
            screen.blit(no_map_text, no_map_rect)
        
        # Legend
        legend_y = map_y + MAP_PREVIEW_SIZE + 30
        legend_text = font.render("Terrain Legend:", True, TEXT_COLOR)
        screen.blit(legend_text, (map_x, legend_y))
        
        legend_items = [
            (TerrainType.GRASSLAND, "Grassland"),
            (TerrainType.HILLS, "Hills"),
            (TerrainType.FORESTED_HILL, "Forested Hill"),
            (TerrainType.FOREST, "Forest"),
            (TerrainType.MOUNTAIN, "Mountain (Structures)"),
            (TerrainType.SHALLOW_WATER, "Shallow Water"),
            (TerrainType.DEEP_WATER, "Deep Water"),
        ]
        
        legend_x = map_x
        legend_y += 35
        for terrain_type_enum, label in legend_items:
            color = Terrain(terrain_type_enum).get_color()
            color_rect = pygame.Rect(legend_x, legend_y, 20, 20)
            pygame.draw.rect(screen, color, color_rect)
            pygame.draw.rect(screen, BORDER_COLOR, color_rect, 1)
            
            label_surface = small_font.render(label, True, TEXT_COLOR)
            screen.blit(label_surface, (legend_x + 25, legend_y + 2))
            legend_y += 25
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()

