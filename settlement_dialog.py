"""
Scrollable settlement dialog showing settlement info and worldbuilding data.
"""
import pygame
from typing import Optional, Dict
from settlements import Settlement, SettlementType


def show_settlement_dialog(screen: pygame.Surface, clock: pygame.time.Clock,
                          settlement: Settlement, settlements: list,
                          worldbuilding_data: Optional[Dict] = None) -> bool:
    """
    Show a scrollable dialog with settlement information and worldbuilding data.
    
    Args:
        screen: Pygame surface to draw on
        clock: Pygame clock for timing
        settlement: The settlement to display
        settlements: List of all settlements (for finding relationships)
        worldbuilding_data: Optional worldbuilding data dictionary
        
    Returns:
        True when user dismisses the dialog
    """
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
    
    # Find worldbuilding data for this settlement
    wb_data = None
    if worldbuilding_data:
        print(f"Debug dialog: Looking up worldbuilding data for {settlement.name} (type: {settlement.settlement_type.value})")
        wb_data = _find_settlement_worldbuilding_data(settlement, settlements, worldbuilding_data)
        if wb_data:
            print(f"Debug dialog: Found worldbuilding data with keys: {list(wb_data.keys())}")
        else:
            print("Debug dialog: No worldbuilding data found for this settlement")
    else:
        print("Debug dialog: No worldbuilding_data provided to dialog")
    
    # Build content lines
    content_lines = []
    
    # Settlement name
    settlement_name = settlement.name if settlement.name else "Unnamed"
    content_lines.append(("title", settlement_name))
    content_lines.append(("spacer", ""))
    
    # Settlement type
    content_lines.append(("header", f"Type: {settlement.settlement_type.value.title()}"))
    content_lines.append(("spacer", ""))
    
    # Vassal relationships
    if settlement.vassal_to:
        liege_name = settlement.vassal_to.name if settlement.vassal_to.name else "Unnamed"
        content_lines.append(("body", f"Vassal to: {liege_name}"))
    else:
        if settlement.settlement_type == SettlementType.TOWN:
            content_lines.append(("body", "Free Town (no liege)"))
    
    # Get vassals
    if settlement.settlement_type == SettlementType.CITY:
        vassal_towns = [s for s in settlements if s.vassal_to == settlement and s.settlement_type == SettlementType.TOWN]
        if vassal_towns:
            content_lines.append(("body", f"Rules {len(vassal_towns)} towns"))
    elif settlement.settlement_type == SettlementType.TOWN:
        vassal_villages = settlement.vassal_villages if hasattr(settlement, 'vassal_villages') else []
        if vassal_villages:
            content_lines.append(("body", f"Rules {len(vassal_villages)} villages"))
    elif settlement.settlement_type == SettlementType.VILLAGE:
        if hasattr(settlement, 'supplies_resource') and settlement.supplies_resource:
            content_lines.append(("body", f"Produces: {settlement.supplies_resource}"))
    
    # Resources (for towns)
    if settlement.settlement_type == SettlementType.TOWN:
        if hasattr(settlement, 'resources') and settlement.resources:
            content_lines.append(("spacer", ""))
            content_lines.append(("header", "Resources:"))
            for resource, amount in settlement.resources.items():
                content_lines.append(("body", f"  {resource}: {amount}"))
        if hasattr(settlement, 'trade_goods'):
            content_lines.append(("body", f"Trade Goods: {settlement.trade_goods}"))
    
    # Trade goods (for cities)
    if settlement.settlement_type == SettlementType.CITY:
        if hasattr(settlement, 'trade_goods'):
            content_lines.append(("body", f"Trade Goods: {settlement.trade_goods}"))
    
    # Worldbuilding data
    if wb_data:
        content_lines.append(("spacer", ""))
        content_lines.append(("header", "Description:"))
        if 'description' in wb_data:
            # Word wrap description
            desc_text = wb_data['description']
            words = desc_text.split()
            current_line = []
            current_width = 0
            max_width = dialog_width - 60  # Padding
            
            for word in words:
                word_surface = body_font.render(word + ' ', True, (200, 200, 200))
                word_width = word_surface.get_width()
                if current_width + word_width > max_width and current_line:
                    content_lines.append(("body", ' '.join(current_line)))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            if current_line:
                content_lines.append(("body", ' '.join(current_line)))
        
        if 'leader' in wb_data:
            leader = wb_data['leader']
            content_lines.append(("spacer", ""))
            content_lines.append(("header", "Leader:"))
            if 'name' in leader:
                content_lines.append(("body", f"Name: {leader['name']}"))
            if 'biography' in leader:
                content_lines.append(("spacer", ""))
                content_lines.append(("body", "Biography:"))
                # Word wrap biography
                bio_text = leader['biography']
                words = bio_text.split()
                current_line = []
                current_width = 0
                
                for word in words:
                    word_surface = body_font.render(word + ' ', True, (200, 200, 200))
                    word_width = word_surface.get_width()
                    if current_width + word_width > max_width and current_line:
                        content_lines.append(("body", ' '.join(current_line)))
                        current_line = [word]
                        current_width = word_width
                    else:
                        current_line.append(word)
                        current_width += word_width
                
                if current_line:
                    content_lines.append(("body", ' '.join(current_line)))
    
    # Calculate total content height
    line_height = {
        'title': 40,
        'header': 30,
        'body': 24,
        'spacer': 10
    }
    total_height = sum(line_height.get(line_type, 24) for line_type, _ in content_lines)
    
    # Scroll state
    scroll_offset = 0
    scroll_speed = 20
    content_area_height = dialog_height - 100  # Space for title and close button
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - scroll_speed)
                elif event.key == pygame.K_DOWN:
                    max_scroll = max(0, total_height - content_area_height)
                    scroll_offset = min(max_scroll, scroll_offset + scroll_speed)
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
        title_surface = title_font.render(settlement_name, True, (255, 255, 0))
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
        screen.blit(title_surface, title_rect)
        
        # Content area (scrollable)
        content_y = dialog_y + 70
        y_offset = content_y - scroll_offset
        
        for line_type, line_text in content_lines:
            if y_offset + line_height[line_type] < dialog_y or y_offset > dialog_y + dialog_height - 30:
                y_offset += line_height[line_type]
                continue
            
            if line_type == 'title':
                text_surface = title_font.render(line_text, True, (255, 255, 0))
            elif line_type == 'header':
                text_surface = header_font.render(line_text, True, (255, 200, 100))
            elif line_type == 'body':
                text_surface = body_font.render(line_text, True, (200, 200, 200))
            else:  # spacer
                y_offset += line_height[line_type]
                continue
            
            screen.blit(text_surface, (dialog_x + 20, y_offset))
            y_offset += line_height[line_type]
        
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
    
    return True


def _find_settlement_worldbuilding_data(settlement: Settlement, settlements: list, 
                                       worldbuilding_data: Dict) -> Optional[Dict]:
    """Find worldbuilding data for a settlement (same logic as PlayScreen)."""
    if settlement.settlement_type == SettlementType.CITY:
        cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
        try:
            city_index = cities.index(settlement) + 1
            city_key = f"City {city_index}"
            if city_key in worldbuilding_data:
                return worldbuilding_data[city_key]
        except ValueError:
            pass
    
    elif settlement.settlement_type == SettlementType.TOWN:
        if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.CITY:
            cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
            try:
                city_index = cities.index(settlement.vassal_to) + 1
                city_key = f"City {city_index}"
                if city_key in worldbuilding_data:
                    city_data = worldbuilding_data[city_key]
                    vassal_towns = [t for t in settlements 
                                 if t.settlement_type == SettlementType.TOWN and t.vassal_to == settlement.vassal_to]
                    try:
                        town_index = vassal_towns.index(settlement) + 1
                        town_key = f"Vassal Town {town_index}"
                        if town_key in city_data:
                            return city_data[town_key]
                    except ValueError:
                        pass
            except ValueError:
                pass
        else:
            free_town_key = "City NONE FOR FREE TOWN"
            if free_town_key in worldbuilding_data:
                free_town_data = worldbuilding_data[free_town_key]
                free_towns = [t for t in settlements 
                            if t.settlement_type == SettlementType.TOWN and t.vassal_to is None]
                try:
                    town_index = free_towns.index(settlement) + 1
                    town_key = f"Vassal Town {town_index}"
                    if town_key in free_town_data:
                        return free_town_data[town_key]
                except ValueError:
                    pass
    
    elif settlement.settlement_type == SettlementType.VILLAGE:
        if settlement.vassal_to and settlement.vassal_to.settlement_type == SettlementType.TOWN:
            town = settlement.vassal_to
            town_data = _find_settlement_worldbuilding_data(town, settlements, worldbuilding_data)
            if town_data:
                vassal_villages = town.vassal_villages if hasattr(town, 'vassal_villages') else []
                try:
                    village_index = vassal_villages.index(settlement) + 1
                    village_key = f"Vassal Village {village_index}"
                    if village_key in town_data:
                        return town_data[village_key]
                except (ValueError, AttributeError):
                    pass
    
    return None

