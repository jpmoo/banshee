"""
Worldbuilding system for generating settlement descriptions and leader information.
Uses a unique choice system to ensure no duplicates.
"""
import random
import sys
from typing import Dict, List, Tuple, Optional
from settlements import Settlement, SettlementType
from terrain import TerrainType

# Import data from separate files
from data_cities import (
    city_tones, city_flavors, city_titles, city_names, city_bios, city_leader_names
)
from data_towns import (
    town_tones, town_flavors, town_titles, town_bios, town_leader_names, town_names
)
from data_villages import (
    village_terrains, village_templates, village_flavor,
    village_titles, village_names, village_bios, village_leader_names
)


# ============================================================
# UNIQUE CHOICE SYSTEM
# ============================================================

def unique_choice(pool: list, label: str):
    """Pop a unique item from a pool; error if exhausted."""
    if not pool:
        sys.exit(f"❌ Ran out of unique items for {label}. Add more entries.")
    return pool.pop(random.randrange(len(pool)))


# ============================================================
# GENERATION HELPERS
# ============================================================

def make_city(tones_pool: list, flavors_pool: list, titles_pool: list,
              leader_names_pool: list, bios_pool: list, city_names_pool: list) -> Dict:
    """Generate city data using unique choices from pools."""
    return {
        "name": unique_choice(city_names_pool, 'city_names'),
        "description": f"A great city {unique_choice(tones_pool, 'city_tones')}. {unique_choice(flavors_pool, 'city_flavors')}",
        "leader": {
            "name": f"{random.choice(titles_pool)} {unique_choice(leader_names_pool, 'city_leader_names')}",
            "biography": unique_choice(bios_pool, 'city_bios')
        }
    }


def make_town(tones_pool: list, flavors_pool: list, titles_pool: list,
              leader_names_pool: list, bios_pool: list, town_names_pool: list) -> Dict:
    """Generate town data using unique choices from pools."""
    tone = unique_choice(tones_pool, 'town_tones')
    # Capitalize first letter if it starts with lowercase
    if tone and tone[0].islower():
        tone = tone[0].upper() + tone[1:]
    return {
        "name": unique_choice(town_names_pool, 'town_names'),
        "description": f"{tone}. {unique_choice(flavors_pool, 'town_flavors')}",
        "leader": {
            "name": f"{random.choice(titles_pool)} {unique_choice(leader_names_pool, 'town_leader_names')}",
            "biography": unique_choice(bios_pool, 'town_bios')
        }
    }


def make_village(terrain: str, resource: str, templates_pool: list, 
                flavor_pool: list, titles_pool: list, leader_names_pool: list,
                bios_pool: list, village_names_pool: list) -> Dict:
    """Generate village data using unique choices from pools."""
    return {
        "name": unique_choice(village_names_pool, 'village_names'),
        "description": f"{unique_choice(templates_pool, 'village_templates')} {unique_choice(flavor_pool, 'village_flavor')}",
        "leader": {
            "name": f"{random.choice(titles_pool)} {unique_choice(leader_names_pool, 'leader_name')}",
            "biography": unique_choice(bios_pool, 'village_bios')
        },
        "terrain": terrain,
        "resource": resource
    }


# ============================================================
# WORLD GENERATION
# ============================================================

def generate_worldbuilding_data(settlements: List[Settlement], seed: int = None, 
                                map_data: Optional[List[List]] = None) -> Dict:
    """
    Generate worldbuilding data for all settlements.
    
    Args:
        settlements: List of all Settlement objects
        seed: Optional random seed for reproducibility
        map_data: Optional 2D list of Terrain objects to check actual terrain types
        
    Returns:
        Dictionary in the format:
        {
            "City 1": {
                "description": "...",
                "leader": {...},
                "Vassal Town 1": {...},
                ...
            },
            "City NONE FOR FREE TOWN": {
                "Vassal Town 1": {...},
                ...
            }
        }
    """
    if seed is not None:
        random.seed(seed)
    
    # Create deep copies of all pools to avoid modifying originals
    def copy_pool(pool):
        return list(pool)
    
    # Initialize pools
    city_tones_pool = copy_pool(city_tones)
    city_flavors_pool = copy_pool(city_flavors)
    city_titles_pool = copy_pool(city_titles)
    city_leader_names_pool = copy_pool(city_leader_names)
    city_bios_pool = copy_pool(city_bios)
    city_names_pool = copy_pool(city_names)
    
    town_tones_pool = copy_pool(town_tones)
    town_flavors_pool = copy_pool(town_flavors)
    town_titles_pool = copy_pool(town_titles)
    town_bios_pool = copy_pool(town_bios)
    town_leader_names_pool = copy_pool(town_leader_names)
    town_names_pool = copy_pool(town_names)
    
    village_titles_pool = copy_pool(village_titles)
    village_bios_pool = copy_pool(village_bios)
    # Villages have their own leader names and settlement names
    village_leader_names_pool = copy_pool(village_leader_names)
    village_names_pool = copy_pool(village_names)
    
    # Village terrain-specific pools
    village_templates_pools = {
        terrain: copy_pool(templates)
        for terrain, templates in village_templates.items()
    }
    village_flavor_pools = {
        terrain: copy_pool(flavors)
        for terrain, flavors in village_flavor.items()
    }
    
    world = {}
    
    # Separate settlements by type
    cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
    towns = [s for s in settlements if s.settlement_type == SettlementType.TOWN]
    villages = [s for s in settlements if s.settlement_type == SettlementType.VILLAGE]
    
    # Generate data for cities and their vassal towns
    city_index = 1
    for city in cities:
        city_key = f"City {city_index}"
        city_data = make_city(city_tones_pool, city_flavors_pool, city_titles_pool,
                              city_leader_names_pool, city_bios_pool, city_names_pool)
        
        # Find towns that are vassals to this city
        vassal_towns = [t for t in towns if t.vassal_to == city]
        town_index = 1
        for town in vassal_towns:
            town_key = f"Vassal Town {town_index}"
            town_data = make_town(town_tones_pool, town_flavors_pool, town_titles_pool,
                                 town_leader_names_pool, town_bios_pool, town_names_pool)
            
            # Find villages that are vassals to this town
            vassal_villages = [v for v in villages if v.vassal_to == town]
            village_index = 1
            for village in vassal_villages:
                village_key = f"Vassal Village {village_index}"
                # Determine terrain type from village's resource
                terrain_map = {
                    "ore": "hills",
                    "fish and fowl": "water",
                    "grain and livestock": "grassland",
                    "lumber": "forest"
                }
                terrain = terrain_map.get(village.supplies_resource, "grassland")
                
                # Check if village is on forested hill - if so, use forest templates
                if map_data and 0 <= village.y < len(map_data) and 0 <= village.x < len(map_data[village.y]):
                    actual_terrain = map_data[village.y][village.x].terrain_type
                    if actual_terrain == TerrainType.FORESTED_HILL:
                        terrain = "forest"
                
                templates_pool = village_templates_pools[terrain]
                flavor_pool = village_flavor_pools[terrain]
                
                village_data = make_village(terrain, village.supplies_resource,
                                           templates_pool, flavor_pool,
                                           village_titles_pool, village_leader_names_pool,
                                           village_bios_pool, village_names_pool)
                town_data[village_key] = village_data
                village_index += 1
            
            city_data[town_key] = town_data
            town_index += 1
        
        world[city_key] = city_data
        city_index += 1
    
    # Generate data for free towns (towns with no liege city)
    free_towns = [t for t in towns if t.vassal_to is None]
    if free_towns:
        free_town_key = "City NONE FOR FREE TOWN"
        free_town_data = {
            "description": "A free city owing allegiance to none, ruled by charisma, coin, and stubborn will.",
            "leader": {
                "name": f"{random.choice(city_titles_pool)} {unique_choice(city_leader_names_pool, 'city_leader_names')}",
                "biography": unique_choice(city_bios_pool, 'city_bios')
            }
        }
        
        town_index = 1
        for town in free_towns:
            town_key = f"Vassal Town {town_index}"
            town_data = make_town(town_tones_pool, town_flavors_pool, town_titles_pool,
                                 town_leader_names_pool, town_bios_pool, town_names_pool)
            
            # Find villages that are vassals to this town
            vassal_villages = [v for v in villages if v.vassal_to == town]
            village_index = 1
            for village in vassal_villages:
                village_key = f"Vassal Village {village_index}"
                # Determine terrain type from village's resource
                terrain_map = {
                    "ore": "hills",
                    "fish and fowl": "water",
                    "grain and livestock": "grassland",
                    "lumber": "forest"
                }
                terrain = terrain_map.get(village.supplies_resource, "grassland")
                
                # Check if village is on forested hill - if so, use forest templates
                if map_data and 0 <= village.y < len(map_data) and 0 <= village.x < len(map_data[village.y]):
                    actual_terrain = map_data[village.y][village.x].terrain_type
                    if actual_terrain == TerrainType.FORESTED_HILL:
                        terrain = "forest"
                
                templates_pool = village_templates_pools[terrain]
                flavor_pool = village_flavor_pools[terrain]
                
                village_data = make_village(terrain, village.supplies_resource,
                                           templates_pool, flavor_pool,
                                           village_titles_pool, village_leader_names_pool,
                                           village_bios_pool, village_names_pool)
                town_data[village_key] = village_data
                village_index += 1
            
            free_town_data[town_key] = town_data
            town_index += 1
        
        world[free_town_key] = free_town_data
    
    return world


            town_index += 1
        
        world[free_town_key] = free_town_data
    
    return world

