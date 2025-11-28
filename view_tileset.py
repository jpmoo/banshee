"""
Utility script to view the tileset in a grid layout.
This helps identify which tiles correspond to which terrain types.
"""
import pygame
import sys
import os

# Initialize pygame
pygame.init()

# Tileset settings
TILESET_PATH = "16x16_old_map_Denzi090523-1.PNG"
TILE_SIZE = 16
SCALE = 4  # Scale up tiles for easier viewing

# Load tileset
if not os.path.exists(TILESET_PATH):
    print(f"Error: Tileset file not found: {TILESET_PATH}")
    sys.exit(1)

tileset = pygame.image.load(TILESET_PATH).convert_alpha()
tileset_width = tileset.get_width()
tileset_height = tileset.get_height()

# Calculate grid dimensions
tiles_per_row = tileset_width // TILE_SIZE
tiles_per_col = tileset_height // TILE_SIZE
total_tiles = tiles_per_row * tiles_per_col

print(f"Tileset: {tileset_width}x{tileset_height} pixels")
print(f"Tiles: {tiles_per_row} per row, {tiles_per_col} per column")
print(f"Total tiles: {total_tiles}")

# Create display window
display_width = tiles_per_row * TILE_SIZE * SCALE + 200  # Extra space for labels
display_height = tiles_per_col * TILE_SIZE * SCALE + 100
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Tileset Viewer - Click tiles to see coordinates")

# Font for labels
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 16)

clock = pygame.time.Clock()
running = True
selected_tile = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = event.pos
                # Check if click is in tile area
                if mouse_x < tiles_per_row * TILE_SIZE * SCALE:
                    tile_x = mouse_x // (TILE_SIZE * SCALE)
                    tile_y = mouse_y // (TILE_SIZE * SCALE)
                    if 0 <= tile_x < tiles_per_row and 0 <= tile_y < tiles_per_col:
                        selected_tile = (tile_x, tile_y)
                        print(f"Selected tile: ({tile_x}, {tile_y}) - Use this in terrain_tile_map")
    
    # Clear screen
    screen.fill((40, 40, 50))
    
    # Draw tileset grid
    for y in range(tiles_per_col):
        for x in range(tiles_per_row):
            # Calculate source rect in tileset
            source_x = x * TILE_SIZE
            source_y = y * TILE_SIZE
            source_rect = pygame.Rect(source_x, source_y, TILE_SIZE, TILE_SIZE)
            
            # Calculate destination position (scaled)
            dest_x = x * TILE_SIZE * SCALE
            dest_y = y * TILE_SIZE * SCALE
            
            # Extract and scale tile
            tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            tile_surface.blit(tileset, (0, 0), source_rect)
            scaled_tile = pygame.transform.scale(tile_surface, (TILE_SIZE * SCALE, TILE_SIZE * SCALE))
            
            # Draw tile
            screen.blit(scaled_tile, (dest_x, dest_y))
            
            # Draw border
            border_rect = pygame.Rect(dest_x, dest_y, TILE_SIZE * SCALE, TILE_SIZE * SCALE)
            pygame.draw.rect(screen, (100, 100, 100), border_rect, 1)
            
            # Draw coordinates
            coord_text = small_font.render(f"({x},{y})", True, (255, 255, 255))
            screen.blit(coord_text, (dest_x + 2, dest_y + 2))
            
            # Highlight selected tile
            if selected_tile == (x, y):
                highlight_rect = pygame.Rect(dest_x, dest_y, TILE_SIZE * SCALE, TILE_SIZE * SCALE)
                pygame.draw.rect(screen, (255, 255, 0), highlight_rect, 3)
    
    # Draw info panel
    info_x = tiles_per_row * TILE_SIZE * SCALE + 10
    info_y = 10
    
    title_text = font.render("Tileset Viewer", True, (255, 255, 255))
    screen.blit(title_text, (info_x, info_y))
    info_y += 30
    
    info_text = [
        f"Tiles: {tiles_per_row}x{tiles_per_col}",
        f"Total: {total_tiles} tiles",
        "",
        "Click a tile to see",
        "its coordinates",
        "",
        "Press ESC to exit"
    ]
    
    if selected_tile:
        info_text.append("")
        info_text.append(f"Selected: ({selected_tile[0]}, {selected_tile[1]})")
        info_text.append("")
        info_text.append("Use in code:")
        info_text.append(f"({selected_tile[0]}, {selected_tile[1]})")
    
    for i, line in enumerate(info_text):
        text_surface = small_font.render(line, True, (200, 200, 200))
        screen.blit(text_surface, (info_x, info_y + i * 20))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

