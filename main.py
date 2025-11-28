"""
Main entry point for the Banshee RPG.
Displays a generated map with different terrain types.
"""
import pygame
import sys
import os
from map_generator import MapGenerator
from map_renderer import MapRenderer
from title_screen import TitleScreen
from menu_screen import MenuScreen
from map_menu_screen import MapMenuScreen
from map_saver import save_map, load_map
from settlements import SettlementType


# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32
MAP_WIDTH = 4000
MAP_HEIGHT = 1000


def generate_map_with_progress(screen: pygame.Surface, title_screen: TitleScreen, 
                               width: int = MAP_WIDTH, height: int = MAP_HEIGHT):
    """
    Generate map while showing progress on title screen.
    
    Args:
        screen: Pygame surface
        title_screen: Title screen instance for progress updates
        width: Map width in tiles
        height: Map height in tiles
        
    Returns:
        Tuple of (generated map data, generator) - generator contains settlements
    """
    def progress_callback(progress: float, message: str):
        """Callback for map generation progress."""
        title_screen.update_progress(progress, message)
        title_screen.render()
        # Process events to keep window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
    
    # Create generator with progress callback
    generator = MapGenerator(width, height, seed=42, 
                           progress_callback=progress_callback)
    
    # Generate map (progress will be shown via callback)
    map_data = generator.generate()
    
    return map_data, generator


def main():
    """Main game loop."""
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Banshee RPG")
    clock = pygame.time.Clock()
    
    # Show main menu screen first
    map_data = None
    map_width = MAP_WIDTH
    map_height = MAP_HEIGHT
    
    # Main menu loop
    while True:
        main_menu = MenuScreen(screen)
        main_menu.render()
        
        main_menu_running = True
        while main_menu_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                
                result = main_menu.handle_event(event)
                if result == 'quit':
                    pygame.quit()
                    sys.exit(0)
                elif result == 'new_game':
                    # Open map menu
                    main_menu_running = False
                    break
                elif result == 'continue':
                    # Placeholder - do nothing for now
                    # Just re-render the menu
                    main_menu.render()
                else:
                    main_menu.render()
            
            clock.tick(60)
            if not main_menu_running:
                break
        
        # If user selected "Start a New Game", show map menu
        if result == 'new_game':
            map_menu = MapMenuScreen(screen)
            map_menu.render()
            
            map_menu_running = True
            while map_menu_running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit(0)
                    
                    result = map_menu.handle_event(event)
                    if result == 'back':
                        # Return to main menu
                        map_menu_running = False
                        break
                    elif result == 'generate':
                        map_menu_running = False
                        # Will generate map below
                        break
                    elif isinstance(result, tuple) and result[0] == 'load':
                        filepath = result[1]
                        print(f"Loading map from {filepath}...")
                        loaded = load_map(filepath)
                        if loaded:
                            map_data, map_width, map_height, settlements = loaded
                            print(f"Map loaded: {map_width}x{map_height} tiles")
                            if settlements:
                                print(f"Loaded {len(settlements)} settlements")
                            generator = None
                            map_menu_running = False
                            break
                        else:
                            print("Failed to load map. Please try again.")
                    else:
                        map_menu.render()
                
                clock.tick(60)
            
            # If we got a result from map menu, break out of main menu loop
            if result in ('generate', 'load') or (isinstance(result, tuple) and result[0] == 'load'):
                break
    
    # If no map was loaded, generate a new one
    generator = None
    settlements = []
    if map_data is None:
        # Show title screen for generation
        title_screen = TitleScreen(screen)
        title_screen.render()
        
        # Generate map with progress updates
        print("Generating map...")
        map_data, generator = generate_map_with_progress(screen, title_screen)
        print(f"Map generated: {map_width}x{map_height} tiles")
        
        # Get settlements from generator
        if generator and hasattr(generator, 'settlements'):
            settlements = generator.settlements
            town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)
            village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)
            city_count = sum(1 for s in settlements if s.settlement_type == SettlementType.CITY)
            total_settlements = len(settlements)
            print(f"Placed {city_count} cities, {town_count} towns, and {village_count} villages (total: {total_settlements} settlements)")
    
    # Create renderer
    renderer = MapRenderer(tile_size=TILE_SIZE)
    
    # Camera position (in tiles)
    camera_x = 0
    camera_y = 0
    
    # Camera movement speed
    camera_speed = 2
    
    # Map view mode
    map_view_mode = False
    overview_tile_size = 1  # Pixels per tile in overview
    overview_camera_x = 0
    overview_camera_y = 0
    overview_camera_speed = 10  # Faster movement in overview
    
    # Settlement selection
    selected_village = None  # Track selected village for connection line
    selected_town = None  # Track selected town for dialogue
    selected_city = None  # Track selected city for dialogue
    
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    
                    if map_view_mode:
                        # Handle clicks in overview map - zoom to clicked location
                        # Convert screen coordinates to map tile coordinates
                        clicked_tile_x = (mouse_x // overview_tile_size) + overview_camera_x
                        clicked_tile_y = (mouse_y // overview_tile_size) + overview_camera_y
                        
                        # Clamp to map bounds
                        clicked_tile_x = max(0, min(map_width - 1, clicked_tile_x))
                        clicked_tile_y = max(0, min(map_height - 1, clicked_tile_y))
                        
                        # Center the normal camera on the clicked location
                        viewport_width = SCREEN_WIDTH // TILE_SIZE
                        viewport_height = SCREEN_HEIGHT // TILE_SIZE
                        camera_x = clicked_tile_x - viewport_width // 2
                        camera_y = clicked_tile_y - viewport_height // 2
                        
                        # Clamp camera to map bounds
                        camera_x = max(0, min(map_width - viewport_width, camera_x))
                        camera_y = max(0, min(map_height - viewport_height, camera_y))
                        
                        # Exit overview mode
                        map_view_mode = False
                    else:
                        # Handle mouse clicks on settlements (only in normal view)
                        # Convert screen coordinates to tile coordinates
                        tile_x = mouse_x // TILE_SIZE + camera_x
                        tile_y = mouse_y // TILE_SIZE + camera_y
                        
                        # Check if a settlement was clicked
                        clicked_settlement = None
                        for settlement in settlements:
                            sx, sy = settlement.get_position()
                            # Check if click is within the settlement's tile
                            if sx == tile_x and sy == tile_y:
                                clicked_settlement = settlement
                                break
                        
                        if clicked_settlement:
                            if clicked_settlement.settlement_type == SettlementType.VILLAGE:
                                # Toggle village selection
                                if selected_village == clicked_settlement:
                                    selected_village = None  # Deselect if clicking same village
                                else:
                                    selected_village = clicked_settlement
                                    selected_town = None  # Close town dialogue if open
                                    selected_city = None  # Close city dialogue if open
                            elif clicked_settlement.settlement_type == SettlementType.TOWN:
                                # Toggle town dialogue
                                if selected_town == clicked_settlement:
                                    selected_town = None  # Close dialogue if clicking same town
                                else:
                                    selected_town = clicked_settlement
                                    selected_village = None  # Deselect village if one is selected
                                    selected_city = None  # Close city dialogue if open
                            elif clicked_settlement.settlement_type == SettlementType.CITY:
                                # Toggle city dialogue
                                if selected_city == clicked_settlement:
                                    selected_city = None  # Close dialogue if clicking same city
                                else:
                                    selected_city = clicked_settlement
                                    selected_village = None  # Deselect village if one is selected
                                    selected_town = None  # Close town dialogue if open
                        else:
                            # Clicked on empty space - deselect everything
                            selected_village = None
                            selected_town = None
                            selected_city = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if map_view_mode:
                        # Exit map view mode
                        map_view_mode = False
                    else:
                        running = False
                elif event.key == pygame.K_m:
                    # Toggle map view mode
                    map_view_mode = not map_view_mode
                    if map_view_mode:
                        # Initialize overview camera to center of map
                        overview_camera_x = map_width // 2 - (SCREEN_WIDTH // overview_tile_size) // 2
                        overview_camera_y = map_height // 2 - (SCREEN_HEIGHT // overview_tile_size) // 2
                elif event.key == pygame.K_r and not map_view_mode:
                    # Regenerate map (only in normal view)
                    print("Regenerating map...")
                    title_screen = TitleScreen(screen)
                    title_screen.render()
                    map_data, generator = generate_map_with_progress(screen, title_screen)
                    map_width = MAP_WIDTH
                    map_height = MAP_HEIGHT
                    # Get settlements from generator
                    if generator and hasattr(generator, 'settlements'):
                        settlements = generator.settlements
                        town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)
                        village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)
                        city_count = sum(1 for s in settlements if s.settlement_type == SettlementType.CITY)
                        total_settlements = len(settlements)
                        print(f"Placed {city_count} cities, {town_count} towns, and {village_count} villages (total: {total_settlements} settlements)")
                    print("Map regenerated!")
                elif event.key == pygame.K_s and not map_view_mode:
                    # Save map
                    import datetime
                    maps_dir = "maps"
                    os.makedirs(maps_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"map_{timestamp}.banshee"
                    filepath = os.path.join(maps_dir, filename)
                    if save_map(map_data, map_width, map_height, filepath, settlements):
                        print(f"Map saved to {filepath}")
                    else:
                        print("Failed to save map")
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        if map_view_mode:
            # Map view mode - show zoomed out overview
            # Handle camera movement in overview
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                overview_camera_x = max(0, overview_camera_x - overview_camera_speed)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                max_camera_x = map_width - (SCREEN_WIDTH // overview_tile_size)
                overview_camera_x = min(max_camera_x, overview_camera_x + overview_camera_speed)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                overview_camera_y = max(0, overview_camera_y - overview_camera_speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                max_camera_y = map_height - (SCREEN_HEIGHT // overview_tile_size)
                overview_camera_y = min(max_camera_y, overview_camera_y + overview_camera_speed)
            
            # Render overview map
            renderer.render_map_overview(map_data, screen, overview_tile_size, 
                                        overview_camera_x, overview_camera_y, settlements)
            
            # Draw viewport indicator showing where normal camera is
            viewport_width = SCREEN_WIDTH // TILE_SIZE
            viewport_height = SCREEN_HEIGHT // TILE_SIZE
            viewport_screen_x = (camera_x - overview_camera_x) * overview_tile_size
            viewport_screen_y = (camera_y - overview_camera_y) * overview_tile_size
            viewport_screen_w = viewport_width * overview_tile_size
            viewport_screen_h = viewport_height * overview_tile_size
            
            if (viewport_screen_x + viewport_screen_w > 0 and viewport_screen_x < SCREEN_WIDTH and
                viewport_screen_y + viewport_screen_h > 0 and viewport_screen_y < SCREEN_HEIGHT):
                # Draw viewport rectangle
                viewport_rect = pygame.Rect(
                    max(0, viewport_screen_x),
                    max(0, viewport_screen_y),
                    min(viewport_screen_w, SCREEN_WIDTH - max(0, viewport_screen_x)),
                    min(viewport_screen_h, SCREEN_HEIGHT - max(0, viewport_screen_y))
                )
                pygame.draw.rect(screen, (255, 255, 0), viewport_rect, 2)
            
            # Draw UI info for map view
            font = pygame.font.Font(None, 24)
            info_text = [
                "MAP VIEW - Zoomed Out",
                f"Overview Camera: ({overview_camera_x}, {overview_camera_y})",
                f"Normal Camera: ({camera_x}, {camera_y})",
                "Arrow Keys/WASD: Scroll overview",
                "Click: Zoom to location",
                "M: Exit map view",
                "ESC: Exit map view"
            ]
            y_offset = 10
            for text in info_text:
                text_surface = font.render(text, True, (255, 255, 255))
                # Draw with black background for readability
                bg_rect = text_surface.get_rect()
                bg_rect.x = 10
                bg_rect.y = y_offset
                pygame.draw.rect(screen, (0, 0, 0), bg_rect)
                screen.blit(text_surface, (10, y_offset))
                y_offset += 25
        else:
            # Normal view mode
            # Handle camera movement with arrow keys
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                camera_x = max(0, camera_x - camera_speed)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                camera_x = min(map_width - (SCREEN_WIDTH // TILE_SIZE), camera_x + camera_speed)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                camera_y = max(0, camera_y - camera_speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                camera_y = min(map_height - (SCREEN_HEIGHT // TILE_SIZE), camera_y + camera_speed)
            
            # Process economy updates for all settlements
            for settlement in settlements:
                settlement.process_economy()
            
            # Calculate player position (center of viewport)
            viewport_width = SCREEN_WIDTH // TILE_SIZE
            viewport_height = SCREEN_HEIGHT // TILE_SIZE
            player_tile_x = camera_x + viewport_width // 2
            player_tile_y = camera_y + viewport_height // 2
            
            # Check if player is on a settlement
            current_settlement = None
            for settlement in settlements:
                sx, sy = settlement.get_position()
                if sx == player_tile_x and sy == player_tile_y:
                    current_settlement = settlement
                    break
            
            # Render map
            renderer.render_map(map_data, screen, camera_x, camera_y, settlements, 
                              selected_village=selected_village,
                              selected_town=selected_town,
                              selected_city=selected_city)
            
            # Draw status window if player is on a settlement
            if current_settlement:
                renderer.draw_settlement_status(screen, current_settlement)
            
            # Draw town dialogue if a town is selected
            if selected_town:
                renderer.draw_town_dialogue(screen, selected_town)
            
            # Draw city dialogue if a city is selected
            if selected_city:
                renderer.draw_city_dialogue(screen, selected_city)
            
            # Draw UI info
            font = pygame.font.Font(None, 24)
            info_text = [
                f"Camera: ({camera_x}, {camera_y})",
                "Arrow Keys/WASD: Move camera",
                "M: Map view (zoomed out)",
                "R: Regenerate map",
                "S: Save map",
                "Click settlements to view info",
                "ESC: Quit"
            ]
            y_offset = 10
            for text in info_text:
                text_surface = font.render(text, True, (255, 255, 255))
                # Draw with black background for readability
                bg_rect = text_surface.get_rect()
                bg_rect.x = 10
                bg_rect.y = y_offset
                pygame.draw.rect(screen, (0, 0, 0), bg_rect)
                screen.blit(text_surface, (10, y_offset))
                y_offset += 25
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

