"""
Interactive script to select tiles from the tileset for each terrain type.
Navigate with arrow keys or mouse, press ENTER to assign the current tile.
Saves mappings to tileset_mappings.json
"""
import pygame
import sys
import os
import json
from terrain import TerrainType

# Tileset settings
MAPPINGS_FILE = "tileset_mappings.json"
TILE_SIZE = 16
SCALE = 6  # Scale up tiles for easier viewing

# Get tileset path from command line argument or use default
if len(sys.argv) > 1:
    TILESET_PATH = sys.argv[1]
else:
    TILESET_PATH = "16x16_old_map_Denzi090523-1.PNG"  # Default

def save_mappings_to_file(mappings):
    """Save terrain mappings to JSON file."""
    # Convert to serializable format
    json_data = {}
    for terrain_type, (x, y) in mappings.items():
        json_data[terrain_type.value] = [x, y]
    
    with open(MAPPINGS_FILE, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"\nSaved mappings to {MAPPINGS_FILE}")

def load_mappings_from_file():
    """Load terrain mappings from JSON file."""
    if not os.path.exists(MAPPINGS_FILE):
        return {}
    
    try:
        with open(MAPPINGS_FILE, 'r') as f:
            json_data = json.load(f)
        
        mappings = {}
        for terrain_name, coords in json_data.items():
            # Find matching TerrainType
            for terrain_type in TerrainType:
                if terrain_type.value == terrain_name:
                    mappings[terrain_type] = tuple(coords)
                    break
        return mappings
    except Exception as e:
        print(f"Error loading mappings: {e}")
        return {}

# Terrain types to map (in order)
TERRAIN_TYPES = [
    TerrainType.GRASSLAND,
    TerrainType.HILLS,
    TerrainType.FORESTED_HILL,
    TerrainType.MOUNTAIN,
    TerrainType.FOREST,
    TerrainType.RIVER,
    TerrainType.SHALLOW_WATER,
    TerrainType.DEEP_WATER,
]

# Initialize pygame
pygame.init()

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

print(f"Tileset: {tileset_width}x{tileset_height} pixels")
print(f"Grid: {tiles_per_row} tiles per row, {tiles_per_col} tiles per column")
print(f"\nInstructions:")
print(f"  Arrow keys or WASD: Navigate tiles")
print(f"  Mouse click: Jump to tile")
print(f"  ENTER: Assign current tile to terrain type")
print(f"  ESC: Cancel/Exit")
print(f"\nStarting tile selection...\n")

# Create display window
display_width = tiles_per_row * TILE_SIZE * SCALE + 400  # Extra space for info panel
display_height = max(tiles_per_col * TILE_SIZE * SCALE, 600)
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Tileset Tile Selector")

# Fonts
font_large = pygame.font.Font(None, 36)
font_medium = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# State
current_terrain_index = 0
current_tile_x = 0
current_tile_y = 0
# Load existing mappings if available
terrain_mappings = load_mappings_from_file()
# Start from first unassigned terrain type
for i, terrain_type in enumerate(TERRAIN_TYPES):
    if terrain_type not in terrain_mappings:
        current_terrain_index = i
        break
else:
    # All assigned, start from beginning
    current_terrain_index = 0

clock = pygame.time.Clock()
running = True

def get_current_terrain():
    """Get the terrain type we're currently selecting for."""
    if current_terrain_index < len(TERRAIN_TYPES):
        return TERRAIN_TYPES[current_terrain_index]
    return None

def draw_tileset_grid():
    """Draw the tileset grid with highlighted current tile."""
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
            border_color = (100, 100, 100)
            if x == current_tile_x and y == current_tile_y:
                border_color = (255, 255, 0)  # Yellow for current tile
            elif (x, y) in terrain_mappings.values():
                border_color = (0, 255, 0)  # Green for already assigned tiles
            
            border_rect = pygame.Rect(dest_x, dest_y, TILE_SIZE * SCALE, TILE_SIZE * SCALE)
            pygame.draw.rect(screen, border_color, border_rect, 2)
            
            # Draw coordinates on current tile
            if x == current_tile_x and y == current_tile_y:
                coord_text = font_small.render(f"({x},{y})", True, (255, 255, 255))
                # Draw with background for visibility
                text_bg = pygame.Surface((coord_text.get_width() + 4, coord_text.get_height() + 4))
                text_bg.fill((0, 0, 0))
                text_bg.set_alpha(180)
                screen.blit(text_bg, (dest_x + 2, dest_y + 2))
                screen.blit(coord_text, (dest_x + 4, dest_y + 4))

def draw_info_panel():
    """Draw the info panel on the right side."""
    panel_x = tiles_per_row * TILE_SIZE * SCALE + 10
    panel_y = 10
    
    # Title
    title_text = font_large.render("Tile Selector", True, (255, 255, 255))
    screen.blit(title_text, (panel_x, panel_y))
    panel_y += 50
    
    # Current terrain type
    current_terrain = get_current_terrain()
    if current_terrain:
        terrain_name = current_terrain.value.replace("_", " ").title()
        prompt_text = font_medium.render(f"Select tile for:", True, (200, 200, 200))
        screen.blit(prompt_text, (panel_x, panel_y))
        panel_y += 35
        
        terrain_text = font_large.render(terrain_name, True, (255, 255, 0))
        screen.blit(terrain_text, (panel_x, panel_y))
        panel_y += 50
        
        # Progress
        progress_text = font_small.render(
            f"({current_terrain_index + 1} of {len(TERRAIN_TYPES)})", 
            True, (150, 150, 150)
        )
        screen.blit(progress_text, (panel_x, panel_y))
        panel_y += 40
    else:
        # All done!
        done_text = font_large.render("All Done!", True, (0, 255, 0))
        screen.blit(done_text, (panel_x, panel_y))
        panel_y += 50
    
    # Current tile info
    panel_y += 20
    current_text = font_medium.render("Current Tile:", True, (200, 200, 200))
    screen.blit(current_text, (panel_x, panel_y))
    panel_y += 30
    
    coord_text = font_large.render(f"({current_tile_x}, {current_tile_y})", True, (255, 255, 255))
    screen.blit(coord_text, (panel_x, panel_y))
    panel_y += 50
    
    # Instructions
    panel_y += 20
    instructions = [
        "Arrow Keys / WASD:",
        "  Navigate tiles",
        "",
        "Mouse Click:",
        "  Jump to tile",
        "",
        "ENTER:",
        "  Assign tile",
        "",
        "ESC:",
        "  Exit"
    ]
    
    for line in instructions:
        if line:
            inst_text = font_small.render(line, True, (150, 150, 150))
            screen.blit(inst_text, (panel_x, panel_y))
        panel_y += 20
    
    # Show assigned mappings
    panel_y += 20
    if terrain_mappings:
        assigned_text = font_medium.render("Assigned Tiles:", True, (200, 200, 200))
        screen.blit(assigned_text, (panel_x, panel_y))
        panel_y += 30
        
        for terrain_type, (x, y) in sorted(terrain_mappings.items(), key=lambda t: TERRAIN_TYPES.index(t[0])):
            terrain_name = terrain_type.value.replace("_", " ").title()
            mapping_text = font_small.render(
                f"{terrain_name}: ({x}, {y})", 
                True, (0, 255, 0)
            )
            screen.blit(mapping_text, (panel_x, panel_y))
            panel_y += 22

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Assign current tile to current terrain type
                current_terrain = get_current_terrain()
                if current_terrain:
                    terrain_mappings[current_terrain] = (current_tile_x, current_tile_y)
                    print(f"Assigned ({current_tile_x}, {current_tile_y}) to {current_terrain.value}")
                    
                    # Move to next terrain type
                    current_terrain_index += 1
                    # Save after each assignment (so progress is preserved)
                    save_mappings_to_file(terrain_mappings)
                    
                    if current_terrain_index >= len(TERRAIN_TYPES):
                        print("\nAll terrain types assigned!")
                        print(f"Mappings saved to tileset_mappings.json")
                        running = False
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                current_tile_x = max(0, current_tile_x - 1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                current_tile_x = min(tiles_per_row - 1, current_tile_x + 1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                current_tile_y = max(0, current_tile_y - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                current_tile_y = min(tiles_per_col - 1, current_tile_y + 1)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = event.pos
                # Check if click is in tile area
                if mouse_x < tiles_per_row * TILE_SIZE * SCALE:
                    tile_x = mouse_x // (TILE_SIZE * SCALE)
                    tile_y = mouse_y // (TILE_SIZE * SCALE)
                    if 0 <= tile_x < tiles_per_row and 0 <= tile_y < tiles_per_col:
                        current_tile_x = tile_x
                        current_tile_y = tile_y
    
    # Clear screen
    screen.fill((30, 30, 40))
    
    # Draw tileset grid
    draw_tileset_grid()
    
    # Draw info panel
    draw_info_panel()
    
    pygame.display.flip()
    clock.tick(60)

# Save mappings before exiting (in case user exits early)
if terrain_mappings:
    save_mappings_to_file(terrain_mappings)

pygame.quit()

# Print final results
if terrain_mappings:
    print("\n" + "="*60)
    print("Mappings saved to tileset_mappings.json")
    print("The game will automatically load these mappings.")
    print("="*60)
    print("\nCurrent mappings:")
    for terrain_type in TERRAIN_TYPES:
        if terrain_type in terrain_mappings:
            x, y = terrain_mappings[terrain_type]
            terrain_name = terrain_type.value
            print(f"  {terrain_name}: ({x}, {y})")
        else:
            terrain_name = terrain_type.value
            print(f"  {terrain_name}: NOT ASSIGNED")
    print("="*60)

