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
TILESETS_DIR = "tilesets"
MAPPINGS_FILE = "tileset_mappings.json"  # Will be saved in tilesets/{tileset_name}/
TILE_SIZE = 16
SCALE = 6  # Scale up tiles for easier viewing

# Get tileset path from command line argument or use default
if len(sys.argv) > 1:
    TILESET_PATH = sys.argv[1]
else:
    # Default: look in tilesets folder (directly, not subfolders)
    default_tileset_path = os.path.join(TILESETS_DIR, "16x16_old_map_Denzi090523-1.PNG")
    if os.path.exists(default_tileset_path):
        TILESET_PATH = default_tileset_path
    else:
        # Fallback to old location
        TILESET_PATH = "16x16_old_map_Denzi090523-1.PNG"

def save_mappings_to_file(mappings, tileset_name=None):
    # Store transparency color as function attribute
    if not hasattr(save_mappings_to_file, 'transparency_color'):
        save_mappings_to_file.transparency_color = None
    """Save terrain mappings to JSON file in tilesets folder (same name as PNG)."""
    # Create tilesets directory if it doesn't exist
    if not os.path.exists(TILESETS_DIR):
        os.makedirs(TILESETS_DIR)
    
    # If tileset is not in tilesets folder, copy it there
    tileset_image_name = os.path.basename(TILESET_PATH)
    tileset_image_path = os.path.join(TILESETS_DIR, tileset_image_name)
    
    if not os.path.exists(tileset_image_path):
        import shutil
        try:
            shutil.copy2(TILESET_PATH, tileset_image_path)
            print(f"Copied tileset image to {tileset_image_path}")
        except Exception as e:
            print(f"Warning: Could not copy tileset image: {e}")
    
    # JSON file should have the same name as the PNG (but with .json extension)
    # Save directly in tilesets folder (not subfolder)
    png_basename = os.path.splitext(tileset_image_name)[0]
    json_filename = png_basename + ".json"
    mappings_file = os.path.join(TILESETS_DIR, json_filename)
    
    # Save mappings file
    # Format: terrain_name -> [[x1, y1]] for single layer, or [[x1, y1], [x2, y2]] for two layers
    json_data = {}
    for terrain_type, layers in mappings.items():
        # Convert to list format for JSON
        if isinstance(layers, list):
            json_data[terrain_type.value] = layers
        else:
            # Old format: single (x, y) tuple - convert to new format
            json_data[terrain_type.value] = [list(layers)]
    
    # Add transparency color if it exists
    if save_mappings_to_file.transparency_color is not None:
        json_data['_transparency_color'] = save_mappings_to_file.transparency_color
    
    with open(mappings_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"\nSaved mappings to {mappings_file}")

def load_mappings_from_file(tileset_name=None):
    """Load terrain mappings from JSON file in tilesets folder (same name as PNG)."""
    # JSON file should have the same name as the PNG, in tilesets folder
    png_basename = os.path.splitext(os.path.basename(TILESET_PATH))[0]
    json_filename = png_basename + ".json"
    mappings_file = os.path.join(TILESETS_DIR, json_filename)
    
    # Fallback to old location/format for backward compatibility
    if not os.path.exists(mappings_file):
        mappings_file = MAPPINGS_FILE
    
    if not os.path.exists(mappings_file):
        return {}
    
    try:
        with open(mappings_file, 'r') as f:
            json_data = json.load(f)
        
        mappings = {}
        for terrain_name, layers in json_data.items():
            # Find matching TerrainType
            for terrain_type in TerrainType:
                if terrain_type.value == terrain_name:
                    # Handle both old format (single [x, y]) and new format ([[x, y]] or [[x1, y1], [x2, y2]])
                    if isinstance(layers, list) and len(layers) > 0:
                        if isinstance(layers[0], list):
                            # New format: list of [x, y] lists
                            mappings[terrain_type] = [tuple(layer) for layer in layers]
                        else:
                            # Old format: single [x, y] - convert to new format
                            mappings[terrain_type] = [tuple(layers)]
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

# Initialize pygame (must be done before loading images)
pygame.init()

# Load tileset
if not os.path.exists(TILESET_PATH):
    print(f"Error: Tileset file not found: {TILESET_PATH}")
    sys.exit(1)

# Create a minimal display surface (required for image loading)
# We'll create the actual window later
pygame.display.set_mode((1, 1))

tileset = pygame.image.load(TILESET_PATH).convert_alpha()
print(f"Tileset loaded: {tileset.get_width()}x{tileset.get_height()}, format: {tileset.get_flags()}")

# Check if tileset has alpha channel with transparent pixels
has_alpha_channel = tileset.get_flags() & pygame.SRCALPHA
has_transparency = False
if has_alpha_channel:
    # Sample some pixels to see if any are actually transparent
    sample_count = min(100, tileset.get_width() * tileset.get_height())
    step = max(1, (tileset.get_width() * tileset.get_height()) // sample_count)
    transparent_pixels = 0
    for i in range(0, tileset.get_width() * tileset.get_height(), step):
        x = i % tileset.get_width()
        y = i // tileset.get_width()
        if y < tileset.get_height():
            pixel = tileset.get_at((x, y))
            if len(pixel) >= 4 and pixel[3] < 255:  # Alpha < 255 means transparent
                transparent_pixels += 1
    has_transparency = transparent_pixels > 0
    if has_transparency:
        print(f"Tileset has alpha channel with transparency ({transparent_pixels} transparent pixels found in sample)")
    else:
        print(f"Tileset has alpha channel but no transparent pixels detected")
else:
    print(f"Tileset does not have alpha channel - will need chroma key color for transparency")
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

# Create display window (replace the minimal one we created earlier)
# Get screen size and scale to fit
screen_info = pygame.display.Info()
max_screen_width = screen_info.current_w - 100  # Leave some margin
max_screen_height = screen_info.current_h - 100

# Calculate visible area (what fits on screen)
info_panel_width = 400
visible_width = max(400, max_screen_width - info_panel_width)  # Ensure minimum width
visible_height = max(400, max_screen_height)  # Ensure minimum height

# Calculate what the tileset size would be at current scale
initial_tileset_width = tiles_per_row * TILE_SIZE * SCALE
initial_tileset_height = tiles_per_col * TILE_SIZE * SCALE

# Calculate scale to fit visible tiles on screen (but allow scrolling for larger tilesets)
# We want to ensure at least some tiles are visible, so calculate scale based on visible area
scale_factor = 1.0
if initial_tileset_width > visible_width:
    scale_factor = max(0.1, visible_width / initial_tileset_width)  # Ensure positive
if initial_tileset_height > visible_height:
    height_scale = max(0.1, visible_height / initial_tileset_height)  # Ensure positive
    scale_factor = min(scale_factor, height_scale)

# Apply scale if needed (but ensure minimum scale of 2 for visibility)
if scale_factor < 1.0 and scale_factor > 0:
    new_scale = max(2, int(SCALE * scale_factor))  # Minimum scale of 2 for visibility
    if new_scale < SCALE:
        SCALE = new_scale
        print(f"Scaled down to fit screen (scale factor: {scale_factor:.2f}, new scale: {SCALE})")
    else:
        print(f"Tileset fits on screen (scale: {SCALE})")
else:
    print(f"Tileset fits on screen (scale: {SCALE})")

# Calculate final tileset area after scaling
tileset_area_width = tiles_per_row * TILE_SIZE * SCALE
tileset_area_height = tiles_per_col * TILE_SIZE * SCALE

# Use visible area for display (tileset will be scrollable if larger)
# Ensure display dimensions are always positive
display_width = max(400, visible_width + info_panel_width)  # Minimum width
display_height = max(600, visible_height)  # Minimum height
print(f"Display size: {display_width}x{display_height}")
print(f"Tileset area: {tileset_area_width}x{tileset_area_height} (scale: {SCALE})")
if tileset_area_width > visible_width or tileset_area_height > visible_height:
    print(f"Tileset is scrollable - use arrow keys to navigate, Page Up/Down to scroll")
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Tileset Tile Selector")

# visible_width and visible_height are already set above, no need to reassign

# Fonts
font_large = pygame.font.Font(None, 36)
font_medium = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# State
current_terrain_index = 0
current_tile_x = 0
current_tile_y = 0
scroll_x = 0  # Horizontal scroll offset
scroll_y = 0  # Vertical scroll offset
selecting_layer = 1  # 1 = base layer, 2 = overlay layer
layer1_selection = None  # (x, y) for layer 1

# Start fresh - the shell script deletes the JSON file before running
# So we always start with an empty mappings dictionary
terrain_mappings = {}
current_terrain_index = 0
transparency_color = None  # Will be set by user selection

clock = pygame.time.Clock()
running = True

def get_current_terrain():
    """Get the terrain type we're currently selecting for."""
    if current_terrain_index < len(TERRAIN_TYPES):
        return TERRAIN_TYPES[current_terrain_index]
    return None

# Print initial terrain type
current_terrain = get_current_terrain()
if current_terrain:
    terrain_name = current_terrain.value.replace("_", " ").title()
    print(f"→ Now selecting tile for: {terrain_name}")

def draw_tileset_grid():
    """Draw the tileset grid with highlighted current tile (with scrolling)."""
    global scroll_x, scroll_y, visible_width, visible_height
    
    # Calculate full tileset area
    tileset_area_width = tiles_per_row * TILE_SIZE * SCALE
    tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
    
    # Clamp scroll to valid range
    max_scroll_x = max(0, tileset_area_width - visible_width)
    max_scroll_y = max(0, tileset_area_height - visible_height)
    scroll_x = max(0, min(scroll_x, max_scroll_x))
    scroll_y = max(0, min(scroll_y, max_scroll_y))
    
    # Draw background for visible tileset area
    tileset_bg_rect = pygame.Rect(0, 0, visible_width, visible_height)
    pygame.draw.rect(screen, (20, 20, 30), tileset_bg_rect)
    
    # Ensure we have a valid tileset
    if tileset is None:
        error_font = pygame.font.Font(None, 36)
        error_text = error_font.render("Error: Tileset not loaded", True, (255, 0, 0))
        screen.blit(error_text, (10, 10))
        return
    
    # Calculate which tiles are visible
    start_tile_x = scroll_x // (TILE_SIZE * SCALE)
    end_tile_x = min(tiles_per_row, start_tile_x + (visible_width // (TILE_SIZE * SCALE)) + 2)
    start_tile_y = scroll_y // (TILE_SIZE * SCALE)
    end_tile_y = min(tiles_per_col, start_tile_y + (visible_height // (TILE_SIZE * SCALE)) + 2)
    
    # Draw visible tiles
    for y in range(start_tile_y, end_tile_y):
        for x in range(start_tile_x, end_tile_x):
            # Calculate source rect in tileset
            source_x = x * TILE_SIZE
            source_y = y * TILE_SIZE
            
            # Bounds check
            if source_x >= tileset.get_width() or source_y >= tileset.get_height():
                continue
                
            source_rect = pygame.Rect(source_x, source_y, TILE_SIZE, TILE_SIZE)
            
            # Calculate destination position (scaled, with scroll offset)
            dest_x = x * TILE_SIZE * SCALE - scroll_x
            dest_y = y * TILE_SIZE * SCALE - scroll_y
            
            # Skip if outside visible area
            if dest_x + TILE_SIZE * SCALE < 0 or dest_x > visible_width:
                continue
            if dest_y + TILE_SIZE * SCALE < 0 or dest_y > visible_height:
                continue
            
            # Extract and scale tile
            try:
                # Create a surface for the tile
                tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                # Blit the portion of the tileset onto the tile surface
                tile_surface.blit(tileset, (0, 0), source_rect)
                
                # Scale to display size
                if SCALE != 1:
                    scaled_tile = pygame.transform.scale(tile_surface, (TILE_SIZE * SCALE, TILE_SIZE * SCALE))
                else:
                    scaled_tile = tile_surface
                
                # Draw tile (only if it's in the visible area)
                screen.blit(scaled_tile, (dest_x, dest_y))
            except Exception as e:
                # If tile extraction fails, draw a placeholder
                placeholder = pygame.Surface((TILE_SIZE * SCALE, TILE_SIZE * SCALE))
                placeholder.fill((50, 50, 50))
                screen.blit(placeholder, (dest_x, dest_y))
            
            # Draw border
            border_color = (100, 100, 100)
            if x == current_tile_x and y == current_tile_y:
                if selecting_layer == 1:
                    border_color = (255, 255, 0)  # Yellow for current tile (layer 1)
                else:
                    border_color = (255, 200, 0)  # Orange for current tile (layer 2)
            # Check if this tile is in any assigned mappings
            is_assigned = False
            for layers in terrain_mappings.values():
                if isinstance(layers, list):
                    for layer in layers:
                        if (x, y) == tuple(layer):
                            is_assigned = True
                            break
                    if is_assigned:
                        break
                elif (x, y) == layers:
                    is_assigned = True
                    break
            
            if is_assigned:
                border_color = (0, 255, 0)  # Green for already assigned tiles
            elif layer1_selection and (x, y) == layer1_selection:
                border_color = (200, 200, 0)  # Light yellow for selected layer 1
            
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
    # Use visible width, not full tileset width
    visible_width = tiles_per_row * TILE_SIZE * SCALE
    panel_x = visible_width + 10
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
        
        # Layer selection status
        if selecting_layer == 1:
            layer_text = font_medium.render("Layer 1 (Base)", True, (255, 255, 0))
        else:
            layer_text = font_medium.render("Layer 2 (Overlay)", True, (255, 200, 0))
        screen.blit(layer_text, (panel_x, panel_y))
        panel_y += 30
        
        if layer1_selection:
            layer1_text = font_small.render(f"Layer 1: ({layer1_selection[0]}, {layer1_selection[1]})", True, (200, 200, 0))
            screen.blit(layer1_text, (panel_x, panel_y))
            panel_y += 25
        
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
        "Page Up/Down:",
        "  Scroll tileset",
        "",
        "Home/End:",
        "  Scroll to top/bottom",
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
        
        for terrain_type in sorted(terrain_mappings.keys(), key=lambda t: TERRAIN_TYPES.index(t)):
            layers = terrain_mappings[terrain_type]
            terrain_name = terrain_type.value.replace("_", " ").title()
            
            # Format layer info
            if isinstance(layers, list) and len(layers) > 0:
                if len(layers) == 1:
                    layer_info = f"({layers[0][0]}, {layers[0][1]})"
                else:
                    layer_info = f"L1:({layers[0][0]},{layers[0][1]}) L2:({layers[1][0]},{layers[1][1]})"
            else:
                layer_info = str(layers)
            
            mapping_text = font_small.render(
                f"{terrain_name}: {layer_info}", 
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
                if selecting_layer == 2:
                    # Cancel layer 2 selection, use only layer 1
                    current_terrain = get_current_terrain()
                    if current_terrain and layer1_selection:
                        terrain_mappings[current_terrain] = [layer1_selection]
                        terrain_name = current_terrain.value.replace("_", " ").title()
                        print(f"✓ Assigned single tile ({layer1_selection[0]}, {layer1_selection[1]}) to {terrain_name} (Layer 2 cancelled)")
                        
                        # Save after each assignment
                        tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
                        save_mappings_to_file(terrain_mappings, tileset_name)
                        
                        # Move to next terrain type
                        current_terrain_index += 1
                        selecting_layer = 1
                        layer1_selection = None
                        
                        if current_terrain_index >= len(TERRAIN_TYPES):
                            print("\n✓ All terrain types assigned!")
                            
                            # Only prompt for transparency color if tileset doesn't have alpha channel
                            if not has_transparency:
                                # Prompt for transparency color
                                print("\n→ Select transparency color (greenscreen/chroma key)")
                                print("  Click on a tile in the tileset to select the color that should be transparent")
                                print("  Or press ENTER to skip (no transparency color)")
                                selecting_transparency = True
                                transparency_selected = False
                            else:
                                print("\n✓ Tileset has alpha channel - transparency will be preserved automatically")
                                selecting_transparency = False
                                transparency_selected = False
                            
                            while selecting_transparency and running:
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        running = False
                                        selecting_transparency = False
                                    elif event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                                            print("  No transparency color selected")
                                            selecting_transparency = False
                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                        if event.button == 1:  # Left click
                                            mouse_x, mouse_y = event.pos
                                            if mouse_x < visible_width:
                                                # Get pixel color from tileset at click position
                                                tile_x = (mouse_x + scroll_x) // (TILE_SIZE * SCALE)
                                                tile_y = (mouse_y + scroll_y) // (TILE_SIZE * SCALE)
                                                if 0 <= tile_x < tiles_per_row and 0 <= tile_y < tiles_per_col:
                                                    # Get pixel color from the tileset image
                                                    pixel_x = tile_x * TILE_SIZE + (mouse_x + scroll_x) % (TILE_SIZE * SCALE) * TILE_SIZE // (TILE_SIZE * SCALE)
                                                    pixel_y = tile_y * TILE_SIZE + (mouse_y + scroll_y) % (TILE_SIZE * SCALE) * TILE_SIZE // (TILE_SIZE * SCALE)
                                                    if 0 <= pixel_x < tileset.get_width() and 0 <= pixel_y < tileset.get_height():
                                                        transparency_color = tileset.get_at((pixel_x, pixel_y))[:3]  # Get RGB (ignore alpha)
                                                        print(f"  Selected transparency color: RGB{transparency_color}")
                                                        transparency_selected = True
                                                        selecting_transparency = False
                                if selecting_transparency:
                                    # Draw prompt on screen
                                    screen.fill((30, 30, 40))
                                    draw_tileset_grid()
                                    prompt_font = pygame.font.Font(None, 36)
                                    prompt_text = prompt_font.render("Click on transparency color (or ENTER to skip)", True, (255, 255, 0))
                                    screen.blit(prompt_text, (screen.get_width() // 2 - prompt_text.get_width() // 2, 50))
                                    pygame.display.flip()
                                    clock.tick(60)
                            
                            if transparency_selected:
                                # Store transparency color in the save function
                                save_mappings_to_file.transparency_color = list(transparency_color)
                            
                            tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
                            save_mappings_to_file(terrain_mappings, tileset_name)
                            print(f"Mappings saved to tileset_mappings.json")
                            running = False
                        else:
                            # Print next terrain type to console
                            next_terrain = get_current_terrain()
                            if next_terrain:
                                next_name = next_terrain.value.replace("_", " ").title()
                                print(f"\n→ Now selecting tile for: {next_name}")
                    else:
                        # No current terrain or layer1_selection, just exit
                        running = False
                else:
                    # ESC during layer 1: skip this terrain type (remove from mappings)
                    current_terrain = get_current_terrain()
                    if current_terrain:
                        if current_terrain in terrain_mappings:
                            del terrain_mappings[current_terrain]
                            terrain_name = current_terrain.value.replace("_", " ").title()
                            print(f"⊘ Skipped {terrain_name} (removed from mappings)")
                        else:
                            terrain_name = current_terrain.value.replace("_", " ").title()
                            print(f"⊘ Skipped {terrain_name}")
                        
                        # Save after removal
                        tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
                        save_mappings_to_file(terrain_mappings, tileset_name)
                        
                        # Move to next terrain type
                        current_terrain_index += 1
                        selecting_layer = 1
                        layer1_selection = None
                        
                        if current_terrain_index >= len(TERRAIN_TYPES):
                            print("\n✓ All terrain types processed!")
                            running = False
                        else:
                            # Print next terrain type to console
                            next_terrain = get_current_terrain()
                            if next_terrain:
                                next_name = next_terrain.value.replace("_", " ").title()
                                print(f"\n→ Now selecting tile for: {next_name}")
                    else:
                        # No current terrain, just exit
                        running = False
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Assign current tile to current layer
                current_terrain = get_current_terrain()
                if current_terrain:
                    if selecting_layer == 1:
                        # Select layer 1 (base)
                        layer1_selection = (current_tile_x, current_tile_y)
                        terrain_name = current_terrain.value.replace("_", " ").title()
                        print(f"✓ Selected Layer 1: tile ({current_tile_x}, {current_tile_y}) for {terrain_name}")
                        # Move to layer 2 selection
                        selecting_layer = 2
                        print(f"→ Now select Layer 2 (Overlay) - or press ESC to use only Layer 1")
                    else:
                        # Select layer 2 (overlay)
                        layer2_selection = (current_tile_x, current_tile_y)
                        terrain_name = current_terrain.value.replace("_", " ").title()
                        
                        # Check if same tile selected for both layers
                        if layer1_selection == layer2_selection:
                            # Use single layer
                            terrain_mappings[current_terrain] = [layer1_selection]
                            print(f"✓ Assigned single tile ({layer1_selection[0]}, {layer1_selection[1]}) to {terrain_name}")
                        else:
                            # Use two layers
                            terrain_mappings[current_terrain] = [layer1_selection, layer2_selection]
                            print(f"✓ Assigned Layer 1: ({layer1_selection[0]}, {layer1_selection[1]}), Layer 2: ({layer2_selection[0]}, {layer2_selection[1]}) to {terrain_name}")
                        
                        # Save after each assignment (so progress is preserved)
                        tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
                        save_mappings_to_file(terrain_mappings, tileset_name)
                        
                        # Move to next terrain type
                        current_terrain_index += 1
                        selecting_layer = 1
                        layer1_selection = None
                        
                        if current_terrain_index >= len(TERRAIN_TYPES):
                            print("\n✓ All terrain types assigned!")
                            
                            # Only prompt for transparency color if tileset doesn't have alpha channel
                            if not has_transparency:
                                # Prompt for transparency color
                                print("\n→ Select transparency color (greenscreen/chroma key)")
                                print("  Click on a tile in the tileset to select the color that should be transparent")
                                print("  Or press ENTER to skip (no transparency color)")
                                selecting_transparency = True
                                transparency_selected = False
                            else:
                                print("\n✓ Tileset has alpha channel - transparency will be preserved automatically")
                                selecting_transparency = False
                                transparency_selected = False
                            
                            while selecting_transparency and running:
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        running = False
                                        selecting_transparency = False
                                    elif event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                                            print("  No transparency color selected")
                                            selecting_transparency = False
                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                        if event.button == 1:  # Left click
                                            mouse_x, mouse_y = event.pos
                                            if mouse_x < visible_width:
                                                # Get pixel color from tileset at click position
                                                tile_x = (mouse_x + scroll_x) // (TILE_SIZE * SCALE)
                                                tile_y = (mouse_y + scroll_y) // (TILE_SIZE * SCALE)
                                                if 0 <= tile_x < tiles_per_row and 0 <= tile_y < tiles_per_col:
                                                    # Get pixel color from the tileset image
                                                    pixel_x = tile_x * TILE_SIZE + (mouse_x + scroll_x) % (TILE_SIZE * SCALE) * TILE_SIZE // (TILE_SIZE * SCALE)
                                                    pixel_y = tile_y * TILE_SIZE + (mouse_y + scroll_y) % (TILE_SIZE * SCALE) * TILE_SIZE // (TILE_SIZE * SCALE)
                                                    if 0 <= pixel_x < tileset.get_width() and 0 <= pixel_y < tileset.get_height():
                                                        transparency_color = tileset.get_at((pixel_x, pixel_y))[:3]  # Get RGB (ignore alpha)
                                                        print(f"  Selected transparency color: RGB{transparency_color}")
                                                        transparency_selected = True
                                                        selecting_transparency = False
                                if selecting_transparency:
                                    # Draw prompt on screen
                                    screen.fill((30, 30, 40))
                                    draw_tileset_grid()
                                    prompt_font = pygame.font.Font(None, 36)
                                    prompt_text = prompt_font.render("Click on transparency color (or ENTER to skip)", True, (255, 255, 0))
                                    screen.blit(prompt_text, (screen.get_width() // 2 - prompt_text.get_width() // 2, 50))
                                    pygame.display.flip()
                                    clock.tick(60)
                            
                            if transparency_selected:
                                # Store transparency color in the save function
                                save_mappings_to_file.transparency_color = list(transparency_color)
                            
                            tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
                            save_mappings_to_file(terrain_mappings, tileset_name)
                            print(f"Mappings saved to tileset_mappings.json")
                            running = False
                        else:
                            # Print next terrain type to console
                            next_terrain = get_current_terrain()
                            if next_terrain:
                                next_name = next_terrain.value.replace("_", " ").title()
                                print(f"\n→ Now selecting tile for: {next_name}")
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                current_tile_x = max(0, current_tile_x - 1)
                # Auto-scroll to keep current tile visible
                tileset_area_width = tiles_per_row * TILE_SIZE * SCALE
                tile_pixel_x = current_tile_x * TILE_SIZE * SCALE
                max_scroll_x = max(0, tileset_area_width - visible_width)
                if tile_pixel_x < scroll_x:
                    scroll_x = max(0, tile_pixel_x)
                elif tile_pixel_x + TILE_SIZE * SCALE > scroll_x + visible_width:
                    scroll_x = min(max_scroll_x, tile_pixel_x + TILE_SIZE * SCALE - visible_width)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                current_tile_x = min(tiles_per_row - 1, current_tile_x + 1)
                # Auto-scroll to keep current tile visible
                tileset_area_width = tiles_per_row * TILE_SIZE * SCALE
                tile_pixel_x = current_tile_x * TILE_SIZE * SCALE
                max_scroll_x = max(0, tileset_area_width - visible_width)
                if tile_pixel_x + TILE_SIZE * SCALE > scroll_x + visible_width:
                    scroll_x = min(max_scroll_x, tile_pixel_x + TILE_SIZE * SCALE - visible_width)
                elif tile_pixel_x < scroll_x:
                    scroll_x = max(0, tile_pixel_x)
            elif event.key in (pygame.K_UP, pygame.K_w):
                current_tile_y = max(0, current_tile_y - 1)
                # Auto-scroll to keep current tile visible
                tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                tile_pixel_y = current_tile_y * TILE_SIZE * SCALE
                max_scroll_y = max(0, tileset_area_height - visible_height)
                if tile_pixel_y < scroll_y:
                    scroll_y = max(0, tile_pixel_y)
                elif tile_pixel_y + TILE_SIZE * SCALE > scroll_y + visible_height:
                    scroll_y = min(max_scroll_y, tile_pixel_y + TILE_SIZE * SCALE - visible_height)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                current_tile_y = min(tiles_per_col - 1, current_tile_y + 1)
                # Auto-scroll to keep current tile visible
                tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                tile_pixel_y = current_tile_y * TILE_SIZE * SCALE
                max_scroll_y = max(0, tileset_area_height - visible_height)
                if tile_pixel_y + TILE_SIZE * SCALE > scroll_y + visible_height:
                    scroll_y = min(max_scroll_y, tile_pixel_y + TILE_SIZE * SCALE - visible_height)
                elif tile_pixel_y < scroll_y:
                    scroll_y = max(0, tile_pixel_y)
            elif event.key == pygame.K_PAGEUP:
                # Scroll up one screen
                tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                scroll_y = max(0, scroll_y - visible_height)
            elif event.key == pygame.K_PAGEDOWN:
                # Scroll down one screen
                tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                max_scroll_y = max(0, tileset_area_height - visible_height)
                scroll_y = min(max_scroll_y, scroll_y + visible_height)
            elif event.key == pygame.K_HOME:
                # Scroll to top
                scroll_y = 0
            elif event.key == pygame.K_END:
                # Scroll to bottom
                tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                max_scroll_y = max(0, tileset_area_height - visible_height)
                scroll_y = max_scroll_y
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = event.pos
                # Check if click is in tile area (use the global visible_width)
                if mouse_x < visible_width:
                    # Account for scroll offset
                    tile_x = (mouse_x + scroll_x) // (TILE_SIZE * SCALE)
                    tile_y = (mouse_y + scroll_y) // (TILE_SIZE * SCALE)
                    if 0 <= tile_x < tiles_per_row and 0 <= tile_y < tiles_per_col:
                        current_tile_x = tile_x
                        current_tile_y = tile_y
                        # Auto-scroll to keep selected tile visible
                        tileset_area_width = tiles_per_row * TILE_SIZE * SCALE
                        tileset_area_height = tiles_per_col * TILE_SIZE * SCALE
                        tile_pixel_x = current_tile_x * TILE_SIZE * SCALE
                        tile_pixel_y = current_tile_y * TILE_SIZE * SCALE
                        max_scroll_x = max(0, tileset_area_width - visible_width)
                        max_scroll_y = max(0, tileset_area_height - visible_height)
                        if tile_pixel_x < scroll_x:
                            scroll_x = max(0, tile_pixel_x)
                        elif tile_pixel_x + TILE_SIZE * SCALE > scroll_x + visible_width:
                            scroll_x = min(max_scroll_x, tile_pixel_x + TILE_SIZE * SCALE - visible_width)
                        if tile_pixel_y < scroll_y:
                            scroll_y = max(0, tile_pixel_y)
                        elif tile_pixel_y + TILE_SIZE * SCALE > scroll_y + visible_height:
                            scroll_y = min(max_scroll_y, tile_pixel_y + TILE_SIZE * SCALE - visible_height)
    
    # Clear screen
    screen.fill((30, 30, 40))
    
    # Draw tileset grid (left side)
    draw_tileset_grid()
    
    # Draw info panel (right side)
    draw_info_panel()
    
    # Force update display
    pygame.display.flip()
    clock.tick(60)

# Save mappings before exiting (in case user exits early)
if terrain_mappings:
    tileset_name = os.path.splitext(os.path.basename(TILESET_PATH))[0]
    save_mappings_to_file(terrain_mappings, tileset_name)

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
            layers = terrain_mappings[terrain_type]
            terrain_name = terrain_type.value
            # Handle both old format (tuple) and new format (list of layers)
            if isinstance(layers, list) and len(layers) > 0:
                if len(layers) == 1:
                    print(f"  {terrain_name}: Layer 1 {layers[0]}")
                else:
                    print(f"  {terrain_name}: Layer 1 {layers[0]}, Layer 2 {layers[1]}")
            else:
                print(f"  {terrain_name}: {layers}")
        else:
            terrain_name = terrain_type.value
            print(f"  {terrain_name}: NOT ASSIGNED")
    print("="*60)

