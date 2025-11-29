"""
Generate quest location maps with structure detection.
Structures (ruins, buildings, standing stones, etc.) are rendered using mountain terrain.
"""
import json
import random
import re
from typing import List, Tuple
from data_quest_locations import quest_location_descriptions
from terrain import Terrain, TerrainType

# Standard quest location map size
MAP_SIZE = 50

# Keywords that indicate structures (case-insensitive)
STRUCTURE_KEYWORDS = [
    'tower', 'fort', 'keep', 'castle', 'ruin', 'ruins', 'chapel', 'abbey', 'monastery',
    'shrine', 'temple', 'altar', 'cairn', 'stone', 'stones', 'menhir', 'dolmen',
    'circle', 'ring', 'mound', 'barrow', 'tomb', 'grave', 'crypt', 'hall', 'lodge',
    'hut', 'huts', 'house', 'farmhouse', 'granary', 'mill', 'windmill', 'watermill',
    'bridge', 'pier', 'jetty', 'causeway', 'arch', 'archway', 'gate', 'statue',
    'obelisk', 'column', 'throne', 'stair', 'stairs', 'step', 'steps', 'wall',
    'rampart', 'battlements', 'watchtower', 'lighthouse', 'hermitage', 'cell',
    'scriptorium', 'observatory', 'school', 'waystation', 'inn', 'market', 'square',
    'village', 'town', 'settlement', 'foundation', 'foundations', 'post', 'posts',
    'cross', 'crossroad', 'crossroads', 'causeway', 'stairway', 'pathway', 'road',
    'ship', 'wreck', 'wreckage', 'shipwreck', 'mast', 'masts', 'beacon', 'beacons',
    'idol', 'idols', 'carving', 'carvings', 'face', 'faces', 'finger', 'pointing',
    'door', 'doors', 'gate', 'gates', 'entrance', 'entrances', 'opening', 'mouth',
    'well', 'pool', 'pond', 'spring', 'cave', 'cavern', 'grotto', 'hollow', 'glade',
    'clearing', 'amphitheater', 'theater', 'arena', 'pit', 'quarry', 'mine', 'mines'
]

def detect_water_features(description: str) -> List[Tuple[int, int, str]]:
    """
    Detect water features in description and return positions and types.
    
    Returns:
        List of (x, y, feature_type) tuples where feature_type is 'shallow_water'
    """
    description_lower = description.lower()
    water_keywords = [
        'water', 'pool', 'pond', 'spring', 'well', 'stream', 'brook', 'creek',
        'river', 'lake', 'sea', 'ocean', 'bay', 'cove', 'inlet', 'lagoon',
        'marsh', 'swamp', 'bog', 'fen', 'wetland', 'tide', 'tidal', 'surf',
        'wave', 'waves', 'shore', 'beach', 'coast', 'coastal', 'harbor',
        'harbour', 'wharf', 'pier', 'jetty', 'docks', 'dock'
    ]
    
    has_water = any(keyword in description_lower for keyword in water_keywords)
    if not has_water:
        return []
    
    # Return a list indicating water should be placed (we'll place it in the map generation)
    return [('water', 'shallow_water')]  # Signal that water should be placed


def detect_vegetation_features(description: str) -> List[Tuple[int, int, str]]:
    """
    Detect vegetation/forest features in description.
    
    Returns:
        List indicating forest should be placed
    """
    description_lower = description.lower()
    vegetation_keywords = [
        'tree', 'trees', 'forest', 'wood', 'woods', 'grove', 'glade', 'glen',
        'copse', 'thicket', 'brake', 'brush', 'vegetation', 'foliage', 'canopy',
        'undergrowth', 'moss', 'mossy', 'fern', 'ferns', 'ivy', 'vine', 'vines',
        'bracken', 'bramble', 'brambles', 'shrub', 'shrubs', 'bush', 'bushes',
        'oak', 'pine', 'birch', 'ash', 'yew', 'elm', 'willow', 'chestnut',
        'redwood', 'elder', 'blackthorn', 'thorn', 'thorns'
    ]
    
    has_vegetation = any(keyword in description_lower for keyword in vegetation_keywords)
    if not has_vegetation:
        return []
    
    # Return a list indicating forest should be placed
    return [('vegetation', 'forest')]  # Signal that forest should be placed


def detect_additional_features(description: str) -> List[Tuple[str, str]]:
    """
    Detect additional physical features and objects that can be rendered.
    
    Returns:
        List of (feature, feature_type) tuples
    """
    description_lower = description.lower()
    features = []
    
    # Physical structures/places
    if re.search(r'\bamphitheater\b', description_lower):
        features.append(('amphitheater', 'circular_structure'))
    if re.search(r'\baqueduct\b', description_lower):
        features.append(('aqueduct', 'linear_structure'))
    if re.search(r'\bbakery\b', description_lower):
        features.append(('bakery', 'rectangular'))
    if re.search(r'\bcathedral\b', description_lower):
        features.append(('cathedral', 'large_rectangular'))
    if re.search(r'\bcave\b', description_lower) or re.search(r'\bcavern\b', description_lower) or \
       re.search(r'\bgrotto\b', description_lower) or re.search(r'\bhollowed\b', description_lower) or \
       re.search(r'\bhollow\b', description_lower):
        features.append(('cave', 'cave_entrance'))
    if re.search(r'\bchasm\b', description_lower):
        features.append(('chasm', 'linear_gap'))
    if re.search(r'\bcliff\b', description_lower) or re.search(r'\bcliffside\b', description_lower):
        features.append(('cliff', 'elevated_edge'))
    if re.search(r'\bcloister\b', description_lower):
        features.append(('cloister', 'rectangular'))
    if re.search(r'\bditch\b', description_lower):
        features.append(('ditch', 'linear_depression'))
    if re.search(r'\bdunes\b', description_lower):
        features.append(('dunes', 'hill_features'))
    if re.search(r'\bfield\b', description_lower):
        features.append(('field', 'open_area'))
    if re.search(r'\bfarmstead\b', description_lower):
        features.append(('farmstead', 'building_group'))
    if re.search(r'\bforge\b', description_lower):
        features.append(('forge', 'rectangular'))
    if re.search(r'\borchard\b', description_lower):
        features.append(('orchard', 'tree_area'))
    if re.search(r'\bpit\b', description_lower):
        features.append(('pit', 'depression'))
    if re.search(r'\bquarry\b', description_lower):
        features.append(('quarry', 'excavation'))
    if re.search(r'\bvale\b', description_lower) or re.search(r'\bvalley\b', description_lower):
        features.append(('vale', 'depression_area'))
    
    # Objects/items that can be rendered
    if re.search(r'\bantlers\b', description_lower) or re.search(r'\bbones\b', description_lower) or re.search(r'\bskulls\b', description_lower):
        features.append(('remains', 'decorative_items'))
    if re.search(r'\bbanners\b', description_lower):
        features.append(('banners', 'decorative_items'))
    if re.search(r'\bbarley\b', description_lower) or re.search(r'\boats\b', description_lower) or re.search(r'\bwheat\b', description_lower):
        features.append(('crops', 'crop_area'))
    if re.search(r'\bcandles\b', description_lower) or re.search(r'\blanterns\b', description_lower) or re.search(r'\btorch\b', description_lower):
        features.append(('lights', 'light_sources'))
    if re.search(r'\bcarcass\b', description_lower) or re.search(r'\bcorpses\b', description_lower):
        features.append(('remains', 'remains_feature'))
    if re.search(r'\bchains\b', description_lower) or re.search(r'\brope\b', description_lower):
        features.append(('chains', 'structural_items'))
    if re.search(r'\bcoral\b', description_lower):
        features.append(('coral', 'underwater_feature'))
    if re.search(r'\bdragon\b', description_lower):
        features.append(('dragon', 'large_creature'))
    if re.search(r'\bpearls\b', description_lower):
        features.append(('pearls', 'treasure_items'))
    if re.search(r'\brunes\b', description_lower):
        features.append(('runes', 'carved_markings'))
    if re.search(r'\bshells\b', description_lower):
        features.append(('shells', 'decorative_items'))
    if re.search(r'\bshards\b', description_lower):
        features.append(('shards', 'debris'))
    if re.search(r'\bslab\b', description_lower):
        features.append(('slab', 'stone_feature'))
    if re.search(r'\bspearheads\b', description_lower):
        features.append(('spearheads', 'weapon_items'))
    if re.search(r'\bstump\b', description_lower):
        features.append(('stump', 'tree_remnant'))
    if re.search(r'\btreasure\b', description_lower):
        features.append(('treasure', 'treasure_items'))
    if re.search(r'\btunnels\b', description_lower):
        features.append(('tunnels', 'underground_passage'))
    if re.search(r'\bwildflowers\b', description_lower):
        features.append(('wildflowers', 'vegetation'))
    
    return features


def detect_structures(description: str) -> List[Tuple[str, str]]:
    """
    Detect structure-related keywords in a description.
    
    Returns:
        List of (keyword, structure_type) tuples where structure_type is:
        - 'stone_circle' for stone circles (individual separate stones)
        - 'standing_stones' for individual standing stones
        - 'boulders' for natural boulders/rocks (use hill tiles)
        - 'circle' for circular structures (non-stone rings)
        - 'rectangular' for buildings (towers, halls, etc.)
        - 'linear' for paths, walls, bridges
        - 'point' for single objects (statues, etc.)
        - 'mound' for mounds, barrows, tombs
    """
    description_lower = description.lower()
    structures = []
    
    # Standing stones (individual separate stones)
    if re.search(r'\bstanding\s+stone', description_lower):
        structures.append(('standing_stone', 'standing_stones'))
    
    # Stone circles (individual stones in a circle)
    if re.search(r'\bstone\s+circle\b', description_lower) or re.search(r'\bring\s+of\s+stones?\b', description_lower):
        structures.append(('stone_circle', 'stone_circle'))
    
    # Boulders and natural rocks (use hill tiles)
    if re.search(r'\bboulder', description_lower) or re.search(r'\brocks?\b', description_lower) or \
       re.search(r'\bfield\s+of\s+boulders\b', description_lower) or \
       re.search(r'\bpetrified\b', description_lower):
        structures.append(('boulders', 'boulders'))
    
    # Other circular structures (non-stone)
    circle_patterns = [
        r'\bringfort\b', r'\bring\s+of\s+wooden\s+posts\b', r'\bring\s+of\s+mushrooms\b'
    ]
    for pattern in circle_patterns:
        if re.search(pattern, description_lower):
            structures.append(('circle', 'circle'))
            break
    
    # Rectangular structures
    rectangular_patterns = [
        r'\btower\b', r'\bfort\b', r'\bkeep\b', r'\bcastle\b', r'\bhall\b',
        r'\blodge\b', r'\bhut\b', r'\bhouse\b', r'\bfarmhouse\b', r'\bchapel\b',
        r'\babbey\b', r'\bmonastery\b', r'\btemple\b', r'\bhermitage\b',
        r'\bcell\b', r'\bscriptorium\b', r'\bobservatory\b', r'\bwaystation\b',
        r'\binn\b', r'\bgranary\b', r'\bwindmill\b', r'\bwatermill\b',
        r'\blighthouse\b', r'\bwatchtower\b', r'\broundhouse\b'
    ]
    for pattern in rectangular_patterns:
        if re.search(pattern, description_lower):
            structures.append(('rectangular', 'rectangular'))
            break
    
    # Linear structures
    linear_patterns = [
        r'\bbridge\b', r'\bpier\b', r'\bjetty\b', r'\bcauseway\b', r'\bwall\b',
        r'\brampart\b', r'\bpath\b', r'\broad\b', r'\bstair\b', r'\bsteps\b',
        r'\barch\b', r'\barchway\b', r'\bgate\b', r'\bchain\b', r'\bchains\b'
    ]
    for pattern in linear_patterns:
        if re.search(pattern, description_lower):
            structures.append(('linear', 'linear'))
            break
    
    # Point structures (non-stone)
    point_patterns = [
        r'\bmenhir\b', r'\bstatue\b', r'\bcross\b',
        r'\bthrone\b', r'\bobelisk\b', r'\bcolumn\b', r'\bfinger\b', r'\bpointing\b',
        r'\bidol\b', r'\bcarving\b', r'\bface\b', r'\bfaces\b', r'\bmarker\b',
        r'\bmarkers\b', r'\bmilestone\b', r'\bmilestones\b', r'\bpost\b', r'\bposts\b'
    ]
    for pattern in point_patterns:
        if re.search(pattern, description_lower):
            structures.append(('point', 'point'))
            break
    
    # Mound structures
    mound_patterns = [
        r'\bmound\b', r'\bbarrow\b', r'\btomb\b', r'\bgrave\b', r'\bcrypt\b',
        r'\bburial\s+mound\b', r'\bgrassy\s+mound\b', r'\bhill\s+altar\b'
    ]
    for pattern in mound_patterns:
        if re.search(pattern, description_lower):
            structures.append(('mound', 'mound'))
            break
    
    # Cairn (can be point or mound)
    if re.search(r'\bcairn\b', description_lower):
        structures.append(('cairn', 'mound'))
    
    # Dolmen (rectangular-like)
    if re.search(r'\bdolmen\b', description_lower):
        structures.append(('dolmen', 'rectangular'))
    
    return structures


def generate_map_with_structures(description: str, location_terrain_type: str, size: int) -> List[List[Terrain]]:
    """
    Generate a quest location map with structures rendered as mountain terrain.
    
    Args:
        description: The location description
        location_terrain_type: Base terrain type
        size: Map size (size x size)
        
    Returns:
        A list of lists of Terrain objects
    """
    # Use a fixed seed based on description for consistency
    random.seed(hash(description) % (2**32))
    
    # Map location terrain type to TerrainType
    terrain_map = {
        "hill": TerrainType.HILLS,
        "forested_hill": TerrainType.FORESTED_HILL,
        "forest": TerrainType.FOREST,
        "grassland": TerrainType.GRASSLAND,
        "waterside": TerrainType.GRASSLAND
    }
    base_terrain = terrain_map.get(location_terrain_type, TerrainType.GRASSLAND)
    
    # Calculate center for feature placement
    center_x, center_y = size // 2, size // 2
    
    # Check if description mentions boulders or rocky formations that should be rendered as hills
    # But exclude standing stones, stone circles, and monuments (those are structures, not natural boulders)
    description_lower = description.lower()
    
    # Check for monuments/structures that use stone (these should NOT trigger scattered hills)
    # Use regex patterns to be more precise
    import re
    monument_patterns = [
        r'\bstanding[\s-]?stone', r'\bstanding[\s-]?stones',
        r'\bstone[\s-]?circle', r'\bstone[\s-]?circles',
        r'\bring\s+of\s+stones?\b', r'\bcircle\s+of\s+stones?\b',
        r'\bstone\s+ring', r'\bstone\s+rings',
        r'\bmenhir', r'\bdolmen', r'\bcairn', r'\bcairns',
        r'\bmonument', r'\bmegalith', r'\bhenge',
        r'\bmound\b', r'\bbarrow\b', r'\btomb\b', r'\bgrave\b', r'\bcrypt\b',
        r'\bburial\s+mound', r'\bgrassy\s+mound'
    ]
    has_monuments = any(re.search(pattern, description_lower) for pattern in monument_patterns)
    
    # Check for natural boulders/rocks (only if no monuments)
    # These are natural features, not structures
    has_boulders = False
    if not has_monuments:
        # Natural boulder/rock keywords
        natural_boulder_keywords = [
            'boulder', 'boulders', 'field of boulders', 'petrified',
            'rocky', 'rock-strewn', 'stony', 'stone-strewn', 'rock field',
            'boulder field', 'scattered boulders', 'loose rocks'
        ]
        has_boulders = any(keyword in description_lower for keyword in natural_boulder_keywords)
        
        # Also check for generic "rocks" or "stones" but only if clearly natural
        # (not part of a structure name like "standing stones" or "stone circle")
        if not has_boulders and ('rocks' in description_lower or 'stones' in description_lower):
            # Only count as boulders if it's clearly natural context
            # Check if it's NOT part of a monument phrase
            if not re.search(r'\b(standing|circle|ring|monument|megalith|henge|mound|barrow|tomb|grave|crypt|burial|grassy)\s+(stone|stones|rock|rocks)', description_lower):
                # Check for natural context words
                natural_context = ['scattered', 'loose', 'field', 'strewn', 'littered', 'natural']
                if any(context in description_lower for context in natural_context):
                    has_boulders = True
    
    # Create base map
    map_data = []
    for y in range(size):
        row = []
        for x in range(size):
            # Outer edges (entire border) match location terrain
            if x == 0 or x == size - 1 or y == 0 or y == size - 1:
                row.append(Terrain(base_terrain))
            else:
                # Interior is grassland by default
                # Only add scattered base terrain (hills) if description mentions natural boulders/rocks
                # (not monuments/structures)
                if base_terrain == TerrainType.HILLS and has_boulders and not has_monuments:
                    # Add some scattered hill patches for natural boulder/rock descriptions
                    if random.random() < 0.10:  # 10% chance for hills in interior when natural boulders mentioned
                        row.append(Terrain(base_terrain))
                    else:
                        row.append(Terrain(TerrainType.GRASSLAND))
                else:
                    row.append(Terrain(TerrainType.GRASSLAND))
        map_data.append(row)
    
    # Detect water features
    water_features = detect_water_features(description)
    
    # Detect vegetation/forest features
    vegetation_features = detect_vegetation_features(description)
    
    # Place water features (shallow water, passable)
    # For waterside maps, add more water features
    if location_terrain_type == 'waterside':
        # Add extensive water coverage for waterside maps
        # Create water along edges and in multiple areas
        water_coverage = 0.3  # 30% of map should be water
        num_water_areas = random.randint(3, 6)
        for _ in range(num_water_areas):
            water_x = random.randint(1, size - 2)
            water_y = random.randint(1, size - 2)
            water_radius = random.randint(3, min(8, size // 6))
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - water_x) ** 2 + (y - water_y) ** 2) ** 0.5
                    if dist < water_radius:
                        map_data[y][x] = Terrain(TerrainType.SHALLOW_WATER)
        # Also add water along some edges
        edge_water_length = size // 3
        if random.random() < 0.5:
            # Water along top or bottom edge
            edge_y = random.choice([1, size - 2])
            for x in range(max(2, center_x - edge_water_length // 2), min(size - 2, center_x + edge_water_length // 2)):
                if 1 <= edge_y < size - 1:
                    map_data[edge_y][x] = Terrain(TerrainType.SHALLOW_WATER)
                    if 1 <= edge_y + 1 < size - 1:
                        map_data[edge_y + 1][x] = Terrain(TerrainType.SHALLOW_WATER)
        else:
            # Water along left or right edge
            edge_x = random.choice([1, size - 2])
            for y in range(max(2, center_y - edge_water_length // 2), min(size - 2, center_y + edge_water_length // 2)):
                if 1 <= edge_x < size - 1:
                    map_data[y][edge_x] = Terrain(TerrainType.SHALLOW_WATER)
                    if 1 <= edge_x + 1 < size - 1:
                        map_data[y][edge_x + 1] = Terrain(TerrainType.SHALLOW_WATER)
    
    if water_features:
        # Place water in appropriate locations (pools, streams, etc.)
        desc_lower = description.lower()
        if 'pool' in desc_lower or 'pond' in desc_lower:
            # Circular pool/pond
            pool_radius = min(4, size // 10)
            pool_x = center_x + random.randint(-size // 6, size // 6)
            pool_y = center_y + random.randint(-size // 6, size // 6)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - pool_x) ** 2 + (y - pool_y) ** 2) ** 0.5
                    if dist < pool_radius:
                        map_data[y][x] = Terrain(TerrainType.SHALLOW_WATER)
        elif 'stream' in desc_lower or 'brook' in desc_lower or 'creek' in desc_lower:
            # Linear stream
            if random.random() < 0.5:
                # Horizontal stream
                stream_y = center_y + random.randint(-size // 8, size // 8)
                for x in range(max(2, center_x - size // 4), min(size - 2, center_x + size // 4)):
                    if 1 <= stream_y < size - 1:
                        map_data[stream_y][x] = Terrain(TerrainType.SHALLOW_WATER)
                        # Add width
                        if 1 <= stream_y + 1 < size - 1:
                            map_data[stream_y + 1][x] = Terrain(TerrainType.SHALLOW_WATER)
            else:
                # Vertical stream
                stream_x = center_x + random.randint(-size // 8, size // 8)
                for y in range(max(2, center_y - size // 4), min(size - 2, center_y + size // 4)):
                    if 1 <= stream_x < size - 1:
                        map_data[y][stream_x] = Terrain(TerrainType.SHALLOW_WATER)
                        # Add width
                        if 1 <= stream_x + 1 < size - 1:
                            map_data[y][stream_x + 1] = Terrain(TerrainType.SHALLOW_WATER)
        elif 'spring' in desc_lower or 'well' in desc_lower:
            # Small spring/well
            spring_x = center_x + random.randint(-size // 8, size // 8)
            spring_y = center_y + random.randint(-size // 8, size // 8)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = spring_x + dx, spring_y + dy
                    if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                        map_data[ny][nx] = Terrain(TerrainType.SHALLOW_WATER)
        else:
            # General water feature - place a small area
            water_x = center_x + random.randint(-size // 6, size // 6)
            water_y = center_y + random.randint(-size // 6, size // 6)
            water_radius = min(3, size // 12)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - water_x) ** 2 + (y - water_y) ** 2) ** 0.5
                    if dist < water_radius:
                        map_data[y][x] = Terrain(TerrainType.SHALLOW_WATER)
    
    # Place vegetation/forest features
    if vegetation_features:
        desc_lower = description.lower()
        if 'glade' in desc_lower or 'clearing' in desc_lower:
            # Glade/clearing - open area surrounded by forest
            glade_radius = min(6, size // 8)
            # Forest around the glade
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if glade_radius < dist < glade_radius + 3:
                        map_data[y][x] = Terrain(TerrainType.FOREST)
        elif 'grove' in desc_lower or 'copse' in desc_lower:
            # Small grove/copse
            grove_radius = min(5, size // 10)
            grove_x = center_x + random.randint(-size // 8, size // 8)
            grove_y = center_y + random.randint(-size // 8, size // 8)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - grove_x) ** 2 + (y - grove_y) ** 2) ** 0.5
                    if dist < grove_radius:
                        map_data[y][x] = Terrain(TerrainType.FOREST)
        elif 'glen' in desc_lower:
            # Glen - valley with forest
            # Forest on sides
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    # Forest on left and right edges of center area
                    if abs(x - center_x) > size // 6:
                        if random.random() < 0.6:
                            map_data[y][x] = Terrain(TerrainType.FOREST)
        else:
            # General forest/vegetation - scattered trees or forest patches
            num_patches = random.randint(3, 8)
            for _ in range(num_patches):
                patch_x = random.randint(2, size - 3)
                patch_y = random.randint(2, size - 3)
                patch_size = random.randint(2, 4)
                for dy in range(-patch_size, patch_size + 1):
                    for dx in range(-patch_size, patch_size + 1):
                        nx, ny = patch_x + dx, patch_y + dy
                        if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                            if random.random() < 0.7:
                                map_data[ny][nx] = Terrain(TerrainType.FOREST)
    
    # Detect structures
    structures = detect_structures(description)
    
    # Detect additional features
    additional_features = detect_additional_features(description)
    
    # If no structures or features, continue to edge generation
    # (edge generation happens after structure placement)
    
    center_x, center_y = size // 2, size // 2
    
    # Place structures (use first detected structure type if any)
    if structures:
        structure_type = structures[0][1]
        
        if structure_type == 'stone_circle':
            # Draw individual standing stones arranged in a circle (separate mountain tiles)
            import math
            radius = min(8, size // 6)
            num_stones = random.randint(6, 12)  # Number of stones in the circle
            
            for i in range(num_stones):
                angle = (2 * math.pi * i) / num_stones
                base_radius = radius * 0.85
                variation = base_radius * 0.15  # 15% variation for natural look
                actual_radius = base_radius + (random.random() - 0.5) * variation
                
                # Use trigonometry to place stones in a circle
                stone_x = int(center_x + actual_radius * math.cos(angle))
                stone_y = int(center_y + actual_radius * math.sin(angle))
                
                # Place stone at calculated position (separate individual stones)
                if 1 <= stone_x < size - 1 and 1 <= stone_y < size - 1:
                    map_data[stone_y][stone_x] = Terrain(TerrainType.MOUNTAIN)
        
        elif structure_type == 'standing_stones':
            # Draw individual separate standing stones (mountain tiles)
            desc_lower = description.lower()
            if 'pair' in desc_lower or 'two' in desc_lower:
                # Two standing stones (never on edges)
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x + 4 < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x + 4] = Terrain(TerrainType.MOUNTAIN)
            elif 'three' in desc_lower or 'sisters' in desc_lower:
                # Three standing stones (triangle, never on edges)
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x < size - 1 and 1 <= center_y - 3 < size - 1:
                    map_data[center_y - 3][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x + 3 < size - 1 and 1 <= center_y + 2 < size - 1:
                    map_data[center_y + 2][center_x + 3] = Terrain(TerrainType.MOUNTAIN)
            else:
                # Single standing stone or small cluster (never on edges)
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                # Sometimes add 1-2 nearby stones
                if random.random() < 0.3:
                    for _ in range(random.randint(1, 2)):
                        offset_x = center_x + random.randint(-2, 2)
                        offset_y = center_y + random.randint(-2, 2)
                        if 1 <= offset_x < size - 1 and 1 <= offset_y < size - 1:
                            map_data[offset_y][offset_x] = Terrain(TerrainType.MOUNTAIN)
        
        elif structure_type == 'boulders':
            # Draw boulders/natural rocks using hill tiles (randomly arranged)
            desc_lower = description.lower()
            num_boulders = random.randint(8, 20)  # Number of boulders
            
            for _ in range(num_boulders):
                # Random position within the map (avoid edges)
                boulder_x = random.randint(2, size - 3)
                boulder_y = random.randint(2, size - 3)
                map_data[boulder_y][boulder_x] = Terrain(TerrainType.HILLS)
                # Sometimes add a small cluster (2-3 tiles)
                if random.random() < 0.3:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = boulder_x + dx, boulder_y + dy
                            if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                                if random.random() < 0.4:
                                    map_data[ny][nx] = Terrain(TerrainType.HILLS)
        
        elif structure_type == 'circle':
            # Draw a circle/ring of mountain tiles (non-stone)
            radius = min(8, size // 6)
            # Check if description suggests a filled circle or ring
            desc_lower = description.lower()
            is_ring = 'ring' in desc_lower or 'circle' in desc_lower
            
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if is_ring:
                        # Ring (circle outline only)
                        if abs(dist - radius) < 1.2:
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                    else:
                        # Filled circle
                        if dist < radius:
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
        
        elif structure_type == 'rectangular':
            # Draw a building with various shapes (rectangular, L-shaped, circular, etc.)
            import math
            shape_type = random.choice(['rectangle', 'square', 'L_shape', 'circular', 'octagonal'])
            
            if shape_type == 'rectangle' or shape_type == 'square':
                # Standard rectangular building
                width = min(12, size // 4) if shape_type == 'rectangle' else min(10, size // 5)
                height = min(10, size // 5) if shape_type == 'rectangle' else width
                start_x = max(1, center_x - width // 2)
                start_y = max(1, center_y - height // 2)
                end_x = min(size - 1, start_x + width)
                end_y = min(size - 1, start_y + height)
                
                # Fill interior
                inner_start_x = start_x + 1
                inner_start_y = start_y + 1
                inner_end_x = end_x - 1
                inner_end_y = end_y - 1
                
                if inner_end_x > inner_start_x and inner_end_y > inner_start_y:
                    for y in range(inner_start_y, inner_end_y):
                        for x in range(inner_start_x, inner_end_x):
                            if 1 <= x < size - 1 and 1 <= y < size - 1:
                                map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                
                # Choose entrance wall
                entrance_wall = random.choice(['bottom', 'top', 'left', 'right'])
                entrance_x = start_x + width // 2
                entrance_y = start_y + height // 2
                
                if entrance_wall == 'bottom':
                    entrance_x = start_x + width // 2
                    entrance_y = end_y - 1
                elif entrance_wall == 'top':
                    entrance_x = start_x + width // 2
                    entrance_y = start_y
                elif entrance_wall == 'left':
                    entrance_x = start_x
                    entrance_y = start_y + height // 2
                elif entrance_wall == 'right':
                    entrance_x = end_x - 1
                    entrance_y = start_y + height // 2
                
                # Draw walls, skipping entrance
                for x in range(start_x, end_x):
                    if 1 <= x < size - 1:
                        if not (entrance_wall == 'top' and x == entrance_x) and 1 <= start_y < size - 1:
                            map_data[start_y][x] = Terrain(TerrainType.MOUNTAIN)
                        if not (entrance_wall == 'bottom' and x == entrance_x) and 1 <= end_y - 1 < size - 1:
                            map_data[end_y - 1][x] = Terrain(TerrainType.MOUNTAIN)
                
                for y in range(start_y, end_y):
                    if 1 <= y < size - 1:
                        if not (entrance_wall == 'left' and y == entrance_y) and 1 <= start_x < size - 1:
                            map_data[y][start_x] = Terrain(TerrainType.MOUNTAIN)
                        if not (entrance_wall == 'right' and y == entrance_y) and 1 <= end_x - 1 < size - 1:
                            map_data[y][end_x - 1] = Terrain(TerrainType.MOUNTAIN)
                
                if entrance_x is not None and entrance_y is not None:
                    if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                        map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
            
            elif shape_type == 'L_shape':
                # L-shaped building
                width1 = min(10, size // 5)
                height1 = min(8, size // 6)
                width2 = min(8, size // 6)
                height2 = min(10, size // 5)
                
                start_x = max(1, center_x - width1 // 2)
                start_y = max(1, center_y - height1 // 2)
                end_x1 = min(size - 1, start_x + width1)
                end_y1 = min(size - 1, start_y + height1)
                
                # Second part of L
                start_x2 = end_x1 - 2
                start_y2 = end_y1 - 2
                end_x2 = min(size - 1, start_x2 + width2)
                end_y2 = min(size - 1, start_y2 + height2)
                
                # Fill interiors
                for y in range(start_y + 1, end_y1 - 1):
                    for x in range(start_x + 1, end_x1 - 1):
                        if 1 <= x < size - 1 and 1 <= y < size - 1:
                            map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                for y in range(start_y2 + 1, end_y2 - 1):
                    for x in range(start_x2 + 1, end_x2 - 1):
                        if 1 <= x < size - 1 and 1 <= y < size - 1:
                            map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                
                # Draw L-shaped walls with entrance
                entrance_wall = random.choice(['bottom', 'top', 'left', 'right'])
                entrance_x = start_x + width1 // 2
                entrance_y = start_y + height1 // 2
                
                # Draw first rectangle walls
                for x in range(start_x, end_x1):
                    if 1 <= x < size - 1:
                        if not (entrance_wall == 'top' and x == entrance_x) and 1 <= start_y < size - 1:
                            map_data[start_y][x] = Terrain(TerrainType.MOUNTAIN)
                        if 1 <= end_y1 - 1 < size - 1:
                            map_data[end_y1 - 1][x] = Terrain(TerrainType.MOUNTAIN)
                for y in range(start_y, end_y1):
                    if 1 <= y < size - 1:
                        if not (entrance_wall == 'left' and y == entrance_y) and 1 <= start_x < size - 1:
                            map_data[y][start_x] = Terrain(TerrainType.MOUNTAIN)
                        if 1 <= end_x1 - 1 < size - 1:
                            map_data[y][end_x1 - 1] = Terrain(TerrainType.MOUNTAIN)
                
                # Draw second rectangle walls
                for x in range(start_x2, end_x2):
                    if 1 <= x < size - 1 and 1 <= start_y2 < size - 1:
                        map_data[start_y2][x] = Terrain(TerrainType.MOUNTAIN)
                    if 1 <= end_y2 - 1 < size - 1:
                        map_data[end_y2 - 1][x] = Terrain(TerrainType.MOUNTAIN)
                for y in range(start_y2, end_y2):
                    if 1 <= y < size - 1:
                        if 1 <= start_x2 < size - 1:
                            map_data[y][start_x2] = Terrain(TerrainType.MOUNTAIN)
                        if 1 <= end_x2 - 1 < size - 1:
                            map_data[y][end_x2 - 1] = Terrain(TerrainType.MOUNTAIN)
                
                if entrance_x is not None and entrance_y is not None:
                    if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                        map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
            
            elif shape_type == 'circular':
                # Circular building
                radius = min(8, size // 6)
                # Fill interior
                for y in range(1, size - 1):
                    for x in range(1, size - 1):
                        dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                        if dist < radius - 1:
                            map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                
                # Draw circular wall with entrance
                entrance_angle = random.random() * 2 * math.pi
                entrance_x = int(center_x + (radius - 0.5) * math.cos(entrance_angle))
                entrance_y = int(center_y + (radius - 0.5) * math.sin(entrance_angle))
                
                for y in range(1, size - 1):
                    for x in range(1, size - 1):
                        dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                        # Draw wall (ring)
                        if abs(dist - radius) < 0.8:
                            # Skip entrance position
                            if abs(x - entrance_x) <= 1 and abs(y - entrance_y) <= 1:
                                continue
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                
                if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                    map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
            
            elif shape_type == 'octagonal':
                # Octagonal building
                radius = min(7, size // 7)
                # Fill interior
                for y in range(1, size - 1):
                    for x in range(1, size - 1):
                        dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                        if dist < radius - 1:
                            map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                
                # Draw octagonal wall
                entrance_side = random.randint(0, 7)
                for i in range(8):
                    angle = (2 * math.pi * i) / 8
                    px = int(center_x + radius * math.cos(angle))
                    py = int(center_y + radius * math.sin(angle))
                    if 1 <= px < size - 1 and 1 <= py < size - 1:
                        if i != entrance_side:
                            map_data[py][px] = Terrain(TerrainType.MOUNTAIN)
                        # Draw wall segments
                        for j in range(3):
                            seg_x = int(center_x + (radius - j) * math.cos(angle))
                            seg_y = int(center_y + (radius - j) * math.sin(angle))
                            if 1 <= seg_x < size - 1 and 1 <= seg_y < size - 1 and i != entrance_side:
                                map_data[seg_y][seg_x] = Terrain(TerrainType.MOUNTAIN)
                
                # Entrance
                entrance_angle = (2 * math.pi * entrance_side) / 8
                entrance_x = int(center_x + radius * math.cos(entrance_angle))
                entrance_y = int(center_y + radius * math.sin(entrance_angle))
                if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                    map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
        
        elif structure_type == 'linear':
            # Draw a linear structure (bridge, path, wall, pier, jetty)
            desc_lower = description.lower()
            # Determine orientation from description
            if 'bridge' in desc_lower or 'causeway' in desc_lower:
                # Bridge is usually horizontal
                y = center_y
                length = size // 3
                start_x = max(2, center_x - length // 2)
                end_x = min(size - 2, center_x + length // 2)
                for x in range(start_x, end_x):
                    map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                    # Add width for bridge
                    if y + 1 < size - 1:
                        map_data[y + 1][x] = Terrain(TerrainType.MOUNTAIN)
            elif 'pier' in desc_lower or 'jetty' in desc_lower or 'wharf' in desc_lower or 'dock' in desc_lower:
                # Pier/jetty extends into water - usually horizontal, extending from edge toward center
                # Place pier extending from one edge toward center
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    # Horizontal pier - extends from left or right edge
                    from_left = random.random() < 0.5
                    if from_left:
                        # Pier extends from left edge
                        start_x = 1
                        end_x = min(size - 2, center_x + size // 6)
                        y = center_y
                    else:
                        # Pier extends from right edge
                        start_x = max(2, center_x - size // 6)
                        end_x = size - 2
                        y = center_y
                    # Draw pier (stone structure)
                    for x in range(start_x, end_x):
                        if 1 <= x < size - 1 and 1 <= y < size - 1:
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                            # Add width for pier (2-3 tiles wide)
                            if y + 1 < size - 1:
                                map_data[y + 1][x] = Terrain(TerrainType.MOUNTAIN)
                            if y + 2 < size - 1 and random.random() < 0.5:
                                map_data[y + 2][x] = Terrain(TerrainType.MOUNTAIN)
                else:
                    # Vertical pier - extends from top or bottom edge
                    from_top = random.random() < 0.5
                    if from_top:
                        # Pier extends from top edge
                        start_y = 1
                        end_y = min(size - 2, center_y + size // 6)
                        x = center_x
                    else:
                        # Pier extends from bottom edge
                        start_y = max(2, center_y - size // 6)
                        end_y = size - 2
                        x = center_x
                    # Draw pier (stone structure)
                    for y in range(start_y, end_y):
                        if 1 <= x < size - 1 and 1 <= y < size - 1:
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                            # Add width for pier (2-3 tiles wide)
                            if x + 1 < size - 1:
                                map_data[y][x + 1] = Terrain(TerrainType.MOUNTAIN)
                            if x + 2 < size - 1 and random.random() < 0.5:
                                map_data[y][x + 2] = Terrain(TerrainType.MOUNTAIN)
            elif 'stair' in desc_lower or 'step' in desc_lower:
                # Stairs can be diagonal or straight
                if random.random() < 0.5:
                    # Diagonal stairs
                    for i in range(min(10, size // 3)):
                        x = center_x - 5 + i
                        y = center_y - 5 + i
                        if 1 <= x < size - 1 and 1 <= y < size - 1:
                            map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                else:
                    # Vertical stairs
                    x = center_x
                    for y in range(max(2, center_y - size // 6), min(size - 2, center_y + size // 6)):
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
            else:
                # Default: randomly choose horizontal or vertical
                if random.random() < 0.5:
                    # Horizontal line
                    y = center_y
                    for x in range(max(2, center_x - size // 4), min(size - 2, center_x + size // 4)):
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                else:
                    # Vertical line
                    x = center_x
                    for y in range(max(2, center_y - size // 4), min(size - 2, center_y + size // 4)):
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
        
        elif structure_type == 'point':
            # Draw a single point or small cluster
            # Never place on edges - preserve edge terrain
            desc_lower = description.lower()
            if 'pair' in desc_lower or 'two' in desc_lower:
                # Two points
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x + 3 < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x + 3] = Terrain(TerrainType.MOUNTAIN)
            elif 'three' in desc_lower or 'sisters' in desc_lower:
                # Three points (triangle)
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x < size - 1 and 1 <= center_y - 2 < size - 1:
                    map_data[center_y - 2][center_x] = Terrain(TerrainType.MOUNTAIN)
                if 1 <= center_x + 2 < size - 1 and 1 <= center_y + 1 < size - 1:
                    map_data[center_y + 1][center_x + 2] = Terrain(TerrainType.MOUNTAIN)
            else:
                # Single point or small cluster
                if 1 <= center_x < size - 1 and 1 <= center_y < size - 1:
                    map_data[center_y][center_x] = Terrain(TerrainType.MOUNTAIN)
                # Sometimes add a small cluster
                if random.random() < 0.4:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = center_x + dx, center_y + dy
                            if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                                if random.random() < 0.3:
                                    map_data[ny][nx] = Terrain(TerrainType.MOUNTAIN)
        
        elif structure_type == 'mound':
            # Draw a mound/tomb/cairn with interior space and tunnel entrance
            import math
            radius = min(6, size // 8)
            
            # Create interior space (small chamber inside)
            inner_radius = max(2, radius - 3)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if dist < inner_radius:
                        map_data[y][x] = Terrain(TerrainType.GRASSLAND)
            
            # Draw mound walls (circular perimeter)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    # Draw wall (ring between inner and outer radius)
                    if inner_radius <= dist < radius:
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
            
            # Add tunnel entrance (passable path from outside to interior)
            # Choose entrance direction
            entrance_angle = random.random() * 2 * math.pi
            tunnel_length = radius - inner_radius
            
            # Create tunnel (passable path)
            for i in range(int(tunnel_length) + 1):
                tunnel_x = int(center_x + (inner_radius + i) * math.cos(entrance_angle))
                tunnel_y = int(center_y + (inner_radius + i) * math.sin(entrance_angle))
                if 1 <= tunnel_x < size - 1 and 1 <= tunnel_y < size - 1:
                    map_data[tunnel_y][tunnel_x] = Terrain(TerrainType.GRASSLAND)
            
            # Ensure entrance opening is clear
            entrance_x = int(center_x + radius * math.cos(entrance_angle))
            entrance_y = int(center_y + radius * math.sin(entrance_angle))
            if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
        
        # Add some variation: if multiple structures detected, add secondary ones
        if len(structures) > 1:
            # Add a second structure offset
            offset_x = center_x + size // 4
            offset_y = center_y + size // 4
            if 1 <= offset_x < size - 1 and 1 <= offset_y < size - 1:
                map_data[offset_y][offset_x] = Terrain(TerrainType.MOUNTAIN)
                # Add a few surrounding tiles for a small structure
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        nx, ny = offset_x + dx, offset_y + dy
                        if 1 <= nx < size - 1 and 1 <= ny < size - 1 and random.random() < 0.5:
                            map_data[ny][nx] = Terrain(TerrainType.MOUNTAIN)
    
    # Render additional features
    for feature_name, feature_type in additional_features:
        if feature_type == 'cave_entrance':  # cave, cavern, grotto
            # Cave as interior structure like tombs - mountain walls, entrance, tunnel, inner cavity
            import math
            cave_radius = min(7, size // 7)
            cave_x = center_x + random.randint(-size // 8, size // 8)
            cave_y = center_y + random.randint(-size // 8, size // 8)
            
            # Create interior space (cavity inside)
            inner_radius = max(3, cave_radius - 4)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - cave_x) ** 2 + (y - cave_y) ** 2) ** 0.5
                    if dist < inner_radius:
                        map_data[y][x] = Terrain(TerrainType.GRASSLAND)  # Inner cavity
            
            # Draw cave walls (mountain perimeter)
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    dist = ((x - cave_x) ** 2 + (y - cave_y) ** 2) ** 0.5
                    # Draw wall (ring between inner and outer radius)
                    if inner_radius <= dist < cave_radius:
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
            
            # Add tunnel entrance (passable path from outside to interior)
            # Choose entrance direction
            entrance_angle = random.random() * 2 * math.pi
            tunnel_length = cave_radius - inner_radius
            
            # Create tunnel (passable path)
            for i in range(int(tunnel_length) + 2):
                tunnel_x = int(cave_x + (inner_radius + i) * math.cos(entrance_angle))
                tunnel_y = int(cave_y + (inner_radius + i) * math.sin(entrance_angle))
                if 1 <= tunnel_x < size - 1 and 1 <= tunnel_y < size - 1:
                    map_data[tunnel_y][tunnel_x] = Terrain(TerrainType.GRASSLAND)
            
            # Ensure entrance opening is clear
            entrance_x = int(cave_x + cave_radius * math.cos(entrance_angle))
            entrance_y = int(cave_y + cave_radius * math.sin(entrance_angle))
            if 1 <= entrance_x < size - 1 and 1 <= entrance_y < size - 1:
                map_data[entrance_y][entrance_x] = Terrain(TerrainType.GRASSLAND)
            # Also clear a few tiles around entrance for easier access
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = entrance_x + dx, entrance_y + dy
                    if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                        dist_from_entrance = ((nx - entrance_x) ** 2 + (ny - entrance_y) ** 2) ** 0.5
                        if dist_from_entrance <= 1.5:
                            # Check if this tile is outside the cave radius
                            dist_from_center = ((nx - cave_x) ** 2 + (ny - cave_y) ** 2) ** 0.5
                            if dist_from_center >= cave_radius - 1:
                                map_data[ny][nx] = Terrain(TerrainType.GRASSLAND)
    
    # Ensure all outer edge tiles match the base terrain type (organic, irregular edges)
    # Create highly organic, invasive coastline-like edges that deeply creep into the quest location
    # This must be done at the end, but we need to preserve features that were placed
    import math
    
    # Create highly irregular edge pattern using multiple overlapping sine waves for organic coastline effect
    # Edge depth varies based on map size, but we need to preserve interior features
    # Base depth is a percentage of map size to ensure it scales appropriately
    # For monument maps (standing stones, stone circles, etc.), reduce edge depth to minimize hill noise
    base_max_depth = max(4, int(size * 0.12))  # At least 4 tiles, or 12% of map size
    # Check if this is a monument map (structures, not natural features)
    desc_lower = description.lower()
    import re
    monument_patterns = [
        r'\bstanding[\s-]?stone', r'\bstone[\s-]?circle', r'\bring\s+of\s+stones?\b',
        r'\bmenhir', r'\bdolmen', r'\bcairn', r'\bmound\b', r'\bbarrow\b',
        r'\btomb\b', r'\bgrave\b', r'\bcrypt\b', r'\bmonument\b'
    ]
    has_monuments = any(re.search(pattern, desc_lower) for pattern in monument_patterns)
    
    # Reduce edge depth for monument maps to minimize hill noise in interior
    # Save current random state and restore it after edge depth calculation
    # to ensure edge generation uses consistent random values
    random_state = random.getstate()
    if has_monuments and base_terrain == TerrainType.HILLS:
        base_max_depth = max(3, int(size * 0.08))  # Reduced to 8% for monuments
        max_edge_depth = random.randint(base_max_depth, base_max_depth + 3)  # Reduced range
    else:
        max_edge_depth = random.randint(base_max_depth, base_max_depth + 6)
    # Restore random state for consistent edge generation
    random.setstate(random_state)
    
    # Track which tiles have important features (structures, water, forest) that shouldn't be overwritten
    # We'll preserve these features even in edge areas, but allow base_terrain to be placed
    feature_tiles = set()
    for y in range(size):
        for x in range(size):
            terrain = map_data[y][x]
            # Preserve features that are NOT base terrain and NOT grassland
            # This means structures (mountain), water, forest, etc. should be preserved
            # But we allow base_terrain (hills, forested_hill, etc.) to be placed in edge areas
            # Only preserve features that are NOT on the absolute edge (edges must be base terrain)
            if terrain.terrain_type not in (TerrainType.GRASSLAND, base_terrain):
                # Don't preserve features on absolute edges - those must be base terrain
                if not (x == 0 or x == size - 1 or y == 0 or y == size - 1):
                    feature_tiles.add((x, y))
    
    # Generate edge depth map using multiple sine waves for highly organic variation
    # Calculate minimum guaranteed depth to ensure edges always extend
    min_guaranteed_depth = max(3, int(max_edge_depth * 0.3))  # At least 30% of max depth
    
    # First pass: Apply guaranteed minimum extension for all edges
    for x in range(size):
        for y in range(size):
            # Skip if this tile has an important feature that should be preserved (unless it's on the absolute edge)
            if (x, y) in feature_tiles and not (x == 0 or x == size - 1 or y == 0 or y == size - 1):
                continue
            
            # Calculate distance from each edge
            dist_top = y
            dist_bottom = size - 1 - y
            dist_left = x
            dist_right = size - 1 - x
            
            # Find minimum distance to any edge
            min_dist = min(dist_top, dist_bottom, dist_left, dist_right)
            
            # Guarantee minimum extension for all edges
            if min_dist < min_guaranteed_depth:
                map_data[y][x] = Terrain(base_terrain)
    
    # Second pass: Apply organic wave-based variation for deeper extension
    for x in range(size):
        for y in range(size):
            # Skip if this tile has an important feature that should be preserved (unless it's on the absolute edge)
            if (x, y) in feature_tiles and not (x == 0 or x == size - 1 or y == 0 or y == size - 1):
                continue
            
            # Calculate distance from each edge
            dist_top = y
            dist_bottom = size - 1 - y
            dist_left = x
            dist_right = size - 1 - x
            
            # Find minimum distance to any edge
            min_dist = min(dist_top, dist_bottom, dist_left, dist_right)
            
            # Process tiles near edges (extend check to max_edge_depth + buffer) for organic variation
            if min_guaranteed_depth <= min_dist <= max_edge_depth + 2:
                # Use multiple sine waves with different frequencies and phases for highly organic coastline effect
                # Use deterministic phases based on position and description hash for consistency
                desc_hash = hash(description) % 10000
                phase1 = ((x * 0.1 + y * 0.15 + desc_hash * 0.01) % (2 * math.pi))
                phase2 = ((x * 0.2 - y * 0.18 + desc_hash * 0.015) % (2 * math.pi))
                phase3 = ((x * 0.3 + y * 0.25 + desc_hash * 0.02) % (2 * math.pi))
                phase4 = ((x * 0.5 - y * 0.4 + desc_hash * 0.025) % (2 * math.pi))
                
                # Multiple overlapping waves with different frequencies create organic patterns
                # Use higher frequency waves for more ragged edges
                wave1 = math.sin(x * 0.4 + y * 0.3 + phase1) * 0.4
                wave2 = math.sin(x * 0.7 - y * 0.5 + phase2) * 0.3
                wave3 = math.sin(x * 1.2 + y * 0.9 + phase3) * 0.2
                wave4 = math.sin(x * 2.0 - y * 1.5 + phase4) * 0.1
                
                # Add deterministic noise for extra ragged variation (based on position hash)
                noise_seed = hash(f"{desc_hash}_{x}_{y}") % 10000
                noise = ((noise_seed / 10000.0) - 0.5) * 0.35  # Deterministic noise
                
                # Add perlin-like noise using multiple octaves for more natural variation
                noise2 = math.sin(x * 0.15 + y * 0.12 + phase1) * 0.15
                noise3 = math.sin(x * 0.3 - y * 0.25 + phase2) * 0.1
                
                combined_wave = (wave1 + wave2 + wave3 + wave4) / 4.0 + noise + noise2 + noise3
                
                # Calculate edge depth based on position and wave pattern
                # Use wider range (0.4 to 1.0) to ensure good penetration
                depth_multiplier = 0.4 + 0.6 * (0.5 + 0.5 * combined_wave)
                
                # Enhance corners - make them thicker/deeper to avoid square appearance
                # Calculate distance to nearest corner
                corner_distances = [
                    ((x - 0) ** 2 + (y - 0) ** 2) ** 0.5,  # Top-left
                    ((x - (size - 1)) ** 2 + (y - 0) ** 2) ** 0.5,  # Top-right
                    ((x - 0) ** 2 + (y - (size - 1)) ** 2) ** 0.5,  # Bottom-left
                    ((x - (size - 1)) ** 2 + (y - (size - 1)) ** 2) ** 0.5  # Bottom-right
                ]
                min_corner_dist = min(corner_distances)
                
                # If close to a corner, increase depth to make corners thicker
                corner_boost = 0
                if min_corner_dist < max_edge_depth * 1.5:
                    # Boost depth near corners (closer = more boost)
                    corner_factor = 1.0 - (min_corner_dist / (max_edge_depth * 1.5))
                    corner_boost = corner_factor * 0.4  # Up to 40% additional depth
                
                depth_multiplier = min(1.0, depth_multiplier + corner_boost)
                # Calculate depth for this specific position based on wave pattern
                # This creates organic, wavy edges
                # Ensure minimum depth is at least 30% of max_edge_depth to guarantee extension
                min_depth = max(3, int(max_edge_depth * 0.3))
                depth = max(min_depth, int(max_edge_depth * depth_multiplier))
                
                # Apply edge terrain based on which edge is closest
                # Use the calculated depth to determine if this tile should be edge terrain
                if min_dist == dist_top:
                    # Top edge - wave extends downward
                    # Tile should be hills if it's within 'depth' tiles of the top edge
                    if y < depth:
                        map_data[y][x] = Terrain(base_terrain)
                elif min_dist == dist_bottom:
                    # Bottom edge - wave extends upward
                    # Tile should be hills if it's within 'depth' tiles of the bottom edge
                    if y >= size - depth:
                        map_data[y][x] = Terrain(base_terrain)
                elif min_dist == dist_left:
                    # Left edge - wave extends rightward
                    # Tile should be hills if it's within 'depth' tiles of the left edge
                    if x < depth:
                        map_data[y][x] = Terrain(base_terrain)
                elif min_dist == dist_right:
                    # Right edge - wave extends leftward
                    # Tile should be hills if it's within 'depth' tiles of the right edge
                    if x >= size - depth:
                        map_data[y][x] = Terrain(base_terrain)
                
                # Corner handling is now integrated into the main depth calculation above
                # This ensures corners are naturally thicker without separate logic
    
    # Ensure the absolute outermost edge is always base terrain (for clean boundaries)
    for y in range(size):
        for x in range(size):
            if x == 0 or x == size - 1 or y == 0 or y == size - 1:
                map_data[y][x] = Terrain(base_terrain)
    
    return map_data


def generate_all_maps():
    """Generate maps for all descriptions and return as dictionary."""
    from data_quest_locations import quest_location_descriptions
    all_maps = {}
    
    for terrain_type, descriptions in quest_location_descriptions.items():
        all_maps[terrain_type] = {}
        print(f"Generating maps for {terrain_type}...")
        
        for i, description in enumerate(descriptions, 1):
            print(f"  [{i}/{len(descriptions)}] {description[:60]}...")
            
            # Generate map with structures
            map_data = generate_map_with_structures(description, terrain_type, MAP_SIZE)
            
            # Convert to serializable format
            map_array = []
            for row in map_data:
                map_row = []
                for terrain in row:
                    map_row.append(terrain.terrain_type.value)
                map_array.append(map_row)
            
            # Store with description
            all_maps[terrain_type][description] = map_array
    
    return all_maps


def save_maps_to_file(maps_data, filename="quest_location_maps_data.json"):
    """Save maps to JSON file."""
    import json
    with open(filename, 'w') as f:
        json.dump(maps_data, f, indent=2)
    print(f"\n✓ Saved {filename}")


if __name__ == "__main__":
    print("Generating quest location maps with structure detection...")
    from data_quest_locations import quest_location_descriptions
    maps = generate_all_maps()
    save_maps_to_file(maps)
    print(f"\n✓ Generated maps for {sum(len(descs) for descs in quest_location_descriptions.values())} descriptions")
