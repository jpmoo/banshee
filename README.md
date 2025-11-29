# Banshee RPG

**🎨 Completely vibe-coded with [Cursor](https://cursor.sh/) 🎨**

This entire project was built using Cursor, the AI-powered code editor. Every feature, every system, every line of code was developed through collaborative AI-assisted programming. From procedural map generation to the economy system, from tileset support to settlement management—it all came together through the magic of AI pair programming with Cursor.

---

A procedural, Celtic-inspired RPG game built with Python and Pygame. Explore procedurally generated worlds, trade resources, and manage settlements in a hierarchical economy system.

## Features

### Procedural World Generation
- **Perlin Noise Terrain**: Procedurally generated maps with realistic terrain distribution
- **Multiple Terrain Types**: Grasslands, forests, hills, forested hills, mountains, rivers, shallow water, and deep water
- **Natural Features**: Rivers, lakes, and impassable borders
- **Large Scale Maps**: Default 4000x1000 tile maps with customizable seeds for reproducibility

### Settlement System
- **Three-Tier Hierarchy**: 
  - **Villages**: Produce one of four resource types (lumber, fish and fowl, grain and livestock, ore)
  - **Towns**: Collect resources from villages, produce trade goods, and serve cities or operate independently
  - **Cities**: Rule over vassal towns and receive trade goods
- **Vassal Relationships**: Hierarchical structures with villages serving towns, and towns serving cities
- **Free Towns**: Independent towns that rule villages but serve no city

### Economy System
- **Resource Production**: Villages produce 10 units of their resource when spawning a caravan
- **Trade Goods**: Towns consume 100 units of each resource type to produce 1 trade good
- **Automatic Transfer**: Towns automatically send 10 trade goods to their liege cities
- **Caravan System**: 
  - Caravans travel from villages to towns carrying resources
  - Turn-based movement respecting terrain difficulty
  - Pathfinding with A* algorithm avoiding impassable terrain
  - Automatic return to villages after delivery

### Worldbuilding & Storytelling
- **Rich Settlement Descriptions**: Procedurally generated descriptions for cities, towns, and villages
- **Leader Biographies**: Unique leader biographies for each settlement
- **Terrain-Specific Templates**: Village descriptions tailored to terrain type (hills, water, grassland, forest)
- **Extensive Data Banks**: 
  - **Cities**: 147 tones, 140 flavors, 131 leader biographies
  - **Towns**: 262 tones, 248 flavors, 250 leader biographies
  - **Villages**: 215 templates per terrain type (860 total), 170 leader biographies, 443 village names
- **Interactive Display**: View detailed settlement information when visiting settlements
- **Scrollable Dialogs**: Settlement information displayed in scrollable dialogs with word-wrapping

### Visual Features
- **Customizable Tilesets**: Support for image-based tilesets (8x8, 16x16, 32x32, 64x64)
- **Automatic Scaling**: Tilesets automatically scaled to 32px display size
- **Multi-Layer Tiles**: Support for base and overlay layers (e.g., trees on grass)
- **Transparency Support**: Chroma key transparency for overlay layers
- **Color-Based Fallback**: Original color-based rendering available
- **Interactive Tile Selection**: Visual tool for mapping terrain types to tileset tiles

### Gameplay Systems
- **Fog of War**: Explore the map to reveal terrain
- **Line of Sight**: Realistic visibility system based on elevation and terrain blocking
- **Celtic Calendar**: Time-based system with months, days, and hours
- **Turn-Based Movement**: Movement costs vary by terrain type
- **Save/Load System**: Save game progress with settlement economy state
- **Map Management**: 
  - Save and load multiple maps
  - Delete maps with confirmation dialog
  - Automatic deletion of associated save files when deleting a map (with warning)

### User Interface
- **Status Panel**: Display settlement information and resources
- **Scrollable Content**: Status area supports scrolling for long descriptions
- **Command Terminal**: Terminal-style command input and message log
- **Map View**: Zoomed-out overview of explored areas
- **Settlement Interaction**: Click or visit settlements to view detailed information

## Requirements

- **Python**: 3.13 or higher
- **Pygame**: 2.6.1 or higher

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jpmoo/banshee.git
   cd banshee
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install pygame
   ```
   
   - `pygame`: Core game library

## Running the Game

### Quick Start
```bash
./start.sh
```

Or directly:
```bash
python main.py
```

### First Run
- You can skip this step, but worldbuilding content won't be generated

## Controls

### Movement
- **Arrow Keys / WASD**: Move player (N/S/E/W)
- **SPACE**: Pass a turn (advance time without moving)

### Navigation
- **M**: Toggle map view (zoomed-out overview)
- **Arrow Keys / WASD** (in map view): Scroll the overview map

### Game Management
- **F**: Save/Load menu
- **Q**: Quit (with options: Save and quit, Quit, or Cancel)
- **T**: Tileset selection
- **ESC**: Cancel prompts / Return to menu

### Settlement Interaction
- **Stand on a settlement**: Automatically displays settlement information in status panel
- **Arrow Keys / Mouse Wheel** (when viewing settlement): Scroll through settlement details

## File Structure

### Core Game Files
- `main.py`: Main game loop and screen management
- `play_screen.py`: Main gameplay screen with movement, exploration, and settlement interaction
- `map_generator.py`: Procedural map generation using Perlin noise
- `map_renderer.py`: Map rendering with tileset support
- `settlements.py`: Settlement classes and economy system
- `caravan.py`: Caravan movement and state management
- `celtic_calendar.py`: Time and calendar system
- `terrain.py`: Terrain types and properties
- `perlin_noise.py`: Perlin noise implementation for terrain generation

### Save/Load System
- `save_game.py`: Game state saving and loading
- `map_saver.py`: Map file saving and loading
- `save_list_screen.py`: Save game selection screen
- `map_list_screen.py`: Map selection screen

### UI Components
- `menu_screen.py`: Main menu
- `map_menu_screen.py`: Map generation/loading menu
- `title_screen.py`: Title screen with progress display
- `text_input.py`: Text input dialog
- `dialog.py`: Message dialog system
- `tileset_selection_screen.py`: In-game tileset selection

### Worldbuilding
- `worldbuilding.py`: Worldbuilding data generation system
- `data_cities.py`: City-level worldbuilding data (tones, flavors, titles, names, bios)
- `data_towns.py`: Town-level worldbuilding data (tones, flavors, titles, bios)
- `data_villages.py`: Village-level worldbuilding data (templates by terrain, flavors, titles, names, bios)
- `settlement_dialog.py`: Settlement information display dialog

### Tileset Tools
- `select_tileset_tiles.py`: Interactive tool for mapping terrain types to tileset tiles
- `select_tileset.sh`: Shell script to run the tileset selector
- `tilesets/`: Directory containing tileset images and JSON mappings

### Data Directories
- `maps/`: Saved map files
- `saves/`: Saved game files
- `tilesets/`: Tileset images and mappings

## Advanced Features

### Tileset Customization
1. Place your tileset PNG in the `tilesets/` directory
2. Run the tileset selector:
   ```bash
   ./select_tileset.sh
   ```
3. Select your tileset image
4. Use the interactive tool to map terrain types to tiles
5. Select the tileset in-game with the 'T' key

### Map Generation
- Maps can be generated with custom seeds for reproducibility
- Generated maps are automatically saved when accepted
- Maps can be loaded and regenerated

### Economy Details
- **Resource Types**: Lumber, Fish and Fowl, Grain and Livestock, Ore
- **Production**: Villages produce 10 units when a caravan spawns
- **Trade Good Creation**: Towns need 100 of each resource type
- **Transfer**: Towns send 10 trade goods to cities automatically
- **Caravan Limits**: Caravans stop spawning if a town has 1000+ units of a resource

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Attribution

When sharing or distributing this software, please include:
- The original repository URL: https://github.com/jpmoo/banshee
- This README file
- The LICENSE file

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Perlin noise implementation for procedural generation

- Built with [Pygame](https://www.pygame.org/)
- Perlin noise implementation for procedural generation
