"""
Scrollable journal dialog showing quest information and archive.
"""
import pygame
from typing import Optional, Dict, List
from quest_location_maps import generate_quest_location_map
from text_utils import wrap_text


def show_journal_dialog(screen: pygame.Surface, clock: pygame.time.Clock,
                       quest: Optional[Dict] = None, quest_archive: Optional[List] = None) -> Optional[str]:
    """
    Show a scrollable dialog with quest information and archive.
    
    Args:
        screen: Pygame surface to draw on
        clock: Pygame clock for timing
        quest: The current quest dictionary (None if no active quest)
        quest_archive: List of archived quests
        
    Returns:
        'drop' if quest was dropped, None when user dismisses the dialog
    """
    if quest_archive is None:
        quest_archive = []
    
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Dialog dimensions
    dialog_width = min(700, int(screen_width * 0.85))
    dialog_height = min(600, int(screen_height * 0.85))
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    # Fonts
    title_font = pygame.font.Font(None, 36)
    header_font = pygame.font.Font(None, 28)
    body_font = pygame.font.Font(None, 22)
    small_font = pygame.font.Font(None, 20)
    
    # Mode: 'current' or 'archive'
    mode = 'current'
    
    waiting = True
    scroll_offset = 0
    scroll_speed = 20
    
    while waiting:
        # Build content lines based on mode
        content_lines = []
        
        if mode == 'current':
            if quest:
                # Title
                content_lines.append(('title', '=== JOURNAL ==='))
                content_lines.append(('spacer', ''))
                
                # Quest description format (only for fetch quests)
                quest_type = quest.get('quest_type', 'fetch')
                if quest_type == 'fetch':
                    # Format: "You must travel {time distance} to the {direction} of {settlement}. You will reach {location}. There, you must retrieve {item} for {person}."
                    distance_days = quest.get('distance_days', 0)
                    direction = quest.get('quest_direction', 'unknown')
                    settlement_name = quest.get('settlement_name', 'Unknown Settlement')
                    target_item = quest.get('target_item', 'item')
                    leader_name = quest.get('leader_name', 'Unknown Leader')
                    original_location_description = quest.get('original_location_description', quest.get('location_description', 'location'))
                    
                    # Format time distance
                    if distance_days < 1:
                        time_str = f"{int(distance_days * 24)} hours"
                    elif distance_days == 1:
                        time_str = "1 day"
                    else:
                        time_str = f"{int(distance_days)} days"
                    
                    quest_description = f"You must travel {time_str} to the {direction} of {settlement_name}. You will reach {original_location_description}. There, you must retrieve {target_item.lower()} for {leader_name}."
                    content_lines.append(('body', quest_description))
                else:
                    # For non-fetch quests, use the location description
                    location_description = quest.get('location_description', 'location')
                    content_lines.append(('body', location_description))
                content_lines.append(('spacer', ''))
                
                # Map preview
                content_lines.append(('map_preview', ''))  # Special marker for map preview
                content_lines.append(('spacer', ''))
                
                # Instructions
                content_lines.append(('body', 'Press D to drop this quest'))
                content_lines.append(('body', 'Press A to view archive'))
                content_lines.append(('body', 'Press ESC/ENTER/SPACE to close'))
            else:
                content_lines.append(('title', '=== JOURNAL ==='))
                content_lines.append(('spacer', ''))
                content_lines.append(('body', 'You are not bound to any quest at the moment.'))
                content_lines.append(('spacer', ''))
                content_lines.append(('body', 'Press A to view archive'))
                content_lines.append(('body', 'Press ESC/ENTER/SPACE to close'))
        else:  # archive mode
            content_lines.append(('title', '=== QUEST ARCHIVE ==='))
            content_lines.append(('spacer', ''))
            
            if quest_archive:
                # Display in reverse order (newest first)
                for i, archived_quest in enumerate(reversed(quest_archive), 1):
                    status = archived_quest.get('status', 'unknown')
                    status_color = 'Completed' if status == 'completed' else 'Dropped'
                    
                    # Get archived_at or completed_at (for backwards compatibility)
                    archived_at = archived_quest.get('archived_at') or archived_quest.get('completed_at', 'Unknown time')
                    
                    # Display quest description in same format as current quest
                    quest_type = archived_quest.get('quest_type', 'fetch')
                    if quest_type == 'fetch':
                        # Format: "You must travel {time distance} to the {direction} of {settlement}. You will reach {location}. There, you must retrieve {item} for {person}."
                        distance_days = archived_quest.get('distance_days', 0)
                        direction = archived_quest.get('quest_direction', 'unknown')
                        settlement_name = archived_quest.get('settlement_name', 'Unknown Settlement')
                        target_item = archived_quest.get('target_item', 'item')
                        leader_name = archived_quest.get('leader_name', 'Unknown Leader')
                        original_location_description = archived_quest.get('original_location_description', archived_quest.get('location_description', 'location'))
                        
                        # Format time distance
                        if distance_days < 1:
                            time_str = f"{int(distance_days * 24)} hours"
                        elif distance_days == 1:
                            time_str = "1 day"
                        else:
                            time_str = f"{int(distance_days)} days"
                        
                        quest_description = f"You must travel {time_str} to the {direction} of {settlement_name}. You will reach {original_location_description}. There, you must retrieve {target_item.lower()} for {leader_name}."
                        content_lines.append(('header', f"Quest #{i} - {status_color}"))
                        content_lines.append(('body', quest_description))
                    else:
                        # For non-fetch quests, use the location description
                        location_description = archived_quest.get('location_description', 'location')
                        content_lines.append(('header', f"Quest #{i} - {status_color}"))
                        content_lines.append(('body', location_description))
                    
                    content_lines.append(('body', f"  Archived: {archived_at}"))
                    content_lines.append(('spacer', ''))
            else:
                content_lines.append(('body', 'No archived quests.'))
                content_lines.append(('spacer', ''))
            
            content_lines.append(('body', 'Press C to view current quest'))
            content_lines.append(('body', 'Press ESC/ENTER/SPACE to close'))
        
        # Calculate line heights
        line_height = {
            'title': 40,
            'header': 30,
            'body': 26,
            'spacer': 10,
            'map_preview': 120  # Height for map preview
        }
        
        # Calculate total height (accounting for word wrapping)
        total_height = 0
        max_text_width = dialog_width - 60  # Leave margin on both sides
        for line_type, line_text in content_lines:
            if line_type == 'spacer':
                total_height += line_height['spacer']
            elif line_type == 'title':
                wrapped_lines = wrap_text(line_text, title_font, max_text_width)
                total_height += len(wrapped_lines) * line_height['title']
            elif line_type == 'header':
                wrapped_lines = wrap_text(line_text, header_font, max_text_width)
                total_height += len(wrapped_lines) * line_height['header']
            elif line_type == 'body':
                wrapped_lines = wrap_text(line_text, body_font, max_text_width)
                total_height += len(wrapped_lines) * line_height['body']
            elif line_type == 'map_preview':
                total_height += line_height['map_preview']
            else:
                total_height += line_height.get(line_type, 26)
        content_area_height = dialog_height - 100  # Space for title and close button
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_d and mode == 'current' and quest:
                    # Drop quest - show confirmation dialog
                    from confirm_dialog import show_confirm_dialog
                    import pygame as pg
                    temp_clock = pg.time.Clock()
                    
                    # Get quest giver info for warning
                    leader_name = quest.get('leader_name', 'Unknown Leader')
                    settlement_name = quest.get('settlement_name', 'Unknown Settlement')
                    warning = f"Warning: You may lose some renown with {leader_name} of {settlement_name}."
                    
                    if show_confirm_dialog(screen, temp_clock, "Drop this quest?", warning):
                        return 'drop'
                    # If cancelled, continue showing journal
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - scroll_speed)
                elif event.key == pygame.K_DOWN:
                    max_scroll = max(0, total_height - content_area_height)
                    scroll_offset = min(max_scroll, scroll_offset + scroll_speed)
                elif event.key == pygame.K_a and mode == 'current':
                    # Switch to archive
                    mode = 'archive'
                    scroll_offset = 0
                elif event.key == pygame.K_c and mode == 'archive':
                    # Switch to current
                    mode = 'current'
                    scroll_offset = 0
            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, min(total_height - content_area_height, scroll_offset - event.y * scroll_speed))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not dialog_rect.collidepoint(event.pos):
                    waiting = False
        
        # Draw dialog
        screen.fill((20, 20, 30))  # Dark background
        
        # Dialog background
        pygame.draw.rect(screen, (40, 40, 50), dialog_rect)
        pygame.draw.rect(screen, (200, 200, 200), dialog_rect, 2)
        
        # Title
        title_text = "JOURNAL" if mode == 'current' else "QUEST ARCHIVE"
        title_surface = title_font.render(title_text, True, (255, 255, 0))
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
        screen.blit(title_surface, title_rect)
        
        # Generate map preview if needed (only once per quest)
        map_preview_surface = None
        if mode == 'current' and quest:
            # Use original location description for map lookup (before item text was appended)
            location_description = quest.get('original_location_description') or quest.get('location_description')
            location_terrain_type = quest.get('location_terrain_type')
            if location_description and location_terrain_type:
                try:
                    # Generate a small preview map (20x20 tiles)
                    preview_map = generate_quest_location_map(location_description, location_terrain_type, 20)
                    # Create preview surface
                    preview_size = 120  # Size in pixels
                    tile_size = preview_size // 20  # 6 pixels per tile
                    map_preview_surface = pygame.Surface((preview_size, preview_size))
                    map_preview_surface.fill((40, 40, 50))  # Background color
                    
                    # Draw map tiles
                    for y in range(20):
                        for x in range(20):
                            terrain = preview_map[y][x]
                            color = terrain.get_color()
                            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                            pygame.draw.rect(map_preview_surface, color, rect)
                    
                    # Draw border
                    pygame.draw.rect(map_preview_surface, (200, 200, 200), 
                                   pygame.Rect(0, 0, preview_size, preview_size), 2)
                except Exception as e:
                    print(f"Error generating map preview: {e}")
        
        # Content area (scrollable)
        content_y = dialog_y + 70
        y_offset = content_y - scroll_offset
        max_text_width = dialog_width - 60  # Leave margin on both sides
        
        for line_type, line_text in content_lines:
            if line_type == 'spacer':
                if y_offset + line_height[line_type] >= dialog_y and y_offset <= dialog_y + dialog_height - 30:
                    y_offset += line_height[line_type]
                else:
                    y_offset += line_height[line_type]
                continue
            
            # Calculate how much space this line will take
            if line_type == 'title':
                wrapped_lines = wrap_text(line_text, title_font, max_text_width)
                line_pixel_height = len(wrapped_lines) * line_height['title']
            elif line_type == 'header':
                wrapped_lines = wrap_text(line_text, header_font, max_text_width)
                line_pixel_height = len(wrapped_lines) * line_height['header']
            elif line_type == 'body':
                wrapped_lines = wrap_text(line_text, body_font, max_text_width)
                line_pixel_height = len(wrapped_lines) * line_height['body']
            elif line_type == 'map_preview':
                line_pixel_height = line_height['map_preview']
                wrapped_lines = None
            else:
                wrapped_lines = None
                line_pixel_height = line_height.get(line_type, 26)
            
            # Skip if outside visible area
            if y_offset + line_pixel_height < dialog_y or y_offset > dialog_y + dialog_height - 30:
                y_offset += line_pixel_height
                continue
            
            # Render the line(s)
            if line_type == 'title':
                for wrapped_line in wrapped_lines:
                    if y_offset >= dialog_y and y_offset <= dialog_y + dialog_height - 30:
                        text_surface = title_font.render(wrapped_line, True, (255, 255, 0))
                        screen.blit(text_surface, (dialog_x + 20, y_offset))
                    y_offset += line_height['title']
            elif line_type == 'header':
                for wrapped_line in wrapped_lines:
                    if y_offset >= dialog_y and y_offset <= dialog_y + dialog_height - 30:
                        text_surface = header_font.render(wrapped_line, True, (255, 200, 100))
                        screen.blit(text_surface, (dialog_x + 20, y_offset))
                    y_offset += line_height['header']
            elif line_type == 'body':
                for wrapped_line in wrapped_lines:
                    if y_offset >= dialog_y and y_offset <= dialog_y + dialog_height - 30:
                        text_surface = body_font.render(wrapped_line, True, (200, 200, 200))
                        screen.blit(text_surface, (dialog_x + 20, y_offset))
                    y_offset += line_height['body']
            elif line_type == 'map_preview':
                # Draw map preview
                if map_preview_surface:
                    preview_x = dialog_x + 20
                    preview_y = y_offset
                    screen.blit(map_preview_surface, (preview_x, preview_y))
                y_offset += line_height['map_preview']
        
        # Scroll indicators
        if scroll_offset > 0:
            up_arrow = small_font.render("↑", True, (150, 150, 150))
            screen.blit(up_arrow, (dialog_x + dialog_width - 30, dialog_y + 70))
        if scroll_offset < total_height - content_area_height:
            down_arrow = small_font.render("↓", True, (150, 150, 150))
            screen.blit(down_arrow, (dialog_x + dialog_width - 30, dialog_y + dialog_height - 50))
        
        # Close instruction
        close_text = small_font.render("Press ESC/ENTER/SPACE or click outside to close | Arrow keys/Scroll to navigate", 
                                      True, (150, 150, 150))
        close_rect = close_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + dialog_height - 20))
        screen.blit(close_text, close_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

