"""
Analyze tileset to suggest terrain mappings based on color patterns.
"""
import pygame
import os
from collections import defaultdict

TILESET_PATH = "16x16_old_map_Denzi090523-1.PNG"
TILE_SIZE = 16

def get_tile_average_color(tileset, tile_x, tile_y):
    """Get average RGB color of a tile."""
    source_x = tile_x * TILE_SIZE
    source_y = tile_y * TILE_SIZE
    
    total_r, total_g, total_b = 0, 0, 0
    pixel_count = 0
    
    for y in range(TILE_SIZE):
        for x in range(TILE_SIZE):
            pixel_x = source_x + x
            pixel_y = source_y + y
            if pixel_x < tileset.get_width() and pixel_y < tileset.get_height():
                color = tileset.get_at((pixel_x, pixel_y))
                total_r += color.r
                total_g += color.g
                total_b += color.b
                pixel_count += 1
    
    if pixel_count == 0:
        return (0, 0, 0)
    
    return (total_r // pixel_count, total_g // pixel_count, total_b // pixel_count)

def categorize_tile_by_color(avg_r, avg_g, avg_b):
    """Categorize tile based on color characteristics."""
    # Water detection (blue tones)
    if avg_b > avg_r + 20 and avg_b > avg_g + 20:
        if avg_b > 150:
            return "deep_water"
        else:
            return "shallow_water"
    
    # Green tones (grass/forest)
    if avg_g > avg_r + 30 and avg_g > avg_b + 30:
        if avg_g > 120:
            return "grassland"
        else:
            return "forest"
    
    # Brown/gray tones (hills/mountains)
    if avg_r + avg_g + avg_b < 200:  # Dark
        if abs(avg_r - avg_g) < 30 and abs(avg_g - avg_b) < 30:  # Gray
            return "mountain"
        else:  # Brown
            return "hills"
    
    # Light brown/yellow (hills/grassland)
    if avg_r > avg_b + 20:
        return "hills"
    
    return "unknown"

def analyze_tileset():
    """Analyze the tileset and suggest terrain mappings."""
    if not os.path.exists(TILESET_PATH):
        print(f"Error: Tileset file not found: {TILESET_PATH}")
        return
    
    pygame.init()
    tileset = pygame.image.load(TILESET_PATH).convert_alpha()
    tileset_width = tileset.get_width()
    tileset_height = tileset.get_height()
    
    tiles_per_row = tileset_width // TILE_SIZE
    tiles_per_col = tileset_height // TILE_SIZE
    
    print(f"Analyzing tileset: {tileset_width}x{tileset_height}")
    print(f"Grid: {tiles_per_row} x {tiles_per_col} tiles\n")
    
    # Analyze each tile
    categories = defaultdict(list)
    
    for y in range(tiles_per_col):
        for x in range(tiles_per_row):
            avg_r, avg_g, avg_b = get_tile_average_color(tileset, x, y)
            category = categorize_tile_by_color(avg_r, avg_g, avg_b)
            categories[category].append((x, y, avg_r, avg_g, avg_b))
    
    # Print suggestions
    print("Suggested terrain mappings based on color analysis:\n")
    
    terrain_mappings = {
        "grassland": categories.get("grassland", []),
        "forest": categories.get("forest", []),
        "hills": categories.get("hills", []),
        "mountain": categories.get("mountain", []),
        "shallow_water": categories.get("shallow_water", []),
        "deep_water": categories.get("deep_water", []),
    }
    
    for terrain_type, tiles in terrain_mappings.items():
        if tiles:
            # Pick the first tile as suggestion (you may want to manually verify)
            tile_x, tile_y, r, g, b = tiles[0]
            print(f"{terrain_type.upper()}: ({tile_x}, {tile_y}) - RGB: ({r}, {g}, {b})")
            if len(tiles) > 1:
                print(f"  (Found {len(tiles)} potential tiles for this terrain)")
        else:
            print(f"{terrain_type.upper()}: No tiles found - may need manual selection")
    
    print("\n\nAll tiles by category:")
    for category, tile_list in sorted(categories.items()):
        print(f"\n{category.upper()} ({len(tile_list)} tiles):")
        for tile_x, tile_y, r, g, b in tile_list[:10]:  # Show first 10
            print(f"  ({tile_x}, {tile_y}) - RGB: ({r}, {g}, {b})")
        if len(tile_list) > 10:
            print(f"  ... and {len(tile_list) - 10} more")

if __name__ == "__main__":
    analyze_tileset()

