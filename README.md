# Banshee RPG

A procedural RPG game built with Python and Pygame featuring:

- Procedurally generated maps with Perlin noise
- Celtic calendar system
- Settlement system (villages, towns, cities) with vassal relationships
- Economy system with resource trading and caravan routes
- Fog of war and exploration mechanics
- Save/load game functionality

## Requirements

- Python 3.13+
- Pygame 2.6.1+

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install pygame
   ```

## Running the Game

```bash
./start.sh
```

Or directly:
```bash
python main.py
```

## Features

### Map Generation
- Procedural terrain generation using Perlin noise
- Multiple terrain types: grasslands, forests, hills, mountains, water
- Rivers and lakes
- Impassable borders

### Settlements
- **Villages**: Produce resources (lumber, fish and fowl, grain and livestock, ore)
- **Towns**: Collect resources from villages, produce trade goods
- **Cities**: Receive trade goods from vassal towns
- Vassal relationships create hierarchical structures

### Economy System
- Villages send resources to towns via caravans
- Towns accumulate resources and produce trade goods (100 of each resource = 1 trade good)
- Towns send trade goods to their liege cities (10 trade goods at a time)
- Resource management with automatic production and transfer

### Gameplay
- Explore procedurally generated maps
- Fog of war system
- Time-based movement (Celtic calendar)
- Save and load game progress

## Controls

- **Arrow Keys / WASD**: Move player
- **M**: Toggle map view
- **F**: Save/Load menu
- **Q**: Quit (with save option)
- **ESC**: Cancel prompts / Return to menu

## File Structure

- `main.py`: Main game loop and screen management
- `map_generator.py`: Procedural map generation
- `play_screen.py`: Main gameplay screen
- `settlements.py`: Settlement and economy system
- `caravan.py`: Caravan movement and trading
- `save_game.py`: Save/load functionality
- `celtic_calendar.py`: Time and calendar system

## License

[Add your license here]

