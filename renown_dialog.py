"""
Renown dialog showing hierarchical renown information for all settlements.
"""
import pygame
from typing import Dict, List, Tuple
from settlements import Settlement, SettlementType


def show_renown_dialog(screen: pygame.Surface, clock: pygame.time.Clock,
                       settlements: List[Settlement], 
                       settlement_renown: Dict[Tuple[int, int], int]) -> None:
    """
    Show a scrollable dialog with renown information for all settlements.
    
    Args:
        screen: Pygame surface to draw on
        clock: Pygame clock for timing
        settlements: List of all settlements
        settlement_renown: Dictionary mapping (x, y) to renown value
    """
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Dialog dimensions
    dialog_width = min(800, int(screen_width * 0.9))
    dialog_height = min(700, int(screen_height * 0.9))
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    # Fonts
    title_font = pygame.font.Font(None, 36)
    header_font = pygame.font.Font(None, 28)
    body_font = pygame.font.Font(None, 22)
    small_font = pygame.font.Font(None, 20)
    
    waiting = True
    scroll_offset = 0
    scroll_speed = 20
    
    # Calculate renown totals
    def get_settlement_renown(settlement: Settlement) -> int:
        """Get renown for a settlement."""
        settlement_key = (settlement.x, settlement.y)
        return settlement_renown.get(settlement_key, 0)
    
    def get_town_total_renown(town: Settlement) -> int:
        """Get total renown for a town (including its villages)."""
        total = get_settlement_renown(town)
        for village in town.vassal_villages:
            total += get_settlement_renown(village)
        return total
    
    def get_city_total_renown(city: Settlement) -> int:
        """Get total renown for a city (including all towns and villages)."""
        total = get_settlement_renown(city)
        for town in city.vassal_towns:
            total += get_town_total_renown(town)
        return total
    
    # Calculate total renown across all settlements
    total_renown = sum(settlement_renown.values())
    
    # Organize settlements by hierarchy
    cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
    towns = [s for s in settlements if s.settlement_type == SettlementType.TOWN]
    villages = [s for s in settlements if s.settlement_type == SettlementType.VILLAGE]
    
    # Sort by name
    cities.sort(key=lambda s: s.name or "")
    towns.sort(key=lambda s: s.name or "")
    villages.sort(key=lambda s: s.name or "")
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_r:
                    waiting = False
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - scroll_speed)
                elif event.key == pygame.K_DOWN:
                    scroll_offset += scroll_speed
            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, scroll_offset - event.y * scroll_speed)
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw dialog background
        pygame.draw.rect(screen, (30, 30, 40), dialog_rect)
        pygame.draw.rect(screen, (100, 100, 100), dialog_rect, 2)
        
        # Title
        title_text = title_font.render("Renown", True, (255, 255, 255))
        screen.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        # Total renown at top
        total_text = header_font.render(f"Total Renown: {total_renown}", True, (255, 255, 0))
        screen.blit(total_text, (dialog_x + 20, dialog_y + 60))
        
        # Content area (scrollable)
        content_y = dialog_y + 100
        content_height = dialog_height - 150  # Leave space for title, total, and close text
        content_rect = pygame.Rect(dialog_x + 10, content_y, dialog_width - 20, content_height)
        
        # First, calculate total content height
        temp_y = 0
        for city in cities:
            temp_y += 35  # City header
            city_towns = [t for t in towns if t.vassal_to == city]
            for town in city_towns:
                temp_y += 28  # Town header
                town_villages = [v for v in villages if v.vassal_to == town]
                temp_y += len(town_villages) * 22  # Villages
            temp_y += 10  # Spacing
        free_towns = [t for t in towns if t.vassal_to is None]
        for town in free_towns:
            temp_y += 35  # Town header
            town_villages = [v for v in villages if v.vassal_to == town]
            temp_y += len(town_villages) * 25  # Villages
        temp_y += 10  # Spacing
        free_villages = [v for v in villages if v.vassal_to is None]
        temp_y += len(free_villages) * 25  # Free villages
        
        # Clamp scroll offset based on calculated content height
        max_scroll = max(0, temp_y - content_height)
        scroll_offset = max(0, min(scroll_offset, max_scroll))
        
        # Create a surface for the scrollable content
        content_surface = pygame.Surface((dialog_width - 20, 10000))  # Large enough for all content
        content_surface.fill((30, 30, 40))  # Match dialog background
        
        y_offset = 0  # Start at top of content surface
        max_text_width = dialog_width - 60  # Leave margin on both sides
        
        # Draw cities with their hierarchy
        for city in cities:
            city_total = get_city_total_renown(city)
            city_name = city.name or "Unnamed City"
            city_renown = get_settlement_renown(city)
            
            # City header
            city_text = header_font.render(f"{city_name} (Total: {city_total}, Own: {city_renown})", 
                                          True, (255, 215, 0))  # Gold color
            content_surface.blit(city_text, (10, y_offset))
            y_offset += 35
            
            # Towns under this city
            city_towns = [t for t in towns if t.vassal_to == city]
            city_towns.sort(key=lambda s: s.name or "")
            
            for town in city_towns:
                town_total = get_town_total_renown(town)
                town_name = town.name or "Unnamed Town"
                town_renown = get_settlement_renown(town)
                
                # Town header (indented)
                town_text = body_font.render(f"  {town_name} (Total: {town_total}, Own: {town_renown})", 
                                            True, (200, 200, 200))
                content_surface.blit(town_text, (10, y_offset))
                y_offset += 28
                
                # Villages under this town
                town_villages = [v for v in villages if v.vassal_to == town]
                town_villages.sort(key=lambda s: s.name or "")
                
                for village in town_villages:
                    village_renown = get_settlement_renown(village)
                    village_name = village.name or "Unnamed Village"
                    
                    # Village entry (more indented)
                    village_text = small_font.render(f"    {village_name}: {village_renown}", 
                                                    True, (180, 180, 180))
                    content_surface.blit(village_text, (10, y_offset))
                    y_offset += 22
            
            # Add spacing between cities
            y_offset += 10
        
        # Draw free towns (towns not vassals to any city)
        free_towns = [t for t in towns if t.vassal_to is None]
        if free_towns:
            free_towns.sort(key=lambda s: s.name or "")
            
            for town in free_towns:
                town_total = get_town_total_renown(town)
                town_name = town.name or "Unnamed Town"
                town_renown = get_settlement_renown(town)
                
                # Town header
                town_text = header_font.render(f"{town_name} (Total: {town_total}, Own: {town_renown})", 
                                              True, (200, 200, 200))
                content_surface.blit(town_text, (10, y_offset))
                y_offset += 35
                
                # Villages under this town
                town_villages = [v for v in villages if v.vassal_to == town]
                town_villages.sort(key=lambda s: s.name or "")
                
                for village in town_villages:
                    village_renown = get_settlement_renown(village)
                    village_name = village.name or "Unnamed Village"
                    
                    # Village entry (indented)
                    village_text = body_font.render(f"  {village_name}: {village_renown}", 
                                                   True, (180, 180, 180))
                    content_surface.blit(village_text, (10, y_offset))
                    y_offset += 25
            
            # Add spacing
            y_offset += 10
        
        # Draw free villages (villages not vassals to any town)
        free_villages = [v for v in villages if v.vassal_to is None]
        if free_villages:
            free_villages.sort(key=lambda s: s.name or "")
            
            for village in free_villages:
                village_renown = get_settlement_renown(village)
                village_name = village.name or "Unnamed Village"
                
                # Village entry
                village_text = body_font.render(f"{village_name}: {village_renown}", 
                                               True, (180, 180, 180))
                content_surface.blit(village_text, (10, y_offset))
                y_offset += 25
        
        # Blit the scrollable content surface to screen with clipping
        screen.set_clip(content_rect)
        screen.blit(content_surface, (content_rect.x, content_rect.y - scroll_offset))
        screen.set_clip(None)
        
        # Draw close instruction
        close_text = small_font.render("Press R or ESC to close", True, (150, 150, 150))
        screen.blit(close_text, (dialog_x + 20, dialog_y + dialog_height - 30))
        
        pygame.display.flip()
        clock.tick(60)

