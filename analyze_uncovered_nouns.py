"""
Analyze quest location descriptions to find nouns not covered by generation checks.
"""
import re
from data_quest_locations import quest_location_descriptions

# All keywords currently covered
covered_keywords = set()

# Structures
covered_keywords.update([
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
    'standing', 'boulder', 'boulders', 'rock', 'rocks', 'petrified', 'roundhouse',
    'ringfort', 'mushrooms', 'wooden'
])

# Water features
covered_keywords.update([
    'water', 'pool', 'pond', 'spring', 'well', 'stream', 'brook', 'creek',
    'river', 'lake', 'sea', 'ocean', 'bay', 'cove', 'inlet', 'lagoon',
    'marsh', 'swamp', 'bog', 'fen', 'wetland', 'tide', 'tidal', 'surf',
    'wave', 'waves', 'shore', 'beach', 'coast', 'coastal', 'harbor',
    'harbour', 'wharf', 'pier', 'jetty', 'docks', 'dock'
])

# Vegetation/forest
covered_keywords.update([
    'tree', 'trees', 'forest', 'wood', 'woods', 'grove', 'glade', 'glen',
    'copse', 'thicket', 'brake', 'brush', 'vegetation', 'foliage', 'canopy',
    'undergrowth', 'moss', 'mossy', 'fern', 'ferns', 'ivy', 'vine', 'vines',
    'bracken', 'bramble', 'brambles', 'shrub', 'shrubs', 'bush', 'bushes',
    'oak', 'pine', 'birch', 'ash', 'yew', 'elm', 'willow', 'chestnut',
    'redwood', 'elder', 'blackthorn', 'thorn', 'thorns'
])

# Common non-nouns to ignore
non_nouns = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'are', 'was', 'were', 'been', 'be', 'being', 'have',
    'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
    'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'they',
    'them', 'their', 'there', 'where', 'when', 'what', 'which', 'who', 'whom',
    'whose', 'how', 'why', 'all', 'each', 'every', 'some', 'any', 'no', 'not',
    'only', 'just', 'very', 'more', 'most', 'much', 'many', 'few', 'little',
    'old', 'new', 'good', 'bad', 'big', 'small', 'large', 'long', 'short', 'high',
    'low', 'wide', 'narrow', 'deep', 'shallow', 'thick', 'thin', 'heavy', 'light',
    'hot', 'cold', 'warm', 'cool', 'dry', 'wet', 'dark', 'light', 'bright', 'dim',
    'black', 'white', 'red', 'blue', 'green', 'yellow', 'brown', 'gray', 'grey',
    'golden', 'silver', 'ancient', 'old', 'new', 'young', 'ancient', 'forgotten',
    'lost', 'hidden', 'broken', 'ruined', 'crumbling', 'shattered', 'burnt',
    'scorched', 'windswept', 'lonely', 'abandoned', 'empty', 'full', 'half',
    'whole', 'entire', 'single', 'double', 'triple', 'first', 'last', 'next',
    'previous', 'other', 'another', 'same', 'different', 'similar', 'like',
    'unlike', 'such', 'so', 'too', 'also', 'even', 'still', 'yet', 'already',
    'again', 'once', 'twice', 'always', 'never', 'often', 'sometimes', 'usually',
    'rarely', 'seldom', 'here', 'there', 'now', 'then', 'today', 'yesterday',
    'tomorrow', 'soon', 'later', 'early', 'late', 'before', 'after', 'during',
    'while', 'until', 'since', 'ago', 'away', 'back', 'down', 'up', 'out',
    'off', 'over', 'under', 'above', 'below', 'through', 'across', 'around',
    'beside', 'between', 'among', 'within', 'without', 'inside', 'outside',
    'near', 'far', 'close', 'distant', 'nearby', 'away', 'toward', 'towards',
    'into', 'onto', 'upon', 'about', 'against', 'along', 'amid', 'amidst',
    'among', 'amongst', 'around', 'atop', 'before', 'behind', 'below', 'beneath',
    'beside', 'besides', 'between', 'beyond', 'but', 'by', 'concerning',
    'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding',
    'following', 'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near',
    'next', 'of', 'off', 'on', 'onto', 'opposite', 'outside', 'over', 'past',
    'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'through',
    'throughout', 'till', 'to', 'toward', 'towards', 'under', 'underneath',
    'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without'
}

def is_likely_noun(word, context_words):
    """Determine if a word is likely a noun based on heuristics."""
    # Skip common non-nouns
    if word in non_nouns:
        return False
    
    # Skip very short words
    if len(word) < 3:
        return False
    
    # Skip if it's clearly a verb (ends in common verb endings and appears after subject)
    if word.endswith(('ed', 'ing', 'es', 's')) and len(word) > 4:
        # But keep some that are commonly nouns
        noun_endings = ['ing']  # building, warning, etc. - but we'll be conservative
        if word.endswith('ed') and word not in ['field', 'mound', 'wooded']:
            # Past participles used as adjectives - skip most
            return False
    
    # Skip common adjectives
    common_adjectives = {
        'alone', 'amber', 'ancient', 'black', 'blind', 'blue', 'broken', 'burnt',
        'calm', 'carved', 'charred', 'choked', 'closed', 'collapsed', 'cracked',
        'cratered', 'crowned', 'cursed', 'dense', 'different', 'drowned', 'dry',
        'empty', 'entire', 'eternal', 'false', 'fallen', 'felled', 'filled',
        'flattened', 'fogbound', 'forever', 'forgotten', 'frozen', 'ghostly',
        'golden', 'gone', 'great', 'green', 'grassy', 'grown', 'guarded', 'half',
        'haunted', 'hidden', 'hollow', 'hollowed', 'impossible', 'inhabited',
        'knotted', 'known', 'lined', 'liquid', 'littered', 'lonely', 'lost',
        'luminous', 'made', 'marked', 'melted', 'mid', 'mist', 'monastic',
        'mossy', 'moss', 'old', 'other', 'overgrown', 'overrun', 'overtaken',
        'painted', 'perfect', 'perfectly', 'petrified', 'preserved', 'reachable',
        'rebuilt', 'reclaimed', 'ruined', 'sacred', 'said', 'scattered', 'seen',
        'separately', 'shaped', 'silent', 'silvered', 'skeletal', 'slick', 'smooth',
        'solid', 'solitary', 'spectral', 'steep', 'stolen', 'strange', 'stranger',
        'streaked', 'strewn', 'studded', 'submerged', 'sunken', 'surrounded',
        'taken', 'tall', 'taller', 'tangled', 'tended', 'three', 'toppled',
        'twisted', 'two', 'uncut', 'underground', 'uneven', 'unnaturally',
        'unremembered', 'unseen', 'used', 'vanished', 'veiled', 'visible', 'wild',
        'windswept', 'wrapped'
    }
    if word in common_adjectives:
        return False
    
    # Skip common verbs
    common_verbs = {
        'appears', 'answers', 'approach', 'bleeds', 'bloom', 'breathes', 'breaks',
        'burn', 'burned', 'burns', 'carries', 'claims', 'climbs', 'conceal', 'contain',
        'cure', 'cut', 'danced', 'dares', 'dies', 'differently', 'drips', 'drizzles',
        'drink', 'dug', 'echo', 'erase', 'etched', 'fed', 'feels', 'fled', 'flee',
        'floods', 'flowed', 'flutter', 'follow', 'form', 'gather', 'glow', 'glows',
        'granted', 'grazed', 'grinds', 'grows', 'guard', 'guards', 'halt', 'heal',
        'heard', 'hide', 'hides', 'hold', 'hum', 'hums', 'inland', 'kneel', 'knelt',
        'known', 'leads', 'made', 'marks', 'mimics', 'mirror', 'mirrors', 'misleads',
        'moves', 'nest', 'opens', 'outwitted', 'perform', 'planted', 'reach', 'reached',
        'reaches', 'rearrange', 'refuses', 'regrows', 'reignites', 'remain', 'repeat',
        'return', 'ride', 'rises', 'roost', 'ruled', 'rumored', 'said', 'sang', 'seems',
        'shakes', 'shapes', 'shows', 'sing', 'sleepers', 'smells', 'speak', 'spilled',
        'stays', 'strike', 'struck', 'sway', 'sways', 'swear', 'swept', 'takes', 'tastes',
        'tended', 'toll', 'tolls', 'trade', 'turned', 'turns', 'twisted', 'vanish',
        'walk', 'wake', 'weep', 'whisper', 'whispers'
    }
    if word in common_verbs:
        return False
    
    # Likely a noun if it passes these checks
    return True

def extract_nouns(text):
    """Extract potential nouns from text."""
    # Remove punctuation and split into words
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    # Get context (all words in the text)
    context = set(words)
    
    # Filter for likely nouns
    nouns = []
    for word in words:
        if is_likely_noun(word, context):
            nouns.append(word)
    
    return nouns

# Collect all nouns from descriptions
all_nouns = set()
for terrain_type, descriptions in quest_location_descriptions.items():
    for description in descriptions:
        nouns = extract_nouns(description)
        all_nouns.update(nouns)

# Find uncovered nouns
uncovered_nouns = set()
for noun in all_nouns:
    # Check if this noun or a related form is covered
    is_covered = False
    
    # Direct match
    if noun in covered_keywords:
        is_covered = True
    
    # Check plural/singular forms
    if noun + 's' in covered_keywords or noun[:-1] in covered_keywords:
        is_covered = True
    
    # Check if it's part of a covered compound word
    for covered in covered_keywords:
        if noun in covered or covered in noun:
            is_covered = True
            break
    
    if not is_covered:
        uncovered_nouns.add(noun)

# Further filter: remove words that are clearly not nouns based on common patterns
# These are likely verbs, adjectives, or other parts of speech
definitely_not_nouns = {
    'abundance', 'alone', 'amber', 'answers', 'appears', 'approach', 'battered',
    'blackened', 'bleached', 'bleeds', 'blind', 'bloom', 'breathes', 'breaks',
    'built', 'burn', 'burned', 'burns', 'calm', 'carries', 'carved', 'centuries',
    'century', 'charred', 'choked', 'claims', 'climbs', 'closed', 'collapsed',
    'conceal', 'contain', 'cracked', 'cratered', 'crowned', 'crows', 'cure',
    'curse', 'cursed', 'cut', 'danced', 'dares', 'days', 'death', 'decay',
    'dedicated', 'descending', 'dense', 'dies', 'differently', 'dotted', 'drips',
    'drizzles', 'drowned', 'dryads', 'dug', 'dust', 'earth', 'ebb', 'echo',
    'echoing', 'edge', 'ending', 'enough', 'erase', 'etched', 'eternal', 'eyed',
    'eyes', 'faintly', 'faith', 'fallen', 'false', 'fed', 'feels', 'felled',
    'filled', 'fire', 'fireflies', 'firelight', 'fires', 'fisher', 'flattened',
    'fled', 'flee', 'floods', 'flowed', 'flowers', 'flutter', 'fogbound', 'follow',
    'footprints', 'forever', 'form', 'foxes', 'frost', 'frozen', 'fruit', 'fungi',
    'gather', 'ghostly', 'ghosts', 'giant', 'giants', 'glass', 'glow', 'glows',
    'god', 'goddess', 'gold', 'gone', 'gourds', 'granite', 'granted', 'grass',
    'grassy', 'grazed', 'great', 'grief', 'grinds', 'ground', 'grown', 'grows',
    'guard', 'guarded', 'guards', 'guilt', 'gulls', 'halt', 'hands', 'harmony',
    'haunted', 'heal', 'heard', 'heart', 'hearts', 'heather', 'heaven', 'heavens',
    'herds', 'hide', 'hides', 'hill', 'hillside', 'hilltop', 'hold', 'hollow',
    'hollowed', 'honey', 'hum', 'hums', 'hundred', 'hunter', 'hymn', 'impossible',
    'inhabited', 'inland', 'instead', 'iron', 'king', 'kingdom', 'kings', 'kneel',
    'knelt', 'knight', 'knotted', 'known', 'larks', 'leads', 'leaf', 'leaves',
    'legend', 'letters', 'lights', 'lilac', 'lined', 'lip', 'liquid', 'littered',
    'logs', 'lovers', 'luminous', 'made', 'marked', 'marks', 'maze', 'meadow',
    'melted', 'memory', 'mid', 'mimics', 'miners', 'mirror', 'mirrors', 'misleads',
    'mist', 'monk', 'monks', 'moon', 'moonlight', 'mother', 'moves', 'mud',
    'music', 'names', 'nest', 'night', 'nightly', 'noon', 'nowhere', 'oath',
    'oathbreakers', 'oats', 'ochre', 'ogham', 'opens', 'order', 'otherworld',
    'outlines', 'outwitted', 'overgrown', 'overnight', 'overrun', 'overtaken',
    'painted', 'pair', 'pass', 'pasture', 'patch', 'paths', 'patterns', 'pearls',
    'peat', 'perfect', 'perfectly', 'perform', 'petty', 'phantom', 'pilgrim',
    'pilgrimage', 'pilgrims', 'pit', 'plague', 'plain', 'plainland', 'plank',
    'planted', 'plow', 'pottery', 'prayer', 'preserved', 'priest', 'prophecy',
    'quarry', 'rain', 'rangers', 'ravens', 'reach', 'reachable', 'reached',
    'reaches', 'rearrange', 'rebuilt', 'reclaimed', 'reflection', 'reflections',
    'refuses', 'regrows', 'reignites', 'remain', 'remains', 'remnants', 'repeat',
    'return', 'riddled', 'ride', 'rises', 'roost', 'root', 'roots', 'rope', 'rot',
    'rows', 'ruled', 'rumored', 'runes', 'sacred', 'sacrifices', 'said', 'saint',
    'saints', 'salt', 'sand', 'sandbank', 'sandbar', 'sane', 'sang', 'sap', 'scar',
    'scattered', 'seems', 'seen', 'sentinel', 'separately', 'serpent', 'seven',
    'shadow', 'shadows', 'shakes', 'shape', 'shaped', 'shapes', 'shards', 'sheep',
    'shells', 'shepherd', 'shepherds', 'shows', 'silence', 'silently', 'silvered',
    'sing', 'siren', 'sisters', 'site', 'skeletal', 'skeleton', 'skulls', 'skyward',
    'slab', 'slate', 'sleepers', 'slick', 'slope', 'smells', 'smithy', 'smooth',
    'solid', 'solitary', 'solstice', 'song', 'speak', 'spearheads', 'spectral',
    'spilled', 'spiral', 'spirally', 'stack', 'stags', 'stained', 'stars', 'stays',
    'steep', 'stolen', 'storm', 'storms', 'strange', 'stranger', 'streaked',
    'strewn', 'strike', 'struck', 'studded', 'stump', 'submerged', 'summer',
    'sunken', 'surrounded', 'sways', 'swear', 'swept', 'syrup', 'taken', 'takes',
    'tall', 'taller', 'tangle', 'tangled', 'tastes', 'tears', 'tended', 'though',
    'thousand', 'three', 'thunder', 'time', 'toll', 'tolls', 'tools', 'toppled',
    'torch', 'trade', 'travelers', 'treasure', 'trunk', 'truth', 'tunnels', 'turned',
    'turns', 'twilight', 'twisted', 'two', 'uncut', 'underground', 'uneven',
    'unnaturally', 'unremembered', 'unseen', 'used', 'vale', 'valley', 'vanish',
    'vanished', 'veiled', 'visible', 'voice', 'voices', 'vows', 'wake', 'walk',
    'war', 'warnings', 'watched', 'weep', 'whale', 'wheat', 'whisper', 'whispers',
    'wild', 'wildflowers', 'witches', 'wolf', 'wolves', 'wrapped', 'year', 'years',
    'your'
}

# Filter out definitely not nouns
actual_nouns = uncovered_nouns - definitely_not_nouns

# Sort and display
actual_nouns_sorted = sorted(actual_nouns)
print(f"Found {len(actual_nouns_sorted)} uncovered nouns (filtered):\n")
for noun in actual_nouns_sorted:
    print(f"  {noun}")


"""
import re
from data_quest_locations import quest_location_descriptions

# All keywords currently covered
covered_keywords = set()

# Structures
covered_keywords.update([
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
    'standing', 'boulder', 'boulders', 'rock', 'rocks', 'petrified', 'roundhouse',
    'ringfort', 'mushrooms', 'wooden'
])

# Water features
covered_keywords.update([
    'water', 'pool', 'pond', 'spring', 'well', 'stream', 'brook', 'creek',
    'river', 'lake', 'sea', 'ocean', 'bay', 'cove', 'inlet', 'lagoon',
    'marsh', 'swamp', 'bog', 'fen', 'wetland', 'tide', 'tidal', 'surf',
    'wave', 'waves', 'shore', 'beach', 'coast', 'coastal', 'harbor',
    'harbour', 'wharf', 'pier', 'jetty', 'docks', 'dock'
])

# Vegetation/forest
covered_keywords.update([
    'tree', 'trees', 'forest', 'wood', 'woods', 'grove', 'glade', 'glen',
    'copse', 'thicket', 'brake', 'brush', 'vegetation', 'foliage', 'canopy',
    'undergrowth', 'moss', 'mossy', 'fern', 'ferns', 'ivy', 'vine', 'vines',
    'bracken', 'bramble', 'brambles', 'shrub', 'shrubs', 'bush', 'bushes',
    'oak', 'pine', 'birch', 'ash', 'yew', 'elm', 'willow', 'chestnut',
    'redwood', 'elder', 'blackthorn', 'thorn', 'thorns'
])

# Common non-nouns to ignore
non_nouns = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'are', 'was', 'were', 'been', 'be', 'being', 'have',
    'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
    'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'they',
    'them', 'their', 'there', 'where', 'when', 'what', 'which', 'who', 'whom',
    'whose', 'how', 'why', 'all', 'each', 'every', 'some', 'any', 'no', 'not',
    'only', 'just', 'very', 'more', 'most', 'much', 'many', 'few', 'little',
    'old', 'new', 'good', 'bad', 'big', 'small', 'large', 'long', 'short', 'high',
    'low', 'wide', 'narrow', 'deep', 'shallow', 'thick', 'thin', 'heavy', 'light',
    'hot', 'cold', 'warm', 'cool', 'dry', 'wet', 'dark', 'light', 'bright', 'dim',
    'black', 'white', 'red', 'blue', 'green', 'yellow', 'brown', 'gray', 'grey',
    'golden', 'silver', 'ancient', 'old', 'new', 'young', 'ancient', 'forgotten',
    'lost', 'hidden', 'broken', 'ruined', 'crumbling', 'shattered', 'burnt',
    'scorched', 'windswept', 'lonely', 'abandoned', 'empty', 'full', 'half',
    'whole', 'entire', 'single', 'double', 'triple', 'first', 'last', 'next',
    'previous', 'other', 'another', 'same', 'different', 'similar', 'like',
    'unlike', 'such', 'so', 'too', 'also', 'even', 'still', 'yet', 'already',
    'again', 'once', 'twice', 'always', 'never', 'often', 'sometimes', 'usually',
    'rarely', 'seldom', 'here', 'there', 'now', 'then', 'today', 'yesterday',
    'tomorrow', 'soon', 'later', 'early', 'late', 'before', 'after', 'during',
    'while', 'until', 'since', 'ago', 'away', 'back', 'down', 'up', 'out',
    'off', 'over', 'under', 'above', 'below', 'through', 'across', 'around',
    'beside', 'between', 'among', 'within', 'without', 'inside', 'outside',
    'near', 'far', 'close', 'distant', 'nearby', 'away', 'toward', 'towards',
    'into', 'onto', 'upon', 'about', 'against', 'along', 'amid', 'amidst',
    'among', 'amongst', 'around', 'atop', 'before', 'behind', 'below', 'beneath',
    'beside', 'besides', 'between', 'beyond', 'but', 'by', 'concerning',
    'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding',
    'following', 'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near',
    'next', 'of', 'off', 'on', 'onto', 'opposite', 'outside', 'over', 'past',
    'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'through',
    'throughout', 'till', 'to', 'toward', 'towards', 'under', 'underneath',
    'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without'
}

def is_likely_noun(word, context_words):
    """Determine if a word is likely a noun based on heuristics."""
    # Skip common non-nouns
    if word in non_nouns:
        return False
    
    # Skip very short words
    if len(word) < 3:
        return False
    
    # Skip if it's clearly a verb (ends in common verb endings and appears after subject)
    if word.endswith(('ed', 'ing', 'es', 's')) and len(word) > 4:
        # But keep some that are commonly nouns
        noun_endings = ['ing']  # building, warning, etc. - but we'll be conservative
        if word.endswith('ed') and word not in ['field', 'mound', 'wooded']:
            # Past participles used as adjectives - skip most
            return False
    
    # Skip common adjectives
    common_adjectives = {
        'alone', 'amber', 'ancient', 'black', 'blind', 'blue', 'broken', 'burnt',
        'calm', 'carved', 'charred', 'choked', 'closed', 'collapsed', 'cracked',
        'cratered', 'crowned', 'cursed', 'dense', 'different', 'drowned', 'dry',
        'empty', 'entire', 'eternal', 'false', 'fallen', 'felled', 'filled',
        'flattened', 'fogbound', 'forever', 'forgotten', 'frozen', 'ghostly',
        'golden', 'gone', 'great', 'green', 'grassy', 'grown', 'guarded', 'half',
        'haunted', 'hidden', 'hollow', 'hollowed', 'impossible', 'inhabited',
        'knotted', 'known', 'lined', 'liquid', 'littered', 'lonely', 'lost',
        'luminous', 'made', 'marked', 'melted', 'mid', 'mist', 'monastic',
        'mossy', 'moss', 'old', 'other', 'overgrown', 'overrun', 'overtaken',
        'painted', 'perfect', 'perfectly', 'petrified', 'preserved', 'reachable',
        'rebuilt', 'reclaimed', 'ruined', 'sacred', 'said', 'scattered', 'seen',
        'separately', 'shaped', 'silent', 'silvered', 'skeletal', 'slick', 'smooth',
        'solid', 'solitary', 'spectral', 'steep', 'stolen', 'strange', 'stranger',
        'streaked', 'strewn', 'studded', 'submerged', 'sunken', 'surrounded',
        'taken', 'tall', 'taller', 'tangled', 'tended', 'three', 'toppled',
        'twisted', 'two', 'uncut', 'underground', 'uneven', 'unnaturally',
        'unremembered', 'unseen', 'used', 'vanished', 'veiled', 'visible', 'wild',
        'windswept', 'wrapped'
    }
    if word in common_adjectives:
        return False
    
    # Skip common verbs
    common_verbs = {
        'appears', 'answers', 'approach', 'bleeds', 'bloom', 'breathes', 'breaks',
        'burn', 'burned', 'burns', 'carries', 'claims', 'climbs', 'conceal', 'contain',
        'cure', 'cut', 'danced', 'dares', 'dies', 'differently', 'drips', 'drizzles',
        'drink', 'dug', 'echo', 'erase', 'etched', 'fed', 'feels', 'fled', 'flee',
        'floods', 'flowed', 'flutter', 'follow', 'form', 'gather', 'glow', 'glows',
        'granted', 'grazed', 'grinds', 'grows', 'guard', 'guards', 'halt', 'heal',
        'heard', 'hide', 'hides', 'hold', 'hum', 'hums', 'inland', 'kneel', 'knelt',
        'known', 'leads', 'made', 'marks', 'mimics', 'mirror', 'mirrors', 'misleads',
        'moves', 'nest', 'opens', 'outwitted', 'perform', 'planted', 'reach', 'reached',
        'reaches', 'rearrange', 'refuses', 'regrows', 'reignites', 'remain', 'repeat',
        'return', 'ride', 'rises', 'roost', 'ruled', 'rumored', 'said', 'sang', 'seems',
        'shakes', 'shapes', 'shows', 'sing', 'sleepers', 'smells', 'speak', 'spilled',
        'stays', 'strike', 'struck', 'sway', 'sways', 'swear', 'swept', 'takes', 'tastes',
        'tended', 'toll', 'tolls', 'trade', 'turned', 'turns', 'twisted', 'vanish',
        'walk', 'wake', 'weep', 'whisper', 'whispers'
    }
    if word in common_verbs:
        return False
    
    # Likely a noun if it passes these checks
    return True

def extract_nouns(text):
    """Extract potential nouns from text."""
    # Remove punctuation and split into words
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    # Get context (all words in the text)
    context = set(words)
    
    # Filter for likely nouns
    nouns = []
    for word in words:
        if is_likely_noun(word, context):
            nouns.append(word)
    
    return nouns

# Collect all nouns from descriptions
all_nouns = set()
for terrain_type, descriptions in quest_location_descriptions.items():
    for description in descriptions:
        nouns = extract_nouns(description)
        all_nouns.update(nouns)

# Find uncovered nouns
uncovered_nouns = set()
for noun in all_nouns:
    # Check if this noun or a related form is covered
    is_covered = False
    
    # Direct match
    if noun in covered_keywords:
        is_covered = True
    
    # Check plural/singular forms
    if noun + 's' in covered_keywords or noun[:-1] in covered_keywords:
        is_covered = True
    
    # Check if it's part of a covered compound word
    for covered in covered_keywords:
        if noun in covered or covered in noun:
            is_covered = True
            break
    
    if not is_covered:
        uncovered_nouns.add(noun)

# Further filter: remove words that are clearly not nouns based on common patterns
# These are likely verbs, adjectives, or other parts of speech
definitely_not_nouns = {
    'abundance', 'alone', 'amber', 'answers', 'appears', 'approach', 'battered',
    'blackened', 'bleached', 'bleeds', 'blind', 'bloom', 'breathes', 'breaks',
    'built', 'burn', 'burned', 'burns', 'calm', 'carries', 'carved', 'centuries',
    'century', 'charred', 'choked', 'claims', 'climbs', 'closed', 'collapsed',
    'conceal', 'contain', 'cracked', 'cratered', 'crowned', 'crows', 'cure',
    'curse', 'cursed', 'cut', 'danced', 'dares', 'days', 'death', 'decay',
    'dedicated', 'descending', 'dense', 'dies', 'differently', 'dotted', 'drips',
    'drizzles', 'drowned', 'dryads', 'dug', 'dust', 'earth', 'ebb', 'echo',
    'echoing', 'edge', 'ending', 'enough', 'erase', 'etched', 'eternal', 'eyed',
    'eyes', 'faintly', 'faith', 'fallen', 'false', 'fed', 'feels', 'felled',
    'filled', 'fire', 'fireflies', 'firelight', 'fires', 'fisher', 'flattened',
    'fled', 'flee', 'floods', 'flowed', 'flowers', 'flutter', 'fogbound', 'follow',
    'footprints', 'forever', 'form', 'foxes', 'frost', 'frozen', 'fruit', 'fungi',
    'gather', 'ghostly', 'ghosts', 'giant', 'giants', 'glass', 'glow', 'glows',
    'god', 'goddess', 'gold', 'gone', 'gourds', 'granite', 'granted', 'grass',
    'grassy', 'grazed', 'great', 'grief', 'grinds', 'ground', 'grown', 'grows',
    'guard', 'guarded', 'guards', 'guilt', 'gulls', 'halt', 'hands', 'harmony',
    'haunted', 'heal', 'heard', 'heart', 'hearts', 'heather', 'heaven', 'heavens',
    'herds', 'hide', 'hides', 'hill', 'hillside', 'hilltop', 'hold', 'hollow',
    'hollowed', 'honey', 'hum', 'hums', 'hundred', 'hunter', 'hymn', 'impossible',
    'inhabited', 'inland', 'instead', 'iron', 'king', 'kingdom', 'kings', 'kneel',
    'knelt', 'knight', 'knotted', 'known', 'larks', 'leads', 'leaf', 'leaves',
    'legend', 'letters', 'lights', 'lilac', 'lined', 'lip', 'liquid', 'littered',
    'logs', 'lovers', 'luminous', 'made', 'marked', 'marks', 'maze', 'meadow',
    'melted', 'memory', 'mid', 'mimics', 'miners', 'mirror', 'mirrors', 'misleads',
    'mist', 'monk', 'monks', 'moon', 'moonlight', 'mother', 'moves', 'mud',
    'music', 'names', 'nest', 'night', 'nightly', 'noon', 'nowhere', 'oath',
    'oathbreakers', 'oats', 'ochre', 'ogham', 'opens', 'order', 'otherworld',
    'outlines', 'outwitted', 'overgrown', 'overnight', 'overrun', 'overtaken',
    'painted', 'pair', 'pass', 'pasture', 'patch', 'paths', 'patterns', 'pearls',
    'peat', 'perfect', 'perfectly', 'perform', 'petty', 'phantom', 'pilgrim',
    'pilgrimage', 'pilgrims', 'pit', 'plague', 'plain', 'plainland', 'plank',
    'planted', 'plow', 'pottery', 'prayer', 'preserved', 'priest', 'prophecy',
    'quarry', 'rain', 'rangers', 'ravens', 'reach', 'reachable', 'reached',
    'reaches', 'rearrange', 'rebuilt', 'reclaimed', 'reflection', 'reflections',
    'refuses', 'regrows', 'reignites', 'remain', 'remains', 'remnants', 'repeat',
    'return', 'riddled', 'ride', 'rises', 'roost', 'root', 'roots', 'rope', 'rot',
    'rows', 'ruled', 'rumored', 'runes', 'sacred', 'sacrifices', 'said', 'saint',
    'saints', 'salt', 'sand', 'sandbank', 'sandbar', 'sane', 'sang', 'sap', 'scar',
    'scattered', 'seems', 'seen', 'sentinel', 'separately', 'serpent', 'seven',
    'shadow', 'shadows', 'shakes', 'shape', 'shaped', 'shapes', 'shards', 'sheep',
    'shells', 'shepherd', 'shepherds', 'shows', 'silence', 'silently', 'silvered',
    'sing', 'siren', 'sisters', 'site', 'skeletal', 'skeleton', 'skulls', 'skyward',
    'slab', 'slate', 'sleepers', 'slick', 'slope', 'smells', 'smithy', 'smooth',
    'solid', 'solitary', 'solstice', 'song', 'speak', 'spearheads', 'spectral',
    'spilled', 'spiral', 'spirally', 'stack', 'stags', 'stained', 'stars', 'stays',
    'steep', 'stolen', 'storm', 'storms', 'strange', 'stranger', 'streaked',
    'strewn', 'strike', 'struck', 'studded', 'stump', 'submerged', 'summer',
    'sunken', 'surrounded', 'sways', 'swear', 'swept', 'syrup', 'taken', 'takes',
    'tall', 'taller', 'tangle', 'tangled', 'tastes', 'tears', 'tended', 'though',
    'thousand', 'three', 'thunder', 'time', 'toll', 'tolls', 'tools', 'toppled',
    'torch', 'trade', 'travelers', 'treasure', 'trunk', 'truth', 'tunnels', 'turned',
    'turns', 'twilight', 'twisted', 'two', 'uncut', 'underground', 'uneven',
    'unnaturally', 'unremembered', 'unseen', 'used', 'vale', 'valley', 'vanish',
    'vanished', 'veiled', 'visible', 'voice', 'voices', 'vows', 'wake', 'walk',
    'war', 'warnings', 'watched', 'weep', 'whale', 'wheat', 'whisper', 'whispers',
    'wild', 'wildflowers', 'witches', 'wolf', 'wolves', 'wrapped', 'year', 'years',
    'your'
}

# Filter out definitely not nouns
actual_nouns = uncovered_nouns - definitely_not_nouns

# Sort and display
actual_nouns_sorted = sorted(actual_nouns)
print(f"Found {len(actual_nouns_sorted)} uncovered nouns (filtered):\n")
for noun in actual_nouns_sorted:
    print(f"  {noun}")

