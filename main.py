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
from map_list_screen import MapListScreen
from map_saver import save_map, load_map, map_name_exists
from text_input import get_text_input
from settlements import SettlementType
from play_screen import PlayScreen
from save_list_screen import SaveListScreen
from save_game import load_game
from dialog import show_message_dialog

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32  # Display tile size (tilesets will be scaled to this size)
MAP_WIDTH = 4000
MAP_HEIGHT = 1000

def generate_map_with_progress(screen: pygame.Surface, title_screen: TitleScreen, 
                               width: int = MAP_WIDTH, height: int = MAP_HEIGHT, 
                               seed: int = None):
    """
    Generate map while showing progress on title screen.
    
    Args:
        screen: Pygame surface
        title_screen: Title screen instance for progress updates
        width: Map width in tiles
        height: Map height in tiles
        seed: Random seed for map generation (None for random)
        
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
    generator = MapGenerator(width, height, seed=seed, 
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
    settlements = []  # Initialize settlements list
    map_was_generated = True  # Initialize flag (will be set correctly when loading/generating)
    
    # Outer loop - handles returning to menu after ESC
    while True:
        # Main menu loop
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
                    result = 'new_game'  # Preserve result
                    break
                elif result == 'continue':
                    # Show save list screen
                    save_list = SaveListScreen(screen, settlements=[])
                    save_list.render()
                    
                    loaded_play_screen = None  # Store loaded play screen
                    save_list_running = True
                    while save_list_running:
                        for save_event in pygame.event.get():
                            if save_event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit(0)
                            
                            save_result = save_list.handle_event(save_event)
                            if save_result == 'back':
                                # Return to main menu
                                save_list_running = False
                                main_menu.render()
                                break
                            elif isinstance(save_result, tuple) and save_result[0] == 'load':
                                save_filepath = save_result[1]
                                print(f"Loading save from {save_filepath}...")
                                
                                # Load save data
                                saved_state = load_game(save_filepath)
                                if saved_state:
                                    # Load the map file
                                    map_filepath = saved_state.get('map_filepath')
                                    if map_filepath and os.path.exists(map_filepath):
                                        loaded = load_map(map_filepath)
                                        if loaded:
                                            map_data, map_width, map_height, map_name, loaded_settlements, seed, worldbuilding_data = loaded
                                            settlements = loaded_settlements
                                            
                                            # Update save list with settlements for location display
                                            save_list.set_settlements(settlements)
                                            
                                            # Create play screen with saved state
                                            print("Entering play screen with saved game...")
                                            loaded_play_screen = PlayScreen(
                                                screen, map_data, map_width, map_height, settlements,
                                                tile_size=TILE_SIZE, map_filepath=map_filepath,
                                                saved_state=saved_state, worldbuilding_data=worldbuilding_data
                                            )
                                            save_list_running = False
                                            main_menu_running = False
                                            result = 'play_from_save'
                                            break
                                        else:
                                            print(f"Error loading map from {map_filepath}")
                                    else:
                                        print(f"Map file not found: {map_filepath}")
                                else:
                                    print(f"Error loading save file: {save_filepath}")
                                
                                if save_list_running:
                                    save_list.render()
                        
                        if save_list_running:
                            save_list.render()
                            pygame.display.flip()
                            clock.tick(60)
                    
                    # If we loaded a game, enter play screen directly
                    if loaded_play_screen is not None:
                        play_screen = loaded_play_screen
                        play_running = True
                        
                        while play_running:
                            # Calculate delta time
                            dt = clock.tick(60) / 1000.0  # Convert milliseconds to seconds
                            
                            for play_event in pygame.event.get():
                                if play_event.type == pygame.QUIT:
                                    play_running = False
                                    return_to_menu = True
                                    break
                                
                                result = play_screen.handle_event(play_event)
                                
                                if result == 'quit':
                                    play_running = False
                                    # Return to main menu
                                    break
                            
                            if play_running:
                                play_screen.update(dt)
                                play_screen.render()
                                pygame.display.flip()
                            else:
                                break
                        
                        # After play screen, return to main menu
                        main_menu_running = True
                        result = None
                        continue
                    
                    if result != 'play_from_save':
                        main_menu.render()
                else:
                    main_menu.render()
            
            clock.tick(60)
            if not main_menu_running:
                break
        
        # If user selected "Start a New Game", show map menu
        # result should already be set from main menu
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
                        # Return to main menu - break out of map menu loop
                        map_menu_running = False
                        # Set result to None so we continue the main menu loop
                        result = None
                        break
                    elif result == 'generate':
                        map_menu_running = False
                        # Will generate map below
                        break
                    elif result == 'load_maps':
                        # Show map list screen
                        map_list = MapListScreen(screen)
                        map_list.render()
                        
                        map_list_running = True
                        while map_list_running:
                            for list_event in pygame.event.get():
                                if list_event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit(0)
                                
                                list_result = map_list.handle_event(list_event)
                                if list_result == 'back':
                                    # Return to map menu
                                    map_list_running = False
                                    map_menu.render()
                                    break
                                elif isinstance(list_result, tuple) and list_result[0] == 'load':
                                    filepath = list_result[1]
                                    filepath = list_result[1]
                                    print(f"Loading map from {filepath}...")
                                    loaded = load_map(filepath)
                                    if loaded:
                                        map_data, map_width, map_height, map_name, loaded_settlements, seed, worldbuilding_data = loaded
                                        current_seed = seed  # Store the loaded seed
                                        settlements = loaded_settlements  # Assign loaded settlements
                                        map_was_generated = False  # Track that this map was loaded, not generated
                                        
                                        print(f"Map '{map_name}' loaded: {map_width}x{map_height} tiles")
                                        if seed is not None:
                                            print(f"Map seed: {seed}")
                                        else:
                                            print("Map seed: Random (not saved)")
                                        print(f"Debug: Loaded {len(settlements)} settlements from file")
                                        if settlements:
                                            town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)
                                            village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)
                                            city_count = sum(1 for s in settlements if s.settlement_type == SettlementType.CITY)
                                            print(f"Loaded {city_count} cities, {town_count} towns, and {village_count} villages")
                                            # Verify vassal relationships
                                            villages_with_towns = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE and s.vassal_to)
                                            towns_with_cities = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN and s.vassal_to)
                                            print(f"Vassal relationships: {villages_with_towns} villages linked to towns, {towns_with_cities} towns linked to cities")
                                        else:
                                            print("WARNING: No settlements loaded from file!")
                                        generator = None
                                        map_list_running = False
                                        map_menu_running = False
                                        result = ('load', filepath)  # Set result to break out
                                        print(f"Debug: Map loaded, setting result={result}, breaking from map list loop")
                                        break
                        else:
                            print("Failed to load map. Please try again.")
                            map_list.render()
                            
                            if map_list_running:
                                map_list.render()
                                pygame.display.flip()
                                clock.tick(60)
                        
                        # If we loaded a map, break out of map menu loop
                        if isinstance(result, tuple) and result[0] == 'load':
                            print(f"Debug: Breaking from map menu loop, result={result}")
                            break
                    else:
                        map_menu.render()
                
                clock.tick(60)
                if not map_menu_running:
                    break
            
            # After map menu loop, check what to do next
            print(f"Debug: After map menu loop. result={result}, type={type(result)}")
            # If we got 'back', continue the outer loop to show main menu again
            if result == 'back':
                print("Debug: result is 'back', continuing outer loop")
                continue
            # If we got a result to show map, fall through to map viewing (don't break!)
            # We're still in the outer while True loop, so we'll continue to map viewing below
        
        # Map viewing section - entered when result indicates we should show a map
        # This is still inside the outer while True loop
        print(f"Debug: After map menu section. result={result}, type={type(result)}")
        if result in ('generate', 'load') or (isinstance(result, tuple) and result[0] == 'load'):
            print(f"Debug: Entering map viewing section. result={result}, map_data={'None' if map_data is None else 'exists'}, map_was_generated={map_was_generated}")
            # If no map was loaded, generate a new one
            generator = None
            # Only set map_was_generated to True if we're generating (not loading)
            # If we loaded a map, map_was_generated should already be set to False from the load
            if map_data is None:
                map_was_generated = True  # Track that this map was generated
                settlements = []
                current_seed = None  # Track the seed used for the current map
                # Show title screen for generation
                title_screen = TitleScreen(screen)
                title_screen.render()
                
                # Get seed from user (optional)
                seed_input = get_text_input(screen, "Enter seed (or leave empty for random):", "", 20)
                seed = None
                if seed_input:
                    seed_input = seed_input.strip()
                    if seed_input:
                        try:
                            seed = int(seed_input)
                            print(f"Using seed: {seed}")
                        except ValueError:
                            print(f"Invalid seed '{seed_input}', using random seed")
                            seed = None
                    else:
                        print("Using random seed")
                else:
                    print("Using random seed")
                
                current_seed = seed  # Store the seed used
                
                # Generate map with progress updates
                print("Generating map...")
                map_data, generator = generate_map_with_progress(screen, title_screen, seed=seed)
                print(f"Map generated: {map_width}x{map_height} tiles")
                
                # Get settlements from generator
                if generator and hasattr(generator, 'settlements'):
                    settlements = generator.settlements
                    worldbuilding_data = None  # No worldbuilding data generation
                    town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)
                    village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)
                    city_count = sum(1 for s in settlements if s.settlement_type == SettlementType.CITY)
                    total_settlements = len(settlements)
                    print(f"Placed {city_count} cities, {town_count} towns, and {village_count} villages (total: {total_settlements} settlements)")
                    # Debug: Print first few settlement positions
                    if settlements:
                        print(f"Debug: First 5 settlements positions:")
                        for i, s in enumerate(settlements[:5]):
                            x, y = s.get_position()
                            print(f"  {i+1}. {s.settlement_type.value} at ({x}, {y})")
            
            # Ensure settlements is initialized (should be set from load or generation)
            # settlements should already be set from load or generation above
            print(f"Debug: Before renderer creation - settlements count: {len(settlements) if settlements else 0}, map_data: {'exists' if map_data is not None else 'None'}")
    
            # Create renderer
            try:
                renderer = MapRenderer(tile_size=TILE_SIZE)
                print("Debug: Renderer created successfully")
            except Exception as e:
                print(f"ERROR: Failed to create renderer: {e}")
                import traceback
                traceback.print_exc()
                continue  # Skip to next iteration of outer loop
            
            # Debug: Check settlements
            if settlements:
                print(f"Debug: settlements list has {len(settlements)} items")
                if len(settlements) > 0:
                    x, y = settlements[0].get_position()
                    print(f"Debug: First settlement at ({x}, {y}), type: {settlements[0].settlement_type.value}")
            else:
                print("Debug: settlements is None or empty!")
    
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
            return_to_menu = False  # Flag to return to map menu when ESC is pressed
            enter_play_screen = False  # Flag to enter play screen
            
            print(f"Debug: Entering map viewing loop. map_data is {'None' if map_data is None else 'not None'}, settlements count: {len(settlements) if settlements else 0}, map_was_generated={map_was_generated}")
            try:
                while running:
                    # Handle events
                    for event in pygame.event.get():

                        if event.type == pygame.QUIT:

                            print("Debug: QUIT event received")

                            running = False

                        elif event.type == pygame.MOUSEBUTTONDOWN:

                            if event.button == 1:  # Left mouse button
                                # Get mouse position from event
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
                                    # Get mouse position from event (already set above)
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
                                        # Set selection for arrows to be drawn
                                        if clicked_settlement.settlement_type == SettlementType.VILLAGE:
                                            selected_village = clicked_settlement
                                            selected_town = None
                                            selected_city = None
                                        elif clicked_settlement.settlement_type == SettlementType.TOWN:
                                            selected_town = clicked_settlement
                                            selected_village = None
                                            selected_city = None
                                        elif clicked_settlement.settlement_type == SettlementType.CITY:
                                            selected_city = clicked_settlement
                                            selected_village = None
                                            selected_town = None
                                        
                                        # Show settlement dialog with worldbuilding data (if available from saved map)
                                        from settlement_dialog import show_settlement_dialog
                                        show_settlement_dialog(screen, clock, clicked_settlement, 
                                                              settlements, worldbuilding_data)

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

                                    # Return to map menu instead of quitting

                                    running = False

                                    return_to_menu = True

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

                        
                                # Get seed from user (optional)

                                seed_input = get_text_input(screen, "Enter seed (or leave empty for random):", "", 20)

                                seed = None

                                if seed_input:

                                    seed_input = seed_input.strip()

                                    if seed_input:

                                        try:

                                            seed = int(seed_input)

                                            print(f"Using seed: {seed}")

                                        except ValueError:

                                            print(f"Invalid seed '{seed_input}', using random seed")

                                            seed = None

                                    else:

                                        print("Using random seed")

                                else:

                                    print("Using random seed")

                        
                                current_seed = seed  # Update the current seed

                                map_data, generator = generate_map_with_progress(screen, title_screen, seed=seed)

                                map_width = MAP_WIDTH

                                map_height = MAP_HEIGHT

                                map_was_generated = True  # Mark as generated after regeneration

                                # Get settlements from generator
                                if generator and hasattr(generator, 'settlements'):
                                    settlements = generator.settlements
                                    worldbuilding_data = None  # No worldbuilding data generation

                                    town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)

                                    village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)

                                    city_count = sum(1 for s in settlements if s.settlement_type == SettlementType.CITY)

                                    total_settlements = len(settlements)

                                    print(f"Placed {city_count} cities, {town_count} towns, and {village_count} villages (total: {total_settlements} settlements)")

                                print("Map regenerated!")

                            elif event.key == pygame.K_RETURN and not map_view_mode:

                                # Accept map and proceed to play screen (ENTER key)

                                # If map was generated, save it first

                                if map_was_generated:

                                    print("Saving generated map...")

                                    map_name = get_text_input(screen, "Enter map name:", "", 50)

                                    if map_name:

                                        map_name = map_name.strip()

                                        if not map_name:

                                            print("Map name cannot be empty")

                                        elif map_name_exists(map_name):

                                            print(f"Map name '{map_name}' already exists. Please choose a different name.")

                                        else:

                                            import datetime

                                            maps_dir = "maps"

                                            os.makedirs(maps_dir, exist_ok=True)

                                            # Use sanitized map name for filename

                                            safe_name = "".join(c for c in map_name if c.isalnum() or c in (' ', '-', '_')).strip()

                                            safe_name = safe_name.replace(' ', '_')

                                            if not safe_name:

                                                safe_name = "map"

                                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                                            filename = f"{safe_name}_{timestamp}.banshee"

                                            filepath = os.path.join(maps_dir, filename)

                                            print(f"Debug: Saving {len(settlements) if settlements else 0} settlements")

                                            if settlements:

                                                print(f"Debug: Settlement types: {[s.settlement_type.value for s in settlements[:5]]}")

                                            if save_map(map_data, map_width, map_height, filepath, map_name, settlements, seed=current_seed, worldbuilding_data=worldbuilding_data):

                                                print(f"Map '{map_name}' saved to {filepath}")

                                                if current_seed is not None:

                                                    print(f"Saved with seed: {current_seed}")

                                                if settlements:

                                                    print(f"Saved {len(settlements)} settlements")

                                                    # Verify vassal relationships are saved

                                                    villages_with_towns = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE and s.vassal_to)

                                                    towns_with_cities = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN and s.vassal_to)

                                                    print(f"Vassal relationships saved: {villages_with_towns} villages linked to towns, {towns_with_cities} towns linked to cities")

                                                # Proceed to play screen after saving

                                                print("Accepting map and proceeding to play screen...")

                                                enter_play_screen = True

                                                running = False  # Exit map viewing loop

                                                break  # Break from event loop

                                            else:

                                                print("ERROR: Failed to save map! Cannot proceed.")

                                    else:

                                        print("Map save cancelled. Cannot proceed without saving.")

                                else:

                                    # Map was loaded, proceed directly to play screen

                                    print("Accepting loaded map and proceeding to play screen...")

                                    enter_play_screen = True

                                    running = False  # Exit map viewing loop

                                    break  # Break from event loop

            
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


                        # Render map


                        renderer.render_map(map_data, screen, camera_x, camera_y, settlements, 


                                                      selected_village=selected_village,


                                                      selected_town=selected_town,


                                                      selected_city=selected_city)


                        # Settlement dialogs are now shown via show_settlement_dialog when clicked


                        # Draw UI info
                        font = pygame.font.Font(None, 24)
                        info_text = [
                            f"Camera: ({camera_x}, {camera_y})",
                            "Arrow Keys/WASD: Move camera",
                            "M: Map view (zoomed out)",
                            "R: Regenerate map",
                            "ENTER: Accept map and proceed",
                            "Click settlements to view info",
                            "ESC: Return to map menu"
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

            
                    # If ESC was pressed, break out to return to menu

                    if return_to_menu:

                        # Reset flag and return to map menu

                        return_to_menu = False

                        # Break out of map viewing loop to return to outer loop

                        break

            
                    # Check if we should enter play screen (after accepting map)

                    if enter_play_screen:

                        # Enter play screen

                        print("Entering play screen...")

                        # Determine map filepath if we loaded a map

                        current_map_filepath = None

                        if isinstance(result, tuple) and result[0] == 'load':

                            current_map_filepath = result[1]

                        elif map_was_generated:

                            # For generated maps, we don't have a filepath yet (would need to save first)

                            current_map_filepath = None

                
                        # Get worldbuilding_data if available (from loaded map or generator)
                        current_worldbuilding_data = None
                        if 'worldbuilding_data' in locals():
                            current_worldbuilding_data = worldbuilding_data
                        elif 'generator' in locals() and hasattr(generator, 'worldbuilding_data'):
                            current_worldbuilding_data = generator.worldbuilding_data
                        
                        play_screen = PlayScreen(
                            screen, map_data, map_width, map_height, settlements,
                            tile_size=TILE_SIZE, map_filepath=current_map_filepath,
                            worldbuilding_data=current_worldbuilding_data
                        )

                        play_running = True

                
                        while play_running:

                            # Calculate delta time

                            dt = clock.tick(60) / 1000.0  # Convert milliseconds to seconds

                    
                            for play_event in pygame.event.get():

                                if play_event.type == pygame.QUIT:

                                    play_running = False

                                    return_to_menu = True

                                    break

                        
                                result = play_screen.handle_event(play_event)

                                if result == 'quit':

                                    play_running = False

                                    # Return to map menu

                                    break

                    
                            if play_running:

                                play_screen.update(dt)

                                play_screen.render()

                                pygame.display.flip()

                            else:

                                break

                
                        # After play screen, check if we came from save load

                        if result == 'play_from_save':

                            # If we loaded from save, we're done (could return to menu or quit)

                            result = None

                            main_menu_running = True

                            continue

                
                        # After play screen, return to map menu

                        if return_to_menu:

                            break

                    
            except Exception as e:
                print(f"ERROR in map viewing loop: {e}")
                import traceback
                traceback.print_exc()
                # Don't break - let it continue to show menu again
                pass
            
            # After map viewing loop ends, return to main menu
            # (This happens when ESC is pressed or when user quits)
            print("Debug: Map viewing loop ended, continuing to main menu")
            continue  # Loop back to show main menu again

if __name__ == "__main__":
    main()

