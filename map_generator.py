"""
Map generation system for the RPG.
Generates maps using Perlin noise with elevation-based terrain classification.
"""
import random
import math
from collections import deque, Counter
from typing import List, Tuple, Set, Dict, Optional
from terrain import Terrain, TerrainType
from perlin_noise import PerlinNoise
from settlements import Settlement, SettlementType
from worldbuilding import generate_worldbuilding_data


class MapGenerator:
    """Generates procedural maps using Perlin noise and elevation thresholds."""
    
    def __init__(self, width: int, height: int, seed: int = None, progress_callback=None):
        """
        Initialize the map generator.
        
        Args:
            width: Map width in tiles
            height: Map height in tiles
            seed: Random seed for reproducible maps (optional)
            progress_callback: Function to call with (progress, message) where progress is 0.0-1.0
        """
        self.width = width
        self.height = height
        self.seed = seed
        self.progress_callback = progress_callback
        if seed is not None:
            random.seed(seed)
    
    def _update_progress(self, progress: float, message: str):
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def _debug_terrain_distribution(self, map_data: List[List[Terrain]], thresholds: Dict[str, float], stage: str = ""):
        """Print debug information about terrain distribution."""
        terrain_counts = Counter()
        for row in map_data:
            for terrain in row:
                terrain_counts[terrain.terrain_type] += 1
        
        total = sum(terrain_counts.values())
        print(f"\n=== Terrain Distribution {stage} ===")
        print(f"Thresholds: Deep={thresholds['deep_water']:.3f}, Shallow={thresholds['shallow_water']:.3f}, "
              f"Grass={thresholds['grassland']:.3f}, Hills={thresholds['hills']:.3f}")
        for terrain_type, count in terrain_counts.most_common():
            percentage = (count / total) * 100
            color = Terrain.TERRAIN_COLORS.get(terrain_type, (0, 0, 0))
            print(f"{terrain_type.value:15s}: {count:8d} ({percentage:5.2f}%) - RGB{color}")
        print("=" * 40 + "\n")
    
    def generate_elevation_map(self) -> List[List[float]]:
        """
        Generate elevation map using Perlin noise.
        
        Returns:
            2D list of elevation values (0.0 to 1.0)
        """
        self._update_progress(0.0, "Generating elevation map with Perlin noise...")
        noise = PerlinNoise(seed=self.seed)
        elevation_map = []
        
        # Scale factors for noise - adjusted for even larger, more coherent landmasses
        scale = 0.002  # Even smaller scale = even larger features (was 0.003)
        octaves = 8  # More octaves for smoother, more coherent transitions
        persistence = 0.7  # Higher persistence = more coherent, larger features (was 0.65)
        
        total_tiles = self.width * self.height
        processed = 0
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Generate noise value (approximately -1 to 1)
                noise_value = noise.octave_noise(x, y, octaves=octaves, 
                                                 persistence=persistence, scale=scale)
                # Normalize to 0.0 to 1.0
                elevation = (noise_value + 1.0) / 2.0
                # Apply a curve to create more mid-range values
                # Using a power < 1.0 compresses high values and expands low values
                # This creates more values in the middle range (grassland/hills)
                elevation = elevation ** 0.85  # Curve to favor mid-range elevations
                row.append(elevation)
                processed += 1
                if processed % 10000 == 0:
                    self._update_progress(0.05 * (processed / total_tiles), 
                                         f"Generating elevation map... {processed}/{total_tiles}")
            elevation_map.append(row)
        
        return elevation_map
    
    def add_ridge_line(self, elevation_map: List[List[float]]) -> List[List[float]]:
        """
        Add a tectonic ridge/mountain chain across the map.
        Creates a curved line that raises elevation.
        
        Args:
            elevation_map: Existing elevation map
            
        Returns:
            Modified elevation map with ridge
        """
        # Create a curved ridge line (sine wave pattern)
        ridge_width = self.width * 0.15  # Width of ridge influence
        ridge_amplitude = self.height * 0.2  # Vertical variation of ridge
        ridge_center_y = self.height / 2  # Center Y position
        
        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from ridge line
                # Ridge follows a sine wave pattern
                ridge_y = ridge_center_y + math.sin(x / (self.width / 4)) * ridge_amplitude
                distance_from_ridge = abs(y - ridge_y)
                
                # Add elevation boost near the ridge
                if distance_from_ridge < ridge_width:
                    # Gaussian falloff
                    influence = math.exp(-(distance_from_ridge ** 2) / (2 * (ridge_width / 3) ** 2))
                    elevation_boost = influence * 0.25  # Maximum boost of 0.25 (reduced from 0.4)
                    elevation_map[y][x] = min(1.0, elevation_map[y][x] + elevation_boost)
        
        return elevation_map
    
    def analyze_elevation_distribution(self, elevation_map: List[List[float]]) -> Dict[str, float]:
        """
        Analyze elevation distribution and return thresholds based on percentiles.
        Ensures we get a good mix of all terrain types.
        
        Args:
            elevation_map: 2D list of elevation values
            
        Returns:
            Dictionary with threshold values
        """
        # Flatten elevation map to list
        all_elevations = []
        for row in elevation_map:
            all_elevations.extend(row)
        
        # Sort for percentile calculation
        sorted_elevations = sorted(all_elevations)
        total = len(sorted_elevations)
        
        # Get min, max, and median to understand the range
        min_elevation = sorted_elevations[0]
        max_elevation = sorted_elevations[-1]
        median_elevation = sorted_elevations[total // 2]
        
        # Calculate thresholds to ensure we get all terrain types
        # Use more aggressive spacing to force mid-range terrain
        # Target distribution:
        # - ~40% deep ocean
        # - ~5% shallow water  
        # - ~40% grassland (increased)
        # - ~12% hills (decreased)
        # - ~3% mountains
        
        deep_water_threshold = sorted_elevations[int(total * 0.40)]
        shallow_water_threshold = sorted_elevations[int(total * 0.45)]
        grassland_threshold = sorted_elevations[int(total * 0.85)]  # 85th percentile (more grassland)
        hills_threshold = sorted_elevations[int(total * 0.97)]  # 97th percentile (fewer hills)
        
        # Force minimum spacing between thresholds to ensure all terrain types appear
        # This prevents thresholds from being too close together
        elevation_range = max_elevation - min_elevation
        
        # Ensure at least 5% of range between each threshold
        min_spacing = elevation_range * 0.05
        
        if shallow_water_threshold - deep_water_threshold < min_spacing:
            shallow_water_threshold = min(deep_water_threshold + min_spacing, max_elevation)
        if grassland_threshold - shallow_water_threshold < min_spacing * 2:
            grassland_threshold = min(shallow_water_threshold + min_spacing * 2, max_elevation)
        if hills_threshold - grassland_threshold < min_spacing:
            hills_threshold = min(grassland_threshold + min_spacing, max_elevation)
        
        # Clamp thresholds to valid range
        deep_water_threshold = max(min_elevation, min(deep_water_threshold, max_elevation))
        shallow_water_threshold = max(deep_water_threshold, min(shallow_water_threshold, max_elevation))
        grassland_threshold = max(shallow_water_threshold, min(grassland_threshold, max_elevation))
        hills_threshold = max(grassland_threshold, min(hills_threshold, max_elevation))
        
        thresholds = {
            'deep_water': deep_water_threshold,
            'shallow_water': shallow_water_threshold,
            'grassland': grassland_threshold,
            'hills': hills_threshold
        }
        
        return thresholds
    
    def apply_elevation_thresholds(self, elevation_map: List[List[float]], 
                                   thresholds: Dict[str, float] = None) -> List[List[Terrain]]:
        """
        Convert elevation map to terrain types based on thresholds.
        Uses either provided thresholds or calculates them from distribution.
        
        Args:
            elevation_map: 2D list of elevation values
            thresholds: Optional dictionary with threshold values. If None, uses defaults.
            
        Returns:
            2D list of Terrain objects
        """
        # Use provided thresholds or defaults
        if thresholds is None:
            thresholds = {
                'deep_water': 0.25,
                'shallow_water': 0.3,
                'grassland': 0.5,
                'hills': 0.65
            }
        
        map_data = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                elevation = elevation_map[y][x]
                
                if elevation < thresholds['deep_water']:
                    terrain_type = TerrainType.DEEP_WATER
                elif elevation < thresholds['shallow_water']:
                    terrain_type = TerrainType.SHALLOW_WATER
                elif elevation < thresholds['grassland']:
                    terrain_type = TerrainType.GRASSLAND
                elif elevation < thresholds['hills']:
                    terrain_type = TerrainType.HILLS
                else:
                    terrain_type = TerrainType.MOUNTAIN
                
                row.append(Terrain(terrain_type))
            map_data.append(row)
        
        return map_data
    
    def contour_coastlines(self, map_data: List[List[Terrain]]) -> List[List[Terrain]]:
        """
        Smooth and contour coastlines for more organic appearance.
        Applies smoothing specifically at water/land boundaries.
        
        Args:
            map_data: 2D list of Terrain objects
            
        Returns:
            Smoothed map data
        """
        new_map = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                current_terrain = map_data[y][x].terrain_type
                
                # Check if we're at a water/land boundary
                is_water = current_terrain in (TerrainType.DEEP_WATER, TerrainType.SHALLOW_WATER, TerrainType.RIVER)
                is_land = current_terrain in (TerrainType.GRASSLAND, TerrainType.HILLS, TerrainType.FORESTED_HILL, TerrainType.MOUNTAIN)
                
                # Count water and land neighbors
                water_neighbors = 0
                land_neighbors = 0
                shallow_water_neighbors = 0
                deep_water_neighbors = 0
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            neighbor_type = map_data[ny][nx].terrain_type
                            if neighbor_type in (TerrainType.DEEP_WATER, TerrainType.SHALLOW_WATER, TerrainType.RIVER):
                                water_neighbors += 1
                                if neighbor_type == TerrainType.SHALLOW_WATER:
                                    shallow_water_neighbors += 1
                                elif neighbor_type == TerrainType.DEEP_WATER:
                                    deep_water_neighbors += 1
                            elif neighbor_type in (TerrainType.GRASSLAND, TerrainType.HILLS, TerrainType.FORESTED_HILL, TerrainType.MOUNTAIN):
                                land_neighbors += 1
                
                # Apply coastline smoothing rules
                if is_water:
                    # If water tile has many land neighbors, consider making it shallow water
                    if land_neighbors >= 3 and current_terrain == TerrainType.DEEP_WATER:
                        row.append(Terrain(TerrainType.SHALLOW_WATER))
                    # If deep water has shallow water neighbors, might be shallow
                    elif shallow_water_neighbors >= 2 and current_terrain == TerrainType.DEEP_WATER:
                        row.append(Terrain(TerrainType.SHALLOW_WATER))
                    else:
                        row.append(Terrain(current_terrain))
                elif is_land:
                    # If land tile has many water neighbors, might be shallow water (beach)
                    if water_neighbors >= 4 and current_terrain == TerrainType.GRASSLAND:
                        row.append(Terrain(TerrainType.SHALLOW_WATER))
                    else:
                        row.append(Terrain(current_terrain))
                else:
                    row.append(Terrain(current_terrain))
            
            new_map.append(row)
        
        return new_map
    
    def generate(self) -> List[List[Terrain]]:
        """
        Generate a complete map using Perlin noise, elevation thresholds, 
        ridge lines, rivers, lakes, and forests.
        
        Returns:
            2D list of Terrain objects
        """
        self._update_progress(0.0, "Starting map generation...")
        elevation_map = self.generate_elevation_map()
        
        # Ridge line generation disabled
        # self._update_progress(0.15, "Adding tectonic ridge line...")
        # elevation_map = self.add_ridge_line(elevation_map)
        
        self._update_progress(0.20, "Analyzing elevation distribution...")
        # Analyze distribution and set thresholds based on percentiles
        thresholds = self.analyze_elevation_distribution(elevation_map)
        
        # Store thresholds for use in other methods
        self.elevation_thresholds = thresholds
        
        self._update_progress(0.25, "Applying elevation thresholds...")
        map_data = self.apply_elevation_thresholds(elevation_map, thresholds)
        
        # Debug: Print terrain distribution
        self._debug_terrain_distribution(map_data, thresholds)
        
        self._update_progress(0.35, "Contouring coastlines...")
        map_data = self.contour_coastlines(map_data)
        self._debug_terrain_distribution(map_data, thresholds, "After coastline contouring")
        
        # Apply one more smoothing pass for better coastlines
        self._update_progress(0.45, "Final coastline smoothing...")
        map_data = self.contour_coastlines(map_data)
        self._debug_terrain_distribution(map_data, thresholds, "After final coastline smoothing")
        
        # Generate rivers and lakes
        self._update_progress(0.50, "Generating rivers and lakes...")
        map_data, river_tiles, lake_tiles = self.generate_rivers_and_lakes(
            map_data, elevation_map
        )
        self._debug_terrain_distribution(map_data, thresholds, f"After rivers/lakes (rivers: {len(river_tiles)}, lakes: {len(lake_tiles)})")
        
        # self._update_progress(0.80, "Applying erosion...")
        # map_data = self.apply_erosion(map_data, elevation_map, river_tiles)
        # self._debug_terrain_distribution(map_data, thresholds, "After erosion")
        
        self._update_progress(0.85, "Adding forests...")
        map_data = self.add_forests(map_data, elevation_map, river_tiles, lake_tiles)
        self._debug_terrain_distribution(map_data, thresholds, "After forests")
        
        self._update_progress(0.95, "Adding impassable borders...")
        map_data = self.add_impassable_borders(map_data, elevation_map)
        self._debug_terrain_distribution(map_data, thresholds, "After borders (FINAL)")
        
        self._update_progress(0.98, "Placing settlements...")
        settlements = self.place_towns(map_data, river_tiles, lake_tiles)
        
        self._update_progress(0.99, "Placing cities...")
        cities = self.place_cities(map_data, river_tiles, lake_tiles, settlements)
        settlements.extend(cities)
        
        # Update town names for independent towns (not vassals to any city)
        for settlement in settlements:
            # Names are now assigned from worldbuilding data
            pass
        
        # Print final settlement counts
        town_count = sum(1 for s in settlements if s.settlement_type == SettlementType.TOWN)
        village_count = sum(1 for s in settlements if s.settlement_type == SettlementType.VILLAGE)
        city_count = len(cities)
        total_settlements = len(settlements)
        print(f"Final settlement counts: {city_count} cities, {town_count} towns, {village_count} villages (total: {total_settlements} settlements)")
        
        # Generate worldbuilding data for all settlements
        self._update_progress(0.95, "Generating worldbuilding data...")
        self.worldbuilding_data = generate_worldbuilding_data(settlements, seed=self.seed, map_data=map_data)
        
        # Assign settlement names from worldbuilding data (extract from leader names)
        self._assign_settlement_names_from_worldbuilding(settlements)
        
        self._update_progress(1.0, "Map generation complete!")
        
        # Store settlements for later access
        self.settlements = settlements
        
        return map_data
    
    def find_river_sources(self, elevation_map: List[List[float]], 
                          num_sources: int = None) -> List[Tuple[int, int]]:
        """
        Find mountain peaks to use as river sources.
        Only selects from the lowest mountain elevations (not the highest peaks).
        
        Args:
            elevation_map: 2D list of elevation values
            num_sources: Number of sources to pick (None = auto based on map size)
            
        Returns:
            List of (x, y) coordinates for river sources
        """
        sources = []
        # Use hills threshold as mountain peak threshold (mountains are above hills)
        peak_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.65)
        
        # Find all mountain peaks with their elevations
        peaks_with_elevation = []
        for y in range(self.height):
            for x in range(self.width):
                elevation = elevation_map[y][x]
                if elevation > peak_threshold:
                    peaks_with_elevation.append((x, y, elevation))
        
        if len(peaks_with_elevation) == 0:
            return sources
        
        # Sort by elevation (lowest first)
        peaks_with_elevation.sort(key=lambda p: p[2])
        
        # Only use the lowest 40% of mountain elevations
        # This ensures rivers start in lower mountains, not the highest peaks
        lowest_portion = int(len(peaks_with_elevation) * 0.4)
        lowest_peaks = peaks_with_elevation[:max(1, lowest_portion)]
        
        # Extract just the coordinates from the lowest peaks
        lowest_peak_coords = [(x, y) for x, y, _ in lowest_peaks]
        
        # Randomly select sources from the lowest mountain elevations
        if num_sources is None:
            # Auto-calculate: roughly 1 source per 2000 tiles (many more rivers)
            num_sources = max(20, min(len(lowest_peak_coords), (self.width * self.height) // 2000))
        
        if len(lowest_peak_coords) > 0:
            sources = random.sample(lowest_peak_coords, min(num_sources, len(lowest_peak_coords)))
        
        return sources
    
    def find_hills_sources(self, elevation_map: List[List[float]],
                          map_data: List[List[Terrain]] = None,
                          num_sources: int = None) -> List[Tuple[int, int]]:
        """
        Find hills locations to use as river sources.
        
        Args:
            elevation_map: 2D list of elevation values
            map_data: Current map data (optional)
            num_sources: Number of sources to pick (None = auto based on map size)
            
        Returns:
            List of (x, y) coordinates for river sources in hills
        """
        sources = []
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
        
        # Find all hills locations (elevation between grassland and hills threshold)
        hills_locations = []
        for y in range(self.height):
            for x in range(self.width):
                elevation = elevation_map[y][x]
                # Check if in hills elevation range
                if grassland_threshold <= elevation < hills_threshold:
                    # Also check terrain type if available
                    if map_data:
                        terrain_type = map_data[y][x].terrain_type
                        if terrain_type in (TerrainType.HILLS, TerrainType.FORESTED_HILL):
                            hills_locations.append((x, y))
                    else:
                        hills_locations.append((x, y))
        
        # Randomly select sources from hills
        if num_sources is None:
            # Auto-calculate: roughly 1 source per 4000 tiles
            num_sources = max(10, min(len(hills_locations), (self.width * self.height) // 4000))
        
        if len(hills_locations) > 0:
            sources = random.sample(hills_locations, min(num_sources, len(hills_locations)))
        
        return sources
    
    def find_lake_sources(self, lake_tiles: Set[Tuple[int, int]], 
                         elevation_map: List[List[float]],
                         map_data: List[List[Terrain]] = None,
                         num_sources: int = None) -> List[Tuple[int, int]]:
        """
        Find lakes in hills that can serve as river sources.
        
        Args:
            lake_tiles: Set of lake tile coordinates
            elevation_map: 2D list of elevation values
            map_data: Current map data (optional)
            num_sources: Number of lake sources to pick (None = auto based on number of lakes)
            
        Returns:
            List of (x, y) coordinates for lake sources (edges of lakes in hills)
        """
        sources = []
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
        
        # Find lakes that are in hills (elevation between grassland and hills threshold)
        hills_lakes = []
        for x, y in lake_tiles:
            if 0 <= x < self.width and 0 <= y < self.height:
                elevation = elevation_map[y][x]
                # Check if lake is in hills elevation range
                if grassland_threshold <= elevation < hills_threshold:
                    # Find edge tiles of the lake (tiles with land neighbors)
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                # Check if neighbor is not a lake (edge of lake)
                                if (nx, ny) not in lake_tiles:
                                    # This is an edge tile - potential source
                                    neighbor_elevation = elevation_map[ny][nx]
                                    # Only if neighbor is at similar or higher elevation (not a deep drop)
                                    if neighbor_elevation >= elevation - 0.05:
                                        hills_lakes.append((x, y))
                                        break
                        else:
                            continue
                        break
        
        # Remove duplicates
        hills_lakes = list(set(hills_lakes))
        
        # Randomly select sources from hills lakes
        if num_sources is None:
            # Auto-calculate: roughly 1 source per 2 hills lakes (more sources from lakes)
            num_sources = max(5, len(hills_lakes) // 2)
        
        if len(hills_lakes) > 0:
            sources = random.sample(hills_lakes, min(num_sources, len(hills_lakes)))
        
        return sources
    
    def compute_flow_direction(self, elevation_map: List[List[float]]) -> List[List[Tuple[int, int]]]:
        """
        Compute D8 flow direction for each tile.
        Returns the direction (dx, dy) of steepest downward slope.
        
        Args:
            elevation_map: 2D list of elevation values
            
        Returns:
            2D list of (dx, dy) tuples representing flow direction, or (0, 0) if no flow
        """
        flow_direction = [[(0, 0)] * self.width for _ in range(self.height)]
        
        # D8 directions: N, NE, E, SE, S, SW, W, NW
        # Diagonal distances are sqrt(2) times longer, so we need to account for that
        directions = [
            (0, -1),   # N
            (1, -1),   # NE
            (1, 0),    # E
            (1, 1),    # SE
            (0, 1),    # S
            (-1, 1),   # SW
            (-1, 0),   # W
            (-1, -1),  # NW
        ]
        # Distance factors: 1.0 for cardinal, sqrt(2) for diagonal
        distance_factors = [1.0, 1.414, 1.0, 1.414, 1.0, 1.414, 1.0, 1.414]
        
        for y in range(self.height):
            for x in range(self.width):
                current_elevation = elevation_map[y][x]
                best_direction = (0, 0)
                steepest_slope = 0.0
                
                # Check all 8 directions
                for i, (dx, dy) in enumerate(directions):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        neighbor_elevation = elevation_map[ny][nx]
                        if neighbor_elevation < current_elevation:
                            # Calculate slope (drop per unit distance)
                            drop = current_elevation - neighbor_elevation
                            distance = distance_factors[i]
                            slope = drop / distance
                            
                            if slope > steepest_slope:
                                steepest_slope = slope
                                best_direction = (dx, dy)
                
                flow_direction[y][x] = best_direction
        
        return flow_direction
    
    def compute_flow_accumulation(self, flow_direction: List[List[Tuple[int, int]]],
                                 sources: List[Tuple[int, int]],
                                 elevation_map: List[List[float]] = None) -> List[List[int]]:
        """
        Compute flow accumulation map using D8 flow directions.
        Counts how many upstream cells flow into each cell.
        
        Args:
            flow_direction: 2D list of (dx, dy) flow directions
            sources: List of (x, y) source coordinates
            
        Returns:
            2D list of flow accumulation values
        """
        # Initialize accumulation map
        accumulation = [[0] * self.width for _ in range(self.height)]
        
        # For each source, trace downstream and accumulate flow
        for source_x, source_y in sources:
            x, y = source_x, source_y
            visited = set()
            path = []
            
            # Trace downstream until we hit sea level or no flow direction
            max_iterations = self.width * self.height
            iterations = 0
            
            while iterations < max_iterations:
                if (x, y) in visited:
                    break  # Circular path
                visited.add((x, y))
                path.append((x, y))
                
                dx, dy = flow_direction[y][x]
                if dx == 0 and dy == 0:
                    break  # No flow direction (sea level or depression)
                
                x += dx
                y += dy
                
                if not (0 <= x < self.width and 0 <= y < self.height):
                    break
                
                iterations += 1
            
            # Accumulate flow along the path
            for px, py in path:
                accumulation[py][px] += 1
        
        return accumulation
    
    def find_nearest_coast(self, x: int, y: int, elevation_map: List[List[float]],
                          shallow_water_threshold: float, max_search: int = 100) -> Tuple[int, int]:
        """
        Find the nearest coastal tile (shallow water) from a given position.
        Uses a simple search to find the closest water.
        
        Args:
            x, y: Starting coordinates
            elevation_map: 2D list of elevation values
            shallow_water_threshold: Elevation threshold for shallow water
            max_search: Maximum search radius
            
        Returns:
            (target_x, target_y) of nearest coast, or (x, y) if not found
        """
        # Simple BFS to find nearest coast
        queue = deque([(x, y, 0)])
        visited = {(x, y)}
        
        while queue:
            cx, cy, dist = queue.popleft()
            
            if dist > max_search:
                break
            
            # Check if this is a coast tile
            if elevation_map[cy][cx] < shallow_water_threshold:
                return (cx, cy)
            
            # Check neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny, dist + 1))
        
        # If no coast found, return original position
        return (x, y)
    
    def flow_river(self, start_x: int, start_y: int, 
                   elevation_map: List[List[float]],
                   flow_direction: List[List[Tuple[int, int]]],
                   river_flow: Dict[Tuple[int, int], int],
                   river_network: Dict[Tuple[int, int], int] = None,
                   existing_lakes: Set[Tuple[int, int]] = None,
                   tributary_count: int = 1) -> Tuple[Set[Tuple[int, int]], bool, Tuple[int, int]]:
        """
        Flow a river from source. Rivers start in mountains, flow toward hills, try to reach coast.
        Rivers try to join with other rivers. Single-strand rivers end in hills in small lakes.
        Rivers with 3+ tributaries have a very good chance of reaching the ocean.
        
        Args:
            start_x, start_y: Starting coordinates (in mountains)
            elevation_map: 2D list of elevation values
            flow_direction: 2D list of (dx, dy) flow directions
            river_flow: Dictionary tracking flow volume at each tile
            river_network: Dictionary tracking tributary count at each tile (tile -> count)
            existing_lakes: Set of existing lake tile coordinates
            tributary_count: Number of tributaries that have merged into this river (starts at 1)
            
        Returns:
            Tuple of (river_path, reached_coast, termination_point)
            - river_path: Set of (x, y) coordinates that the river flows through
            - reached_coast: True if river reached shallow water (ocean)
            - termination_point: (x, y) where river ended, or None if reached coast
        """
        if existing_lakes is None:
            existing_lakes = set()
        if river_network is None:
            river_network = {}
        
        river_path = set()
        x, y = start_x, start_y
        shallow_water_threshold = getattr(self, 'elevation_thresholds', {}).get('shallow_water', 0.3)
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
        
        max_iterations = min(5000, int((self.width + self.height) * 1.5))
        iterations = 0
        
        # Initialize flow at starting point
        river_flow[(x, y)] = river_flow.get((x, y), 0) + 1
        river_network[(x, y)] = tributary_count
        
        # Determine river goal based on tributary count:
        # - Single-strand (tributary_count = 1): some can reach coast, others end in lakes
        # - 2+ tributaries: ALWAYS reach coast (100% chance)
        if tributary_count >= 2:
            # 2+ tributaries ALWAYS target coast
            river_goal = 'coast'
            coast_target = self.find_nearest_coast(start_x, start_y, elevation_map, shallow_water_threshold, max_search=500)
            coast_seeking_active = False
        else:
            # Single-strand: 30% chance to try for coast, 70% end in lakes
            if random.random() < 0.3:  # 30% of single-strand rivers try for coast
                river_goal = 'coast'
                coast_target = self.find_nearest_coast(start_x, start_y, elevation_map, shallow_water_threshold, max_search=500)
                coast_seeking_active = False
            else:
                river_goal = 'lake'  # Will create lake in hills
                coast_target = None
                coast_seeking_active = False
        
        found_lake = False
        reached_coast = False
        last_direction = None
        no_progress_count = 0
        visited_positions = set()
        termination_point = None
        
        # Track terrain phase: 'mountain' -> 'hills' -> 'grassland'
        terrain_phase = 'mountain'  # Start in mountains
        iterations_in_hills = 0
        iterations_in_grassland = 0
        iterations_since_last_join_attempt = 0
        
        while iterations < max_iterations:
            # Check for loops
            if (x, y) in visited_positions:
                break
            
            river_path.add((x, y))
            visited_positions.add((x, y))
            if len(visited_positions) > 50:
                visited_positions.remove(min(visited_positions, key=lambda p: (p[0], p[1])))
            
            current_elevation = elevation_map[y][x]
            previous_position = (x, y)
            
            # Determine current terrain phase based on elevation
            if current_elevation >= hills_threshold:
                current_phase = 'mountain'
            elif current_elevation >= grassland_threshold:
                current_phase = 'hills'
            elif current_elevation >= shallow_water_threshold:
                current_phase = 'grassland'
            else:
                current_phase = 'water'
            
            # Update terrain phase tracking
            if current_phase == 'grassland' and terrain_phase != 'grassland':
                # Just entered grasslands - start trying to join
                terrain_phase = 'grassland'
                iterations_in_grassland = 0
            elif current_phase == 'hills' and terrain_phase == 'mountain':
                # Transitioned from mountain to hills
                terrain_phase = 'hills'
                iterations_in_hills = 0
            elif current_phase == 'hills':
                iterations_in_hills += 1
            elif current_phase == 'grassland':
                iterations_in_grassland += 1
            
            # Help rivers exit hills - if in hills for a while, prioritize moving toward grasslands
            if terrain_phase == 'hills' and iterations_in_hills > 100:
                # After 100 iterations in hills, start prioritizing lower elevations to exit
                # This helps rivers flow toward grasslands
                pass  # This will be handled in direction selection below
            
            # If we've been in grasslands for a while without joining and can't form 2+ tributaries, give up
            # BUT don't do this if we're coast-bound - coast-bound rivers should keep going
            if terrain_phase == 'grassland' and tributary_count < 2 and river_goal != 'coast':
                if iterations_in_grassland > 300:  # Been in grasslands for 300+ iterations
                    # Check if there are any nearby rivers we could still join
                    nearby_river_found = False
                    for dy2 in range(-30, 31):
                        for dx2 in range(-30, 31):
                            if dx2 == 0 and dy2 == 0:
                                continue
                            nx2, ny2 = x + dx2, y + dy2
                            if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                                if (nx2, ny2) in river_network and (nx2, ny2) not in river_path:
                                    nearby_river_found = True
                                    break
                        if nearby_river_found:
                            break
                    
                    if not nearby_river_found:
                        # No nearby rivers, give up and create a lake
                        river_goal = 'lake'
                        coast_target = None
                        coast_seeking_active = False
            
            # Check if we've merged with another river (tributary count increases)
            if (x, y) in river_network and river_network[(x, y)] > tributary_count:
                # We've merged! Update our tributary count
                tributary_count = river_network[(x, y)]
                iterations_since_last_join_attempt = 0
                # If we now have 2+ tributaries, ALWAYS switch to coast goal
                if tributary_count >= 2:
                    river_goal = 'coast'
                    coast_target = self.find_nearest_coast(x, y, elevation_map, shallow_water_threshold, max_search=500)
                    coast_seeking_active = False
            else:
                iterations_since_last_join_attempt += 1
            
            # Check termination conditions
            if river_goal == 'coast':
                # Coast-bound rivers should NOT terminate in lakes - keep flowing toward coast
                # Check if we've reached shallow water (ocean)
                if current_elevation < shallow_water_threshold:
                    water_neighbors = 0
                    for dy2 in [-1, 0, 1]:
                        for dx2 in [-1, 0, 1]:
                            if dx2 == 0 and dy2 == 0:
                                continue
                            nx2, ny2 = x + dx2, y + dy2
                            if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                                neighbor_elevation = elevation_map[ny2][nx2]
                                if neighbor_elevation < shallow_water_threshold:
                                    water_neighbors += 1
                    if water_neighbors >= 2:
                        reached_coast = True
                        break
                # Don't check for depressions if coast-bound - keep flowing
            elif river_goal == 'lake':
                # Check if we've reached an existing lake
                if (x, y) in existing_lakes:
                    found_lake = True
                    termination_point = (x, y)
                    break
                
                # Check if we're in a depression suitable for a lake
                # For single-strand rivers, prefer hills
                is_depression = True
                for dy2 in [-1, 0, 1]:
                    for dx2 in [-1, 0, 1]:
                        if dx2 == 0 and dy2 == 0:
                            continue
                        nx2, ny2 = x + dx2, y + dy2
                        if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                            neighbor_elevation = elevation_map[ny2][nx2]
                            if neighbor_elevation < current_elevation - 0.01:
                                is_depression = False
                                break
                    if not is_depression:
                        break
                
                # Create lake if in depression - rivers form small lakes when they hit depressions
                # BUT: All rivers in grasslands ignore depressions and keep flowing
                # Single-strand rivers: prefer hills (elevation between grassland and hills threshold)
                # Other rivers: can end in hills, forested hills, forests, but NOT grasslands
                if is_depression and iterations > 30:  # Reduced from 50 to form lakes sooner
                    # Check elevation range
                    in_hills = grassland_threshold <= current_elevation < hills_threshold
                    in_grassland = current_elevation >= shallow_water_threshold and current_elevation < grassland_threshold
                    
                    # ALL rivers in grasslands ignore depressions - keep flowing
                    if in_grassland:
                        # Don't terminate in grasslands - keep flowing toward coast or to join
                        pass
                    # Single-strand: must be in hills, but only after trying to exit
                    elif tributary_count == 1:
                        if not in_hills:
                            # Continue flowing if not in hills yet
                            pass
                        elif iterations_in_hills < 150:
                            # Don't terminate in hills too early - give river a chance to exit
                            pass
                        else:
                            # Check depression size
                            depression_size = 0
                            has_mountain_nearby = False
                            for dy2 in range(-5, 6):
                                for dx2 in range(-5, 6):
                                    nx2, ny2 = x + dx2, y + dy2
                                    if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                                        if abs(elevation_map[ny2][nx2] - current_elevation) < 0.02:
                                            depression_size += 1
                                        if elevation_map[ny2][nx2] >= hills_threshold:
                                            has_mountain_nearby = True
                            
                            if not has_mountain_nearby and 10 <= depression_size <= 200:
                                found_lake = True
                                termination_point = (x, y)
                                break
                    else:
                        # Multi-tributary: can end in hills, but NOT grasslands
                        if in_hills and current_elevation < hills_threshold * 0.9:
                            depression_size = 0
                            has_mountain_nearby = False
                            for dy2 in range(-5, 6):
                                for dx2 in range(-5, 6):
                                    nx2, ny2 = x + dx2, y + dy2
                                    if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                                        if abs(elevation_map[ny2][nx2] - current_elevation) < 0.02:
                                            depression_size += 1
                                        if elevation_map[ny2][nx2] >= hills_threshold:
                                            has_mountain_nearby = True
                            
                            if not has_mountain_nearby and 10 <= depression_size <= 200:
                                found_lake = True
                                termination_point = (x, y)
                                break
                
                # Also check if we should terminate naturally (after flowing enough)
                if iterations > 200:
                    if random.random() < 0.02:  # 2% chance per iteration after 200
                        termination_point = (x, y)
                        break
            
            # Activate coast-seeking for coast-bound rivers (activate much earlier)
            if river_goal == 'coast' and coast_target:
                distance_to_coast = abs(x - coast_target[0]) + abs(y - coast_target[1])
                # Activate coast-seeking much earlier - after 100 iterations or when within 400 tiles
                if distance_to_coast < 400 or iterations > 100:
                    coast_seeking_active = True
            else:
                distance_to_coast = 999999
            
            # Find best direction with meandering and river merging
            primary_dx, primary_dy = flow_direction[y][x]
            
            # Collect all valid paths (downward in mountains/hills, more flexible in grasslands)
            all_valid_paths = []
            all_downward_paths = []
            best_slope = 0.0
            best_dir = None
            best_dir_with_coast = None
            best_coast_score = -999
            best_dir_toward_river = None
            best_river_score = -999
            
            # Look for nearby rivers to merge with
            nearby_river = None
            min_river_dist = 30  # Look for rivers within 30 tiles
            
            for dy2 in [-1, 0, 1]:
                for dx2 in [-1, 0, 1]:
                    if dx2 == 0 and dy2 == 0:
                        continue
                    nx2, ny2 = x + dx2, y + dy2
                    if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                        neighbor_elevation = elevation_map[ny2][nx2]
                        
                        # Check for nearby rivers to merge with
                        if (nx2, ny2) in river_network and (nx2, ny2) not in river_path:
                            dist = abs(nx2 - x) + abs(ny2 - y)
                            if dist < min_river_dist:
                                min_river_dist = dist
                                nearby_river = (nx2, ny2)
                        
                        # In mountains: only allow downward movement
                        # In hills and grasslands: allow slight elevation increases to join rivers
                        elevation_allowed = False
                        if terrain_phase == 'mountain':
                            # Strictly downward in mountains
                            if neighbor_elevation < current_elevation:
                                elevation_allowed = True
                        elif terrain_phase == 'hills':
                            # In hills: allow slight increases if joining a river
                            if neighbor_elevation < current_elevation:
                                elevation_allowed = True
                            elif nearby_river and neighbor_elevation <= current_elevation + 0.03:
                                # Allow small elevation increase to join river in hills
                                elevation_allowed = True
                        elif terrain_phase == 'grassland':
                            # In grasslands: allow slight increases if joining a river
                            if neighbor_elevation < current_elevation:
                                elevation_allowed = True
                            elif nearby_river and neighbor_elevation <= current_elevation + 0.05:
                                # Allow small elevation increase to join river
                                elevation_allowed = True
                        
                        if elevation_allowed:
                            drop = current_elevation - neighbor_elevation
                            if dx2 != 0 and dy2 != 0:
                                slope = drop / 1.414
                            else:
                                slope = drop
                            
                            all_valid_paths.append(((dx2, dy2), slope))
                            
                            if neighbor_elevation < current_elevation:
                                all_downward_paths.append(((dx2, dy2), slope))
                            if slope > best_slope:
                                best_slope = slope
                                best_dir = (dx2, dy2)
                            
                            # River merging: prefer directions toward nearby rivers (in hills and grasslands)
                            if nearby_river:
                                river_dist = abs((x + dx2) - nearby_river[0]) + abs((y + dy2) - nearby_river[1])
                                river_score = min_river_dist - river_dist
                                # Boost score if moving toward river
                                if neighbor_elevation <= current_elevation:
                                    river_score += (current_elevation - neighbor_elevation) * 5
                                elif terrain_phase in ('hills', 'grassland'):
                                    # In hills and grasslands, allow slight uphill to join
                                    river_score += 2.0
                                
                                if river_score > best_river_score:
                                    best_river_score = river_score
                                    best_dir_toward_river = (dx2, dy2)
                        
                        # Coast-seeking
                        if coast_seeking_active and neighbor_elevation <= current_elevation:
                            new_dist_to_coast = abs((x + dx2) - coast_target[0]) + abs((y + dy2) - coast_target[1])
                            coast_score = distance_to_coast - new_dist_to_coast
                            coast_score += (current_elevation - neighbor_elevation) * 10
                            if coast_score > best_coast_score:
                                best_coast_score = coast_score
                                best_dir_with_coast = (dx2, dy2)
            
                        # Help rivers exit hills - boost directions that lead toward grasslands
                        # (This is handled by boosting the slope in the path selection below)
            
            # Choose direction: prioritize merging in hills and grasslands, then coast, then meandering
            if terrain_phase in ('hills', 'grassland') and best_dir_toward_river and best_river_score > 0:
                # In hills and grasslands, prioritize joining rivers (70% chance if good path exists)
                if random.random() < 0.7:
                    dx, dy = best_dir_toward_river
                elif best_dir:
                    dx, dy = best_dir
                else:
                    dx, dy = best_dir_toward_river
            elif best_dir_toward_river and best_river_score > 2:
                # Good opportunity to merge (50% chance if good path exists, even in mountains)
                if random.random() < 0.5:
                    dx, dy = best_dir_toward_river
                elif best_dir:
                    dx, dy = best_dir
                else:
                    dx, dy = best_dir_toward_river
            elif river_goal == 'coast' and coast_seeking_active and best_dir_with_coast:
                # Coast-bound rivers strongly prioritize coast direction
                if best_dir_with_coast == best_dir or best_coast_score > 0:
                    dx, dy = best_dir_with_coast
                elif best_dir:
                    # 80% chance to choose coast direction when coast-seeking
                    if random.random() < 0.8:
                        dx, dy = best_dir_with_coast
                    else:
                        dx, dy = best_dir
                else:
                    dx, dy = best_dir_with_coast
            elif all_valid_paths:
                # Meandering logic: prefer paths that create curves
                # Also boost paths that lead toward grasslands if in hills
                meander_paths = []
                for path_dir, slope in all_valid_paths:
                    meander_score = slope
                    
                    # If in hills and this path leads toward grasslands, boost it
                    if terrain_phase == 'hills' and iterations_in_hills > 100:
                        # Check if this direction leads toward grassland elevation
                        nx2, ny2 = x + path_dir[0], y + path_dir[1]
                        if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                            neighbor_elev = elevation_map[ny2][nx2]
                            if neighbor_elev < grassland_threshold and neighbor_elev < current_elevation:
                                # This path leads toward grasslands - boost it
                                meander_score = slope * 1.4
                    
                    # Strong boost for perpendicular directions
                    if last_direction:
                        dot_product = path_dir[0] * last_direction[0] + path_dir[1] * last_direction[1]
                        if abs(dot_product) < 0.3:  # Very perpendicular
                            meander_score *= 3.0  # Strong boost for meandering
                        elif abs(dot_product) < 0.6:
                            meander_score *= 2.0
                        elif abs(dot_product) < 0.8:
                            meander_score *= 1.4
                        if abs(dot_product) > 0.9:  # Going straight
                            meander_score *= 0.5
                    
                    meander_paths.append((path_dir, meander_score, slope))
                
                meander_paths.sort(key=lambda p: p[1], reverse=True)
                
                # Weighted random from top paths
                top_paths = meander_paths[:min(4, len(meander_paths))]
                if len(top_paths) > 1:
                    total_score = sum(p[1] for p in top_paths)
                    rand_val = random.random() * total_score
                    cumulative = 0
                    for path_dir, meander_score, slope in top_paths:
                        cumulative += meander_score
                        if rand_val <= cumulative:
                            if slope > 0.005:
                                dx, dy = path_dir
                                break
                    else:
                        dx, dy = top_paths[0][0]
                else:
                    dx, dy = top_paths[0][0]
            elif primary_dx != 0 or primary_dy != 0:
                dx, dy = primary_dx, primary_dy
            else:
                # No downward path - try to continue toward goal
                if current_elevation < shallow_water_threshold * 1.2 or coast_seeking_active:
                    best_water_dir = None
                    best_water_elevation = current_elevation
                    best_water_coast_dist = distance_to_coast
                    
                    for dy2 in [-1, 0, 1]:
                        for dx2 in [-1, 0, 1]:
                            if dx2 == 0 and dy2 == 0:
                                continue
                            nx2, ny2 = x + dx2, y + dy2
                            if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                                neighbor_elevation = elevation_map[ny2][nx2]
                                if coast_target:
                                    new_coast_dist = abs(nx2 - coast_target[0]) + abs(ny2 - coast_target[1])
                                else:
                                    new_coast_dist = 999999
                                
                                if (neighbor_elevation < best_water_elevation or 
                                    (neighbor_elevation <= best_water_elevation + 0.01 and new_coast_dist < best_water_coast_dist)):
                                    best_water_elevation = neighbor_elevation
                                    best_water_coast_dist = new_coast_dist
                                    best_water_dir = (dx2, dy2)
                    
                    if best_water_dir:
                        dx, dy = best_water_dir
                    else:
                        termination_point = (x, y)
                        break
                else:
                    termination_point = (x, y)
                    break
            
            # Additional meandering: sometimes override for wider curves (only in grasslands)
            if terrain_phase == 'grassland' and iterations > 5 and random.random() < 0.3:  # 30% chance for extra meandering in grasslands
                alternative_meander_paths = []
                for dy2 in [-1, 0, 1]:
                    for dx2 in [-1, 0, 1]:
                        if dx2 == 0 and dy2 == 0:
                            continue
                        nx2, ny2 = x + dx2, y + dy2
                        if 0 <= nx2 < self.width and 0 <= ny2 < self.height:
                            neighbor_elevation = elevation_map[ny2][nx2]
                            # In grasslands, allow slight elevation increases for meandering
                            if neighbor_elevation < current_elevation or (neighbor_elevation <= current_elevation + 0.03):
                                if dx2 != 0 and dy2 != 0:
                                    slope = (current_elevation - neighbor_elevation) / 1.414
                                else:
                                    slope = current_elevation - neighbor_elevation
                                
                                meander_boost = 1.0
                                if last_direction:
                                    dot_product = dx2 * last_direction[0] + dy2 * last_direction[1]
                                    if abs(dot_product) < 0.2:
                                        meander_boost = 4.0  # Very strong for perpendicular
                                    elif abs(dot_product) < 0.5:
                                        meander_boost = 2.5
                                    elif abs(dot_product) < 0.7:
                                        meander_boost = 1.8
                                    if abs(dot_product) > 0.85:
                                        meander_boost = 0.2
                                
                                if slope > 0.005:
                                    alternative_meander_paths.append(((dx2, dy2), slope * meander_boost, slope))
                
                if alternative_meander_paths:
                    alternative_meander_paths.sort(key=lambda p: p[1], reverse=True)
                    top_alternatives = alternative_meander_paths[:min(3, len(alternative_meander_paths))]
                    if len(top_alternatives) > 1:
                        total_boosted = sum(p[1] for p in top_alternatives)
                        rand_val = random.random() * total_boosted
                        cumulative = 0
                        for path_dir, boosted_score, slope in top_alternatives:
                            cumulative += boosted_score
                            if rand_val <= cumulative:
                                dx, dy = path_dir
                                break
                    elif top_alternatives:
                        dx, dy = top_alternatives[0][0]
            
            # Move to next tile
            last_direction = (dx, dy)
            x += dx
            y += dy
            
            if not (0 <= x < self.width and 0 <= y < self.height):
                termination_point = (x - dx, y - dy)
                break
            
            # Check if we merged with another river
            if (x, y) in river_network and (x, y) not in river_path:
                # Merge! Increase tributary count
                river_network[(x, y)] = river_network[(x, y)] + tributary_count
                tributary_count = river_network[(x, y)]
                # If we now have 3+ tributaries, switch to coast goal
                if tributary_count >= 2 and river_goal != 'coast':
                    # 2+ tributaries ALWAYS target coast
                    river_goal = 'coast'
                    coast_target = self.find_nearest_coast(x, y, elevation_map, shallow_water_threshold, max_search=500)
                    coast_seeking_active = False
            
            # Track progress
            if (x, y) == previous_position:
                no_progress_count += 1
                if no_progress_count >= 10:
                    termination_point = (x, y)
                    break
            else:
                no_progress_count = 0
                previous_position = (x, y)
            
            # Update flow and network
            river_flow[(x, y)] = river_flow.get((x, y), 0) + 1
            river_network[(x, y)] = max(river_network.get((x, y), 0), tributary_count)
            
            iterations += 1
        
        if not termination_point and not reached_coast:
            termination_point = (x, y)
        
        return river_path, reached_coast, termination_point
    
    def fill_depression(self, x: int, y: int, 
                       elevation_map: List[List[float]],
                       visited: Set[Tuple[int, int]],
                       map_data: List[List[Terrain]] = None) -> Set[Tuple[int, int]]:
        """
        Fill a depression (lake basin) by finding all connected tiles
        at the same or lower elevation. Excludes mountains.
        
        Args:
            x, y: Starting coordinates in depression
            elevation_map: 2D list of elevation values
            visited: Set of already processed coordinates
            map_data: Current map data to check terrain types (optional)
            
        Returns:
            Set of (x, y) coordinates in the lake basin
        """
        lake_tiles = set()
        start_elevation = elevation_map[y][x]
        to_process = [(x, y)]
        visited.add((x, y))
        
        # Get thresholds to check if we're near mountains
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        
        # Find all tiles in the basin (connected tiles at same or lower elevation)
        while to_process:
            cx, cy = to_process.pop(0)
            current_elevation = elevation_map[cy][cx]
            
            # Don't create lakes in or near mountains
            if current_elevation >= hills_threshold:
                continue  # Skip mountain tiles
            
            # Also check terrain type if available
            if map_data:
                if map_data[cy][cx].terrain_type == TerrainType.MOUNTAIN:
                    continue  # Skip mountains
            
            lake_tiles.add((cx, cy))
            
            # Check all neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited:
                            neighbor_elevation = elevation_map[ny][nx]
                            
                            # Don't expand into mountains
                            if neighbor_elevation >= hills_threshold:
                                continue
                            
                            # If neighbor is at same or lower elevation, it's part of basin
                            if neighbor_elevation <= start_elevation + 0.02:
                                visited.add((nx, ny))
                                to_process.append((nx, ny))
        
        return lake_tiles
    
    def generate_rivers_and_lakes(self, map_data: List[List[Terrain]],
                                  elevation_map: List[List[float]]) -> Tuple[
                                      List[List[Terrain]], Set[Tuple[int, int]], Set[Tuple[int, int]]
                                  ]:
        """
        Generate rivers and lakes on the map using D8 flow direction algorithm.
        
        Args:
            map_data: Current map data
            elevation_map: Elevation map for flow calculations
            
        Returns:
            Tuple of (updated_map_data, river_tiles, lake_tiles)
        """
        river_tiles = set()
        lake_tiles = set()
        river_flow = {}  # Track flow volume for river width
        river_network = {}  # Track tributary count at each tile
        
        # Compute flow direction using D8 algorithm
        self._update_progress(0.52, "Computing flow directions...")
        flow_direction = self.compute_flow_direction(elevation_map)
        
        # Find river sources - increase number for more rivers
        # More sources: 1 per 2000 tiles for many rivers
        num_sources = max(100, (self.width * self.height) // 2000)
        sources = self.find_river_sources(elevation_map, num_sources=num_sources)
        self._update_progress(0.55, f"Found {len(sources)} river sources, computing flow accumulation...")
        
        # Compute flow accumulation (this will also create tributaries)
        flow_accumulation = self.compute_flow_accumulation(flow_direction, sources, elevation_map)
        
        self._update_progress(0.60, "Tracing rivers...")
        
        # Track lakes as they're created so rivers can flow into them
        current_lakes = set()
        river_terminations = []  # Track termination points for lake creation
        
        # Flow each river using D8 flow direction
        for source_x, source_y in sources:
            river_path, reached_coast, termination_point = self.flow_river(
                source_x, source_y, elevation_map, 
                flow_direction, river_flow, 
                river_network=river_network,
                existing_lakes=current_lakes,
                tributary_count=1
            )
            river_tiles.update(river_path)
            
            # Track termination points for lake creation
            if termination_point and not reached_coast:
                river_terminations.append(termination_point)
        
        # Create lakes at river terminations first (before finding lake sources)
        
        # Create lakes at river termination points
        # Lakes should be created in hills, forested hills, forests, or grasslands
        self._update_progress(0.65, "Creating lakes at river terminations...")
        visited_depressions = set()
        max_lake_size = 5000  # Maximum tiles per lake
        min_lake_size = 10    # Minimum tiles per lake
        total_lake_tiles = 0
        max_total_lakes = 100000  # Maximum total lake tiles
        
        shallow_threshold = getattr(self, 'elevation_thresholds', {}).get('shallow_water', 0.3)
        grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        
        # Create lakes at river terminations
        for x, y in river_terminations:
            if (x, y) in visited_depressions or total_lake_tiles >= max_total_lakes:
                continue
            
            # Check if this is a depression suitable for a lake
            current_elevation = elevation_map[y][x]
            is_depression = True
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if elevation_map[ny][nx] < current_elevation - 0.01:
                            is_depression = False
                            break
                if not is_depression:
                    break
            
            if is_depression:
                # Check if we're in appropriate terrain (hills, grassland, etc.)
                # Don't create lakes near mountains
                if current_elevation >= hills_threshold * 0.9:  # Too close to mountains
                    continue
                
                # Check elevation range - should be in hills or grassland range
                in_hills = grassland_threshold <= current_elevation < hills_threshold
                in_grassland = current_elevation >= shallow_threshold and current_elevation < grassland_threshold
                
                # Also check terrain type if available (hills, forested hills, forests, grasslands)
                terrain_ok = False
                if map_data:
                    terrain_type = map_data[y][x].terrain_type
                    terrain_ok = terrain_type in (
                        TerrainType.HILLS, TerrainType.FORESTED_HILL, 
                        TerrainType.FOREST, TerrainType.GRASSLAND
                    )
                else:
                    # If no map_data, just check elevation
                    terrain_ok = in_hills or in_grassland
                
                if terrain_ok:
                    lake_basin = self.fill_depression(x, y, elevation_map, visited_depressions, map_data)
                    # Allow smaller lakes (minimum 5 tiles for small depressions)
                    if 5 <= len(lake_basin) <= max_lake_size:
                        if total_lake_tiles + len(lake_basin) <= max_total_lakes:
                            lake_tiles.update(lake_basin)
                            current_lakes.update(lake_basin)  # Add to current lakes for other rivers
                            total_lake_tiles += len(lake_basin)
        
        # Find lakes in hills that can serve as river sources
        self._update_progress(0.68, "Finding lake sources in hills...")
        lake_sources = self.find_lake_sources(lake_tiles, elevation_map, map_data, 
                                              num_sources=max(20, len(lake_tiles) // 50))
        
        # Find hills locations that can serve as river sources
        self._update_progress(0.685, "Finding hills sources...")
        hills_sources = self.find_hills_sources(elevation_map, map_data)
        
        # Combine all additional sources
        additional_sources = lake_sources + hills_sources
        
        # Flow rivers from lake and hills sources
        if additional_sources:
            self._update_progress(0.69, f"Tracing {len(additional_sources)} rivers from lakes and hills...")
            for source_x, source_y in additional_sources:
                river_path, reached_coast, termination_point = self.flow_river(
                    source_x, source_y, elevation_map, 
                    flow_direction, river_flow, 
                    river_network=river_network,
                    existing_lakes=current_lakes,
                    tributary_count=1
                )
                river_tiles.update(river_path)
                
                # Track termination points for additional lake creation
                if termination_point and not reached_coast:
                    river_terminations.append(termination_point)
        
        # Fill other depressions, especially in hilly areas
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in visited_depressions or (x, y) in river_tiles:
                    continue
                
                if total_lake_tiles >= max_total_lakes:
                    break
                
                # Check if we're in a depression
                is_depression = True
                current_elevation = elevation_map[y][x]
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if elevation_map[ny][nx] < current_elevation - 0.01:
                                is_depression = False
                                break
                    if not is_depression:
                        break
                
                # Prefer lakes in hilly areas (elevation between grassland and hills threshold)
                # But NOT near mountains
                deep_water_threshold = getattr(self, 'elevation_thresholds', {}).get('deep_water', 0.25)
                grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
                hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
                
                # Don't create lakes near mountains (within 10% of hills threshold)
                if is_depression and current_elevation >= deep_water_threshold and current_elevation < hills_threshold * 0.9:
                    # Check if any neighbors are mountains
                    has_mountain_neighbor = False
                    if map_data:
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if dx == 0 and dy == 0:
                                    continue
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    if map_data[ny][nx].terrain_type == TerrainType.MOUNTAIN:
                                        has_mountain_neighbor = True
                                        break
                            if has_mountain_neighbor:
                                break
                    
                    if not has_mountain_neighbor:
                        # Higher chance for lakes in hilly areas, but not near mountains
                        is_hilly = grassland_threshold < current_elevation < hills_threshold * 0.85
                        lake_chance = 0.25 if is_hilly else 0.08  # Reduced chances
                        
                        if random.random() < lake_chance:
                            lake_basin = self.fill_depression(x, y, elevation_map, visited_depressions, map_data)
                            if min_lake_size <= len(lake_basin) <= max_lake_size:
                                if total_lake_tiles + len(lake_basin) <= max_total_lakes:
                                    lake_tiles.update(lake_basin)
                                    total_lake_tiles += len(lake_basin)
            if total_lake_tiles >= max_total_lakes:
                break
        
        self._update_progress(0.70, f"Generated {len(river_tiles)} river tiles and {len(lake_tiles)} lake tiles")
        
        # Apply rivers and lakes to map
        # Rivers use RIVER terrain type (distinct from coastal shallow water)
        shallow_threshold = getattr(self, 'elevation_thresholds', {}).get('shallow_water', 0.3)
        
        for x, y in river_tiles:
            current_elevation = elevation_map[y][x]
            # Check if river has reached the ocean (shallow water)
            is_at_ocean = current_elevation < shallow_threshold
            
            # Place rivers on land (not on existing deep water)
            # Allow rivers in mountains, hills, and grasslands - they should be visible throughout their path
            hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
            if map_data[y][x].terrain_type != TerrainType.DEEP_WATER:
                # Use flow accumulation to determine river width
                accumulation = flow_accumulation[y][x]
                flow_volume = river_flow.get((x, y), 1)
                
                # If at ocean, use shallow water; otherwise use RIVER terrain
                if is_at_ocean:
                    # River reaches ocean - use shallow water
                    terrain_type = TerrainType.SHALLOW_WATER
                else:
                    # River on land - use RIVER terrain type
                    terrain_type = TerrainType.RIVER
                
                # Major rivers (high accumulation or multiple sources) get wider
                if accumulation >= 3 or flow_volume >= 3:
                    # Make wider (include neighbors)
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor_elevation = elevation_map[ny][nx]
                                # Don't expand rivers into deep water
                                if map_data[ny][nx].terrain_type != TerrainType.DEEP_WATER:
                                    # Check if neighbor is also at ocean
                                    neighbor_is_ocean = neighbor_elevation < shallow_threshold
                                    neighbor_terrain = TerrainType.SHALLOW_WATER if neighbor_is_ocean else TerrainType.RIVER
                                    map_data[ny][nx] = Terrain(neighbor_terrain)
                else:
                    map_data[y][x] = Terrain(terrain_type)
        
        # Lakes become shallow water (but not near mountains)
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        for x, y in lake_tiles:
            current_elevation = elevation_map[y][x]
            # Don't place lakes near mountains
            if (map_data[y][x].terrain_type not in (TerrainType.DEEP_WATER, TerrainType.MOUNTAIN, TerrainType.RIVER) and
                current_elevation < hills_threshold * 0.9):
                map_data[y][x] = Terrain(TerrainType.SHALLOW_WATER)
        
        return map_data, river_tiles, lake_tiles
    
    def apply_erosion(self, map_data: List[List[Terrain]],
                     elevation_map: List[List[float]],
                     river_tiles: Set[Tuple[int, int]]) -> List[List[Terrain]]:
        """
        Apply erosion pass to smooth terrain near rivers.
        Rivers erode the land around them slightly.
        
        Args:
            map_data: Current map data
            elevation_map: Elevation map
            river_tiles: Set of river tile coordinates
            
        Returns:
            Updated map data with erosion applied
        """
        # Simple erosion: convert some grassland near rivers to shallow water (riverbanks)
        # But don't erode near mountains
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        
        for x, y in river_tiles:
            current_elevation = elevation_map[y][x]
            # Don't erode near mountains
            if current_elevation >= hills_threshold * 0.85:
                continue
            
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        neighbor_elevation = elevation_map[ny][nx]
                        # Don't erode near mountains
                        if neighbor_elevation >= hills_threshold * 0.85:
                            continue
                        
                        if map_data[ny][nx].terrain_type == TerrainType.GRASSLAND:
                            # Small chance to erode adjacent grassland
                            if random.random() < 0.1:  # 10% chance
                                map_data[ny][nx] = Terrain(TerrainType.SHALLOW_WATER)
        
        return map_data
    
    def compute_water_distance_map(self, map_data: List[List[Terrain]], 
                                   max_distance: int = 25) -> List[List[float]]:
        """
        Pre-compute distance to nearest water for all tiles using BFS.
        Much faster than checking every water tile for every grassland tile.
        
        Args:
            map_data: Current map data
            max_distance: Maximum distance to compute (beyond this, return max_distance)
            
        Returns:
            2D list of distances to nearest water
        """
        self._update_progress(0.86, "Computing water distance map...")
        distance_map = [[max_distance + 1.0] * self.width for _ in range(self.height)]
        
        # Initialize queue with all water tiles
        queue = deque()
        
        for y in range(self.height):
            for x in range(self.width):
                # Include rivers in water distance calculation for forests
                if map_data[y][x].terrain_type in (TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, TerrainType.RIVER):
                    distance_map[y][x] = 0.0
                    queue.append((x, y, 0.0))
        
        # BFS to compute distances
        processed = 0
        total_tiles = self.width * self.height
        
        while queue:
            x, y, dist = queue.popleft()
            
            # Check all neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        # Calculate new distance (Euclidean for diagonal, Manhattan for cardinal)
                        if dx != 0 and dy != 0:
                            new_dist = dist + 1.414  # sqrt(2) for diagonal
                        else:
                            new_dist = dist + 1.0
                        
                        if new_dist < distance_map[ny][nx] and new_dist <= max_distance:
                            distance_map[ny][nx] = new_dist
                            queue.append((nx, ny, new_dist))
            
            processed += 1
            if processed % 50000 == 0:
                self._update_progress(0.86 + 0.02 * (processed / total_tiles), 
                                     f"Computing distances... {processed}/{total_tiles}")
        
        return distance_map
    
    def compute_river_lake_distance_map(self, map_data: List[List[Terrain]],
                                        river_tiles: Set[Tuple[int, int]],
                                        lake_tiles: Set[Tuple[int, int]],
                                        max_distance: int = 25) -> List[List[float]]:
        """
        Pre-compute distance to nearest river or lake (not coastal water).
        Only considers rivers and lakes, not all water.
        
        Args:
            map_data: Current map data
            river_tiles: Set of river tile coordinates
            lake_tiles: Set of lake tile coordinates
            max_distance: Maximum distance to compute
            
        Returns:
            2D list of distances to nearest river/lake
        """
        distance_map = [[max_distance + 1.0] * self.width for _ in range(self.height)]
        
        # Initialize queue with all river and lake tiles
        queue = deque()
        water_tiles = river_tiles | lake_tiles
        
        for x, y in water_tiles:
            if 0 <= x < self.width and 0 <= y < self.height:
                distance_map[y][x] = 0.0
                queue.append((x, y, 0.0))
        
        # BFS to compute distances
        while queue:
            x, y, dist = queue.popleft()
            
            # Check all neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        # Calculate new distance
                        if dx != 0 and dy != 0:
                            new_dist = dist + 1.414  # sqrt(2) for diagonal
                        else:
                            new_dist = dist + 1.0
                        
                        if new_dist < distance_map[ny][nx] and new_dist <= max_distance:
                            distance_map[ny][nx] = new_dist
                            queue.append((nx, ny, new_dist))
        
        return distance_map
    
    def add_forests(self, map_data: List[List[Terrain]],
                   elevation_map: List[List[float]],
                   river_tiles: Set[Tuple[int, int]] = None,
                   lake_tiles: Set[Tuple[int, int]] = None) -> List[List[Terrain]]:
        """
        Add forests to grassland areas and forested hills to hill areas, only near rivers and lakes (not coastal water).
        
        Args:
            map_data: 2D list of Terrain objects
            elevation_map: 2D list of elevation values to determine hill elevations
            river_tiles: Set of river tile coordinates
            lake_tiles: Set of lake tile coordinates
            
        Returns:
            Map data with forests and forested hills added
        """
        if river_tiles is None:
            river_tiles = set()
        if lake_tiles is None:
            lake_tiles = set()
        
        # Pre-compute distance to rivers/lakes only (not all water)
        self._update_progress(0.86, "Computing river/lake distance map...")
        distance_map = self.compute_river_lake_distance_map(map_data, river_tiles, lake_tiles, max_distance=20)
        
        # Use a different seed for forest placement
        forest_seed = (self.seed + 1000) if self.seed is not None else None
        noise = PerlinNoise(seed=forest_seed)
        
        # Scale for forest clusters
        forest_scale = 0.02
        
        # Get elevation thresholds to determine hill elevations
        grassland_threshold = getattr(self, 'elevation_thresholds', {}).get('grassland', 0.5)
        hills_threshold = getattr(self, 'elevation_thresholds', {}).get('hills', 0.7)
        
        # Calculate a buffer zone to keep forested hills away from mountains
        # Forested hills should only be in the lower-to-mid hills range, not near mountains
        hills_range = hills_threshold - grassland_threshold
        forested_hill_max_elevation = grassland_threshold + (hills_range * 0.75)  # Top 75% of hills range
        
        total_grassland = sum(1 for row in map_data for tile in row 
                             if tile.terrain_type == TerrainType.GRASSLAND)
        total_hills = sum(1 for row in map_data for tile in row 
                         if tile.terrain_type == TerrainType.HILLS)
        processed = 0
        
        self._update_progress(0.88, "Placing forests and forested hills...")
        
        for y in range(self.height):
            for x in range(self.width):
                current_terrain = map_data[y][x].terrain_type
                current_elevation = elevation_map[y][x]
                
                # Get distance to nearest river/lake (not coastal water)
                min_water_distance = distance_map[y][x]
                
                # Only place forests/forested hills near rivers/lakes (within reasonable distance)
                max_water_distance = 12  # Maximum distance from river/lake to place forests
                if min_water_distance > max_water_distance:
                    continue  # Too far from river/lake, skip
                
                # Generate forest noise
                forest_noise = noise.octave_noise(x, y, octaves=4, 
                                                  persistence=0.6, scale=forest_scale)
                forest_value = (forest_noise + 1.0) / 2.0
                
                # Adjust threshold based on proximity to river/lake
                # Closer to water = lower threshold (more likely to be forest)
                # Higher base threshold to reduce overall forest density
                forest_threshold = 0.65  # Higher base threshold
                if min_water_distance < 3:  # Very close to river/lake
                    # Reduce threshold significantly near water
                    forest_threshold = 0.25 - (3 - min_water_distance) * 0.05
                    forest_threshold = max(0.15, forest_threshold)  # Minimum threshold
                elif min_water_distance < 6:  # Close to river/lake
                    forest_threshold = 0.4 - (6 - min_water_distance) * 0.05
                elif min_water_distance < 9:  # Moderately close
                    forest_threshold = 0.5 - (9 - min_water_distance) * 0.03
                elif min_water_distance < 12:  # Somewhat close
                    forest_threshold = 0.6 - (12 - min_water_distance) * 0.03
                
                # Place forest on grassland if noise value is high enough
                if current_terrain == TerrainType.GRASSLAND:
                    if forest_value > forest_threshold:
                        map_data[y][x] = Terrain(TerrainType.FOREST)
                    processed += 1
                
                # Place forested hills on hills at hill elevations, but not too close to mountains
                elif current_terrain == TerrainType.HILLS:
                    # Check if elevation is in the hill range AND not too close to mountains
                    if grassland_threshold < current_elevation < forested_hill_max_elevation:
                        if forest_value > forest_threshold:
                            map_data[y][x] = Terrain(TerrainType.FORESTED_HILL)
                    processed += 1
                
                # Update progress every 50000 tiles
                if processed % 50000 == 0:
                    total_processed = total_grassland + total_hills
                    if total_processed > 0:
                        progress = 0.88 + 0.07 * (processed / total_processed)
                        self._update_progress(progress, 
                                             f"Placing forests and forested hills... {processed}/{total_processed}")
        
        return map_data
    
    def add_impassable_borders(self, map_data: List[List[Terrain]],
                               elevation_map: List[List[float]]) -> List[List[Terrain]]:
        """
        Add impassable mountain borders at the top and bottom of the map.
        Uses a contoured approach with smooth elevation transition.
        
        Args:
            map_data: Current map data
            elevation_map: Original elevation map for reference
            
        Returns:
            Map data with impassable borders added
        """
        border_width = 50  # Width of the border in tiles
        max_elevation_boost = 0.5  # Maximum elevation boost at edges
        
        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from top and bottom edges
                dist_from_top = y
                dist_from_bottom = self.height - 1 - y
                
                # Find minimum distance to edge
                min_dist_to_edge = min(dist_from_top, dist_from_bottom)
                
                # If within border width, raise elevation
                if min_dist_to_edge < border_width:
                    # Calculate elevation boost with smooth falloff
                    # Use a smooth curve (sine-based) for natural contouring
                    progress = min_dist_to_edge / border_width
                    # Smooth curve: starts at 1.0 at edge, goes to 0.0 at border_width
                    boost_factor = math.sin(progress * math.pi / 2)  # Smooth falloff
                    elevation_boost = max_elevation_boost * (1.0 - boost_factor)
                    
                    # Raise the elevation
                    new_elevation = elevation_map[y][x] + elevation_boost
                    
                    # Reclassify terrain based on new elevation using distribution-based thresholds
                    thresholds = getattr(self, 'elevation_thresholds', {
                        'hills': 0.65,
                        'grassland': 0.5,
                        'shallow_water': 0.3
                    })
                    
                    if new_elevation >= thresholds.get('hills', 0.65):
                        # High enough to be mountain
                        map_data[y][x] = Terrain(TerrainType.MOUNTAIN)
                    elif new_elevation >= thresholds.get('grassland', 0.5):
                        # High enough to be hills
                        map_data[y][x] = Terrain(TerrainType.HILLS)
                    elif new_elevation >= thresholds.get('shallow_water', 0.3):
                        # Could be grassland or hills depending on original
                        if elevation_map[y][x] < thresholds.get('shallow_water', 0.3):
                            # Was water, now make it grassland or hills
                            if new_elevation >= thresholds.get('grassland', 0.5):
                                map_data[y][x] = Terrain(TerrainType.HILLS)
                            else:
                                map_data[y][x] = Terrain(TerrainType.GRASSLAND)
                        # Otherwise keep existing terrain
                    # Below shallow water threshold, keep existing terrain (water stays water)
        
        return map_data
    
    def place_towns(self, map_data: List[List[Terrain]], 
                   river_tiles: Set[Tuple[int, int]],
                   lake_tiles: Set[Tuple[int, int]]) -> List[Settlement]:
        """
        Place towns on the map based on resource distribution.
        
        Rules:
        - Towns must be on shallow water (coastal or river/lake)
        - Must be within 800 tiles of:
          * Grasslands (agriculture)
          * Hills (mining)
          * Forests/forested hills (lumber)
        - No town should be closer than 1600 tiles to another town
        
        Args:
            map_data: 2D list of Terrain objects
            river_tiles: Set of river tile coordinates
            lake_tiles: Set of lake tile coordinates
            
        Returns:
            List of Settlement objects
        """
        # List of town names to randomly assign
        town_names = [
            "Aelbrig", "Baelara", "Brannoch", "Caerwyn", "Clynnmor", "Dûn Aine", "Eilthir", "Faelinn",
            "Garanmoor", "Halbragh", "Inniskeir", "Kaer Muir", "Lirvale", "Moighan", "Naevra", "Oirthir",
            "Pendraen", "Quarnach", "Rhoslyn", "Saethra", "Taerloch", "Uainech", "Vannagh", "Wynfell",
            "Aedlen", "Beithra", "Cairmorra", "Dromlach", "Erynfael", "Fynedd", "Glan Tir", "Haerloch",
            "Irvallan", "Kilmora", "Lornach", "Muirlen", "Naddra", "Orraigh", "Pwyllin", "Rhenmor",
            "Suilvenn", "Taranis Gate", "Ulbrae", "Veyrach", "Wynglen", "Aenloch", "Balwynne", "Corthrae",
            "Drumnor", "Eirvale", "Farlan", "Gorthen", "Hallowmere", "Ildrach", "Kellmor", "Lughmoor",
            "Marnach", "Nairden", "Onachra", "Penvale", "Quorrae", "Rhaedwyn", "Siorra", "Taebrin",
            "Urris", "Vaelorn", "Wintir", "Aghren", "Brethrae", "Clonagh", "Dairlin", "Eileanach",
            "Finloch", "Gwynglen", "Hallara", "Iorven", "Kelnagh", "Lirach", "Morrin", "Naesca",
            "Orlinn", "Paedrin", "Rhunvale", "Saille", "Taranwy", "Ullach", "Varnoch", "Wynnmor",
            "Aerwen", "Branagh", "Cadanor", "Dûn Lir", "Elthrae", "Fionmoor", "Glastir", "Haelwen",
            "Illenach", "Kaervyn", "Lorraig", "Maegra"
        ]
        # Shuffle the names for random assignment, then use as a queue (pop from front)
        random.shuffle(town_names)
        
        # List of village names to randomly assign
        village_names = [
            "Aelrin", "Aghra", "Ailloch", "Airdlen", "Aisca", "Aislin", "Albrin", "Alrae", "Ambragh", "Anwen",
            "Ardra", "Arlen", "Arnagh", "Asca", "Athrae", "Baelach", "Baerin", "Bailloch", "Ballen", "Balrae",
            "Banrin", "Barraig", "Beatha", "Beithin", "Belmor", "Benach", "Benrae", "Bethra", "Bhaen", "Blaenoch",
            "Blethra", "Boirlen", "Braen", "Branlin", "Brenach", "Brinloch", "Brochan", "Bronnach", "Brunna", "Brynlin",
            "Caelach", "Caerlin", "Cairin", "Calrae", "Cambrin", "Canaigh", "Carlen", "Casra", "Cathra", "Ceannach",
            "Cearnin", "Ceolra", "Cerin", "Cethra", "Charnin", "Chloen", "Cianach", "Clachra", "Clanna", "Clarn",
            "Clenach", "Clonnin", "Clutha", "Coenlin", "Colbrae", "Collin", "Comrach", "Conlin", "Corran", "Cothra",
            "Craelin", "Crannach", "Crethra", "Croen", "Cuilen", "Curragh", "Daelach", "Daenin", "Dairach", "Dalin",
            "Damra", "Darnach", "Deirlin", "Delrae", "Denach", "Derlen", "Dethra", "Doinn", "Domach", "Donlen",
            "Dorrin", "Dranagh", "Drethra", "Drinn", "Drunlen", "Dualla", "Dulen", "Dûninn", "Duthra", "Ealra",
            "Eanach", "Eirlen", "Eithra", "Elach", "Elin", "Embrin", "Enloch", "Enna", "Enrach", "Enwen",
            "Eorlen", "Eothra", "Errin", "Eslen", "Ethlin", "Faelach", "Faenna", "Failinn", "Fainach", "Falin",
            "Falra", "Farrach", "Fathra", "Fearnin", "Feirlen", "Felin", "Fenach", "Ferin", "Fianna", "Fildra",
            "Finach", "Finlen", "Finnra", "Fionach", "Firlen", "Flanra", "Flinn", "Fluthra", "Foen", "Forrach",
            "Fraen", "Frinach", "Fuinna", "Gaenach", "Gailin", "Galach", "Gallen", "Garnin", "Gathra", "Geanlin",
            "Geirlen", "Gellan", "Gerach", "Gethra", "Ghaen", "Glaenach", "Glann", "Glethra", "Gluin", "Goirlen",
            "Golach", "Gollin", "Gorlen", "Granna", "Grethra", "Grinach", "Gruin", "Guenna", "Gulach", "Gullen",
            "Gwyrin", "Haenach", "Halra", "Hanlin", "Harrach", "Heirlen", "Helin", "Henach", "Herlin", "Hethra",
            "Hianna", "Hirin", "Holach", "Hollen", "Horin", "Hraith", "Huinn", "Ianach", "Iarla", "Ienlin",
            "Ilenach", "Ilthra", "Inach", "Inlen", "Innisra", "Iorach", "Iorlen", "Islen", "Ithra", "Kaelra",
            "Kaen", "Kairlen", "Kalach", "Kanlin", "Karrach", "Kearin", "Keirlen", "Kellach", "Kelnin", "Kernach",
            "Kethra", "Kiann", "Kilrach", "Kinnin", "Kirlen", "Klann", "Klythra", "Koen", "Korlen", "Kraen",
            "Laenna", "Lairlen", "Lallan", "Larnach", "Leirach", "Lellan", "Lenra", "Lethra", "Lianach", "Lielin",
            "Linach", "Lirinn", "Lirlen", "Lithra", "Loen", "Loinn", "Lornach", "Lothra", "Luinn", "Maelach",
            "Maenna", "Mailin", "Mainach", "Malra", "Marnin", "Mathra", "Mearlen", "Meirach", "Mellach", "Menlin",
            "Merach", "Methra", "Mhaen", "Mianna", "Minach", "Mirlen", "Moinn", "Mornach", "Muirlen", "Muinn",
            "Nairach", "Nallen", "Narnin", "Neirlen", "Nellach", "Nenra", "Nethra", "Niann", "Ninach", "Noinn",
            "Norlen", "Nuinn", "Oenlin", "Oirach", "Oirlen", "Olach", "Ollin", "Ornach", "Orra", "Othra",
            "Paenna", "Pailin", "Panach", "Parlen", "Peirach", "Pellin", "Penach", "Perrin", "Pethra", "Phairin",
            "Phinlen", "Phorlen", "Porthra", "Quaen", "Quallin", "Quenach", "Quillin", "Quinra", "Raenna", "Rairlen",
            "Rallan", "Ranach", "Rarnin", "Reirlen", "Relach", "Renlin", "Rethra", "Rhaen", "Rhialin", "Rhonach",
            "Rhuinn", "Rianach", "Riann", "Rinlen", "Rionach", "Rithra", "Roen", "Rolach", "Rolin", "Rornach",
            "Ruirlen", "Ruinn", "Saelach", "Saenna", "Sainach", "Salra", "Sarnin", "Seirlen", "Selach", "Senlin",
            "Sethra", "Sgairin", "Shainach", "Sheirlen", "Shellin", "Shorlen", "Siann", "Sillach", "Simlen", "Sinnach",
            "Soinn", "Sorlen", "Sothra", "Suinn", "Taenach", "Tairlen", "Tallen", "Tarnach", "Teirach", "Tellin",
            "Tenra", "Tethra", "Thaen", "Thalin", "Thirlen", "Thonnach", "Thuin", "Tiann", "Tinach", "Toinn",
            "Tornin", "Tuirlen", "Tuinn", "Uaen", "Uallin", "Uenach", "Ullin", "Ulthra", "Unach", "Unlen",
            "Urrin", "Uthra", "Vaenach", "Vallin", "Varnin", "Veirlen", "Velach", "Vernin", "Vethra", "Viann",
            "Vinlen", "Voen", "Volach", "Vornach", "Wairlin", "Wathra", "Wenlin", "Wethra", "Wiann", "Winach",
            "Woinn", "Wornin", "Wuinn", "Yaenna", "Yairlen", "Yallan", "Yenach", "Yornach", "Yuinn", "Yuthra"
        ]
        # Shuffle the village names for random assignment, then use as a queue (pop from front)
        random.shuffle(village_names)
        
        towns = []
        
        # Find all shallow water locations (coastal + rivers + lakes)
        shallow_water_tiles = set()
        for y in range(self.height):
            for x in range(self.width):
                terrain_type = map_data[y][x].terrain_type
                if terrain_type in (TerrainType.SHALLOW_WATER, TerrainType.RIVER):
                    shallow_water_tiles.add((x, y))
        
        # Also add lake tiles (they're shallow water)
        shallow_water_tiles.update(lake_tiles)
        
        # Create resource location sets for efficient lookup
        agriculture_tiles = set()  # Grasslands
        mining_tiles = set()  # Hills
        lumber_tiles = set()  # Forests and forested hills
        
        for y in range(self.height):
            for x in range(self.width):
                terrain_type = map_data[y][x].terrain_type
                if terrain_type == TerrainType.GRASSLAND:
                    agriculture_tiles.add((x, y))
                elif terrain_type == TerrainType.HILLS:
                    mining_tiles.add((x, y))
                elif terrain_type in (TerrainType.FOREST, TerrainType.FORESTED_HILL):
                    lumber_tiles.add((x, y))
        
        # Pre-filter: Find all grassland tiles adjacent to shallow water (much faster)
        grassland_adjacent_to_water = set()
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        # Only iterate through shallow water tiles and check their neighbors (much smaller set)
        for wx, wy in shallow_water_tiles:
            for dx, dy in directions:
                nx, ny = wx + dx, wy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if map_data[ny][nx].terrain_type == TerrainType.GRASSLAND:
                        grassland_adjacent_to_water.add((nx, ny))
        
        print(f"Found {len(grassland_adjacent_to_water)} grassland tiles adjacent to water")
        
        # Check resource requirements for candidate locations
        potential_towns = []
        resource_range = 30  # Within 30 tiles of resources (tight range)
        
        # Convert resource sets to lists for faster iteration (sets are slower for small ranges)
        mining_list = list(mining_tiles)
        lumber_list = list(lumber_tiles)
        
        print(f"Checking {len(grassland_adjacent_to_water)} candidate locations for resources...")
        
        # Check each candidate location - use direct distance check (faster for small ranges)
        checked = 0
        for x, y in grassland_adjacent_to_water:
            checked += 1
            if checked % 5000 == 0:
                print(f"Checking candidate locations: {checked}/{len(grassland_adjacent_to_water)}, found: {len(potential_towns)}")
            
            has_mining = False
            has_lumber = False
            
            # Direct check: only look at nearby tiles (61x61 area = 3721 tiles max)
            # This is faster than iterating through all resource tiles
            for dy in range(-resource_range, resource_range + 1):
                if has_mining and has_lumber:
                    break
                for dx in range(-resource_range, resource_range + 1):
                    if abs(dx) + abs(dy) > resource_range:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        # Check if this tile is a mining resource
                        if not has_mining and (nx, ny) in mining_tiles:
                            has_mining = True
                        # Check if this tile is a lumber resource
                        if not has_lumber and (nx, ny) in lumber_tiles:
                            has_lumber = True
                        if has_mining and has_lumber:
                            break
            
            if has_mining and has_lumber:
                potential_towns.append((x, y))
        
        # Filter towns to ensure minimum distance - reduced to get 55-65 towns
        min_town_distance = 50  # Reduced to allow more towns
        min_town_distance_sq = min_town_distance * min_town_distance  # Use squared distance (faster)
        target_towns = 60  # Target number of towns (55-65 range)
        
        # Use spatial grid for fast distance checking
        town_grid = {}  # Maps (x//min_town_distance, y//min_town_distance) to list of towns
        grid_cell_size = min_town_distance
        
        print(f"Found {len(potential_towns)} potential town locations, filtering by distance...")
        print(f"Target: {target_towns} towns, current towns: {len(towns)}")
        
        if len(potential_towns) == 0:
            print("WARNING: No potential town locations found!")
            return towns + []
        
        for i, (x, y) in enumerate(potential_towns):
            if i % 1000 == 0:
                print(f"Filtering towns: {i}/{len(potential_towns)}, placed: {len(towns)}")
            
            # Early exit if we have enough towns
            current_count = len(towns)
            if current_count >= target_towns:
                print(f"Reached target of {target_towns} towns (actual: {current_count}), stopping early")
                break
            
            # Check distance to existing towns using spatial grid (much faster)
            too_close = False
            grid_x, grid_y = x // grid_cell_size, y // grid_cell_size
            
            # Only check nearby grid cells (3x3 area)
            for gx in range(grid_x - 1, grid_x + 2):
                for gy in range(grid_y - 1, grid_y + 2):
                    if (gx, gy) in town_grid:
                        for town in town_grid[(gx, gy)]:
                            town_x, town_y = town.get_position()
                            dx, dy = x - town_x, y - town_y
                            distance_sq = dx * dx + dy * dy
                            if distance_sq < min_town_distance_sq:
                                too_close = True
                                break
                    if too_close:
                        break
                if too_close:
                    break
            
            if not too_close:
                # Name will be assigned from worldbuilding data later
                new_town = Settlement(SettlementType.TOWN, x, y, name=None)
                towns.append(new_town)
                # Add to spatial grid
                if (grid_x, grid_y) not in town_grid:
                    town_grid[(grid_x, grid_y)] = []
                town_grid[(grid_x, grid_y)].append(new_town)
        
        # Place 4 villages for each town (one for each resource type)
        villages = []
        village_range = 30  # Villages must be within 30 tiles of their town (matching resource range)
        
        # Track all occupied tiles (towns and villages) to prevent overlaps
        occupied_tiles = set()
        for town in towns:
            tx, ty = town.get_position()
            occupied_tiles.add((tx, ty))
        
        # Create agriculture tiles set for village placement
        agriculture_tiles = set()
        for y in range(self.height):
            for x in range(self.width):
                if map_data[y][x].terrain_type == TerrainType.GRASSLAND:
                    agriculture_tiles.add((x, y))
        
        print(f"Placing villages for {len(towns)} towns...")
        for i, town in enumerate(towns):
            if i % 10 == 0:
                print(f"Placing villages for town {i+1}/{len(towns)}, placed {len(villages)} villages so far")
            
            town_x, town_y = town.get_position()
            
            # 1. Village next to shallow water (for fish and fowl) - must be on land adjacent to water
            water_village = self._find_village_location_fast(
                town_x, town_y, shallow_water_tiles, village_range, 
                map_data, None, is_water_village=True, occupied_tiles=occupied_tiles
            )
            if water_village:
                # Name will be assigned from worldbuilding data later
                resource = "fish and fowl"
                new_village = Settlement(SettlementType.VILLAGE, water_village[0], water_village[1], 
                                        name=None, vassal_to=town, supplies_resource=resource)
                villages.append(new_village)
                town.vassal_villages.append(new_village)  # Add to town's vassal list
                if resource not in town.resource_villages:
                    town.resource_villages[resource] = []
                town.resource_villages[resource].append(new_village)  # Add to town's resource mapping
                occupied_tiles.add(water_village)
            
            # 2. Village on grasslands (for grain and livestock)
            agriculture_village = self._find_village_location_fast(
                town_x, town_y, agriculture_tiles, village_range,
                map_data, TerrainType.GRASSLAND, occupied_tiles=occupied_tiles
            )
            if agriculture_village:
                # Name will be assigned from worldbuilding data later
                resource = "grain and livestock"
                new_village = Settlement(SettlementType.VILLAGE, agriculture_village[0], agriculture_village[1],
                                        name=None, vassal_to=town, supplies_resource=resource)
                villages.append(new_village)
                town.vassal_villages.append(new_village)  # Add to town's vassal list
                if resource not in town.resource_villages:
                    town.resource_villages[resource] = []
                town.resource_villages[resource].append(new_village)  # Add to town's resource mapping
                occupied_tiles.add(agriculture_village)
            
            # 3. Village in hills (for ore)
            mining_village = self._find_village_location_fast(
                town_x, town_y, mining_tiles, village_range,
                map_data, TerrainType.HILLS, occupied_tiles=occupied_tiles
            )
            if mining_village:
                # Name will be assigned from worldbuilding data later
                resource = "ore"
                new_village = Settlement(SettlementType.VILLAGE, mining_village[0], mining_village[1],
                                        name=None, vassal_to=town, supplies_resource=resource)
                villages.append(new_village)
                town.vassal_villages.append(new_village)  # Add to town's vassal list
                if resource not in town.resource_villages:
                    town.resource_villages[resource] = []
                town.resource_villages[resource].append(new_village)  # Add to town's resource mapping
                occupied_tiles.add(mining_village)
            
            # 4. Village in forests or forested hills (for lumber)
            lumber_village = self._find_village_location_fast(
                town_x, town_y, lumber_tiles, village_range,
                map_data, None, allowed_terrain=[TerrainType.FOREST, TerrainType.FORESTED_HILL], 
                occupied_tiles=occupied_tiles
            )
            if lumber_village:
                # Name will be assigned from worldbuilding data later
                resource = "lumber"
                new_village = Settlement(SettlementType.VILLAGE, lumber_village[0], lumber_village[1],
                                        name=None, vassal_to=town, supplies_resource=resource)
                villages.append(new_village)
                town.vassal_villages.append(new_village)  # Add to town's vassal list
                if resource not in town.resource_villages:
                    town.resource_villages[resource] = []
                town.resource_villages[resource].append(new_village)  # Add to town's resource mapping
                occupied_tiles.add(lumber_village)
        
        # Return both towns and villages
        all_settlements = towns + villages
        total_settlements = len(all_settlements)
        print(f"Generated {len(towns)} towns and {len(villages)} villages (total: {total_settlements} settlements)")
        return all_settlements
    
    def place_cities(self, map_data: List[List[Terrain]], 
                    river_tiles: Set[Tuple[int, int]],
                    lake_tiles: Set[Tuple[int, int]],
                    existing_settlements: List[Settlement]) -> List[Settlement]:
        """
        Place cities on the map based on town clusters.
        
        Rules:
        - Cities appear adjacent to shallow water
        - A city is created when 3+ towns are within 200 blocks of a shallow water tile
        - Those towns become vassals of the city
        
        Args:
            map_data: 2D list of Terrain objects
            river_tiles: Set of river tile coordinates
            lake_tiles: Set of lake tile coordinates
            existing_settlements: List of existing settlements (towns and villages)
            
        Returns:
            List of City Settlement objects
        """
        cities = []
        
        # Get all towns from existing settlements
        towns = [s for s in existing_settlements if s.settlement_type == SettlementType.TOWN]
        
        if len(towns) < 3:
            print("Not enough towns to form cities (need at least 3)")
            return cities
        
        # Find all shallow water locations (coastal + rivers + lakes)
        shallow_water_tiles = set()
        for y in range(self.height):
            for x in range(self.width):
                terrain_type = map_data[y][x].terrain_type
                if terrain_type in (TerrainType.SHALLOW_WATER, TerrainType.RIVER):
                    shallow_water_tiles.add((x, y))
        
        # Also add lake tiles (they're shallow water)
        shallow_water_tiles.update(lake_tiles)
        
        # List of city names to randomly assign
        city_names = [
            "Ailthirion", "Albaroch", "Ardmaen", "Bael Tir", "Belenmor", "Brannath",
            "Caer Aedon", "Caer Dovra", "Caerlinne", "Cairbrigh", "Caltraen", "Cathair Muir",
            "Ceorlach", "Coedwyn", "Corravon", "Craegwyn", "Crennagh", "Culdaran", "Cynnaroch",
            "Dalbrad", "Danvraen", "Deorwyn", "Dinas Mael", "Dûn Caelen", "Dûn Gwair", "Dûn Moira",
            "Eilthros", "Elarach", "Eredwyn", "Eryndor", "Faelgor", "Fionncaer", "Galtraen",
            "Garvach", "Glaemor", "Glanraith", "Gwairmor", "Gwennar", "Hael Tir", "Hallavor",
            "Illtraen", "Innis Muir", "Kaer Dûn", "Kaerthir", "Kelravon", "Kilmorven", "Korrwyn",
            "Lannvrech", "Lir Dûn", "Lochraen", "Lorcairn", "Lughvenn", "Maen Tir", "Maerwyn",
            "Mairach", "Malthros", "Marvran", "Menhirra", "Mornath", "Nairvenn", "Naivros",
            "Nevanor", "Oirthmar", "Orra Dûn", "Ossvenn", "Pendraith", "Penwynn", "Rathmorra",
            "Rhydwen", "Rionnath", "Sarn Tir", "Scaevra", "Sennach", "Sevanach", "Sionmor",
            "Solmara", "Stronach", "Taelvenn", "Talmorra", "Tanraith", "Taranwen", "Tethmor",
            "Thalrach", "Thirnaen", "Tir Alwen", "Tir Caelen", "Tulanach", "Tynmuir", "Uaine Dûn",
            "Urvalen", "Valtraen", "Varwynn", "Veilmar", "Velthir", "Vennach", "Veyl Tir",
            "Vornachair", "Wynmorra", "Ythrenn", "Zairloch"
        ]
        random.shuffle(city_names)
        name_index = 0
        
        # Track occupied tiles (cities can't overlap with existing settlements)
        occupied_tiles = set()
        for settlement in existing_settlements:
            sx, sy = settlement.get_position()
            occupied_tiles.add((sx, sy))
        
        # Find grassland tiles adjacent to shallow water
        city_range = 200  # Towns must be within 200 blocks
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        print(f"Checking {len(shallow_water_tiles)} shallow water tiles for city placement...")
        
        # For each shallow water tile, check if 3+ towns are within range
        potential_city_locations = []
        for wx, wy in shallow_water_tiles:
            # Check adjacent grassland tiles
            for dx, dy in directions:
                city_x, city_y = wx + dx, wy + dy
                if 0 <= city_x < self.width and 0 <= city_y < self.height:
                    if map_data[city_y][city_x].terrain_type == TerrainType.GRASSLAND:
                        if (city_x, city_y) not in occupied_tiles:
                            # Count towns within range
                            nearby_towns = []
                            for town in towns:
                                tx, ty = town.get_position()
                                # Use Manhattan distance for efficiency
                                distance = abs(tx - city_x) + abs(ty - city_y)
                                if distance <= city_range:
                                    nearby_towns.append(town)
                            
                            if len(nearby_towns) >= 3:
                                potential_city_locations.append((city_x, city_y, nearby_towns))
        
        print(f"Found {len(potential_city_locations)} potential city locations")
        
        # Sort by number of nearby towns (descending) to prioritize locations with more towns
        potential_city_locations.sort(key=lambda x: len(x[2]), reverse=True)
        
        # Track which towns have been claimed by cities
        claimed_towns = set()
        
        # Place cities (avoid overlapping and claiming same towns)
        for city_x, city_y, nearby_towns in potential_city_locations:
            if (city_x, city_y) in occupied_tiles:
                continue
            
            # Filter out towns that are already vassals to another city
            available_towns = [t for t in nearby_towns if t not in claimed_towns and t.vassal_to is None]
            
            if len(available_towns) < 3:
                continue  # Not enough unclaimed towns
            
            # Name will be assigned from worldbuilding data later
            # Create city
            new_city = Settlement(SettlementType.CITY, city_x, city_y, name=None)
            cities.append(new_city)
            occupied_tiles.add((city_x, city_y))
            
            # Make available towns vassals of the city
            for town in available_towns:
                town.vassal_to = new_city
                new_city.vassal_towns.append(town)
                claimed_towns.add(town)
        
        print(f"Placed {len(cities)} cities")
        return cities
    
    def _has_resource_within_range(self, x: int, y: int, resource_tiles: Set[Tuple[int, int]], 
                                   max_range: int) -> bool:
        """
        Check if there's a resource tile within the specified range.
        
        Args:
            x, y: Starting coordinates
            resource_tiles: Set of resource tile coordinates
            max_range: Maximum distance to search
            
        Returns:
            True if resource found within range
        """
        # Use Manhattan distance for efficiency (faster than Euclidean)
        for rx, ry in resource_tiles:
            distance = abs(rx - x) + abs(ry - y)
            if distance <= max_range:
                return True
        return False
    
    def _has_resource_within_range_optimized(self, x: int, y: int, resource_tiles: Set[Tuple[int, int]], 
                                             max_range: int) -> bool:
        """
        Optimized version that only checks nearby tiles instead of all resource tiles.
        Much faster for small ranges.
        
        Args:
            x, y: Starting coordinates
            resource_tiles: Set of resource tile coordinates
            max_range: Maximum distance to search
            
        Returns:
            True if resource found within range
        """
        # Only check tiles within the range box (much faster for small ranges)
        for dy in range(-max_range, max_range + 1):
            for dx in range(-max_range, max_range + 1):
                # Check Manhattan distance
                if abs(dx) + abs(dy) > max_range:
                    continue
                nx, ny = x + dx, y + dy
                if (nx, ny) in resource_tiles:
                    return True
        return False
    
    def _find_village_location_fast(self, town_x: int, town_y: int, 
                                     resource_tiles: Set[Tuple[int, int]], 
                                     max_range: int,
                                     map_data: List[List[Terrain]],
                                     required_terrain: TerrainType = None,
                                     allowed_terrain: List[TerrainType] = None,
                                     is_water_village: bool = False,
                                     occupied_tiles: Set[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        Fast version: Find a suitable location for a village near a town.
        Uses a spiral search pattern starting from the town, checking closest tiles first.
        
        Args:
            town_x, town_y: Town coordinates
            resource_tiles: Set of resource tile coordinates to search near
            max_range: Maximum distance from town
            map_data: Map data to check terrain types
            required_terrain: Required terrain type for village (if specified)
            allowed_terrain: List of allowed terrain types (if specified, overrides required_terrain)
            is_water_village: If True, village must be on land adjacent to water
            
        Returns:
            (x, y) coordinates for village, or None if no suitable location found
        """
        # Use spiral search: check tiles in order of distance from town
        # This is much faster than checking all tiles in a box
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        if occupied_tiles is None:
            occupied_tiles = set()
        
        # Search in expanding rings around the town
        for distance in range(1, max_range + 1):
            # Check all tiles at this distance (Manhattan distance)
            for dy in range(-distance, distance + 1):
                for dx in range(-distance, distance + 1):
                    if abs(dx) + abs(dy) != distance:
                        continue  # Only check tiles at exactly this distance
                    
                    rx, ry = town_x + dx, town_y + dy
                    if not (0 <= rx < self.width and 0 <= ry < self.height):
                        continue
                    
                    # Check if this is a resource tile
                    if (rx, ry) not in resource_tiles:
                        continue
                    
                    # For water villages: find land adjacent to this water tile
                    if is_water_village:
                        for vdx, vdy in directions:
                            vx, vy = rx + vdx, ry + vdy
                            if 0 <= vx < self.width and 0 <= vy < self.height:
                                # Check if tile is already occupied
                                if (vx, vy) in occupied_tiles:
                                    continue
                                terrain_type = map_data[vy][vx].terrain_type
                                if terrain_type not in (TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, TerrainType.RIVER):
                                    # Check distance from town
                                    town_dist = abs(vx - town_x) + abs(vy - town_y)
                                    if town_dist <= max_range:
                                        return (vx, vy)
                    else:
                        # For other villages: check if this resource tile has the right terrain
                        # Check if tile is already occupied
                        if (rx, ry) in occupied_tiles:
                            continue
                        terrain_type = map_data[ry][rx].terrain_type
                        if allowed_terrain:
                            if terrain_type in allowed_terrain:
                                return (rx, ry)
                        elif required_terrain:
                            if terrain_type == required_terrain:
                                return (rx, ry)
                        else:
                            # No terrain requirement, use the resource tile itself
                            return (rx, ry)
        
        return None
    
    def _find_village_location(self, town_x: int, town_y: int, 
                               resource_tiles: Set[Tuple[int, int]], 
                               max_range: int,
                               map_data: List[List[Terrain]],
                               required_terrain: TerrainType = None,
                               allowed_terrain: List[TerrainType] = None,
                               is_water_village: bool = False,
                               occupied_tiles: Set[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        Find a suitable location for a village near a town.
        (Kept for backwards compatibility, but use _find_village_location_fast instead)
        
        Args:
            town_x, town_y: Town coordinates
            resource_tiles: Set of resource tile coordinates to search near
            max_range: Maximum distance from town
            map_data: Map data to check terrain types
            required_terrain: Required terrain type for village (if specified)
            allowed_terrain: List of allowed terrain types (if specified, overrides required_terrain)
            is_water_village: If True, village must be on land adjacent to water
            occupied_tiles: Set of tiles already occupied by towns or villages
            
        Returns:
            (x, y) coordinates for village, or None if no suitable location found
        """
        return self._find_village_location_fast(town_x, town_y, resource_tiles, max_range,
                                                map_data, required_terrain, allowed_terrain, is_water_village, occupied_tiles)
        
        # Try to find a suitable location near the resource
        # For water village: find a location on land adjacent to shallow water
        # For other villages: find a location on the required terrain type
        for rx, ry, _ in nearby_resources:
            # Check adjacent tiles
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    vx, vy = rx + dx, ry + dy
                    if 0 <= vx < self.width and 0 <= vy < self.height:
                        terrain_type = map_data[vy][vx].terrain_type
                        
                        # For water villages: must be on land (not water) adjacent to water
                        if is_water_village:
                            if terrain_type not in (TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER, TerrainType.RIVER):
                                # Check that this tile is adjacent to water (rx, ry is water)
                                distance = abs(vx - town_x) + abs(vy - town_y)
                                if distance <= max_range:
                                    return (vx, vy)
                        # Check if terrain is suitable
                        elif allowed_terrain:
                            if terrain_type in allowed_terrain:
                                # Check distance from town
                                distance = abs(vx - town_x) + abs(vy - town_y)
                                if distance <= max_range:
                                    return (vx, vy)
                        elif required_terrain:
                            if terrain_type == required_terrain:
                                # Check distance from town
                                distance = abs(vx - town_x) + abs(vy - town_y)
                                if distance <= max_range:
                                    return (vx, vy)
        
        # If no adjacent location found, try the resource tile itself if terrain matches
        # (but not for water villages - they must be on land)
        if not is_water_village:
            for rx, ry, _ in nearby_resources:
                if 0 <= rx < self.width and 0 <= ry < self.height:
                    terrain_type = map_data[ry][rx].terrain_type
                    if allowed_terrain:
                        if terrain_type in allowed_terrain:
                            return (rx, ry)
                    elif required_terrain:
                        if terrain_type == required_terrain:
                            return (rx, ry)
        
        return None
    
    def _assign_settlement_names_from_worldbuilding(self, settlements: List[Settlement]):
        """
        Assign settlement names from worldbuilding data.
        Extracts the name part (without title) from leader names.
        """
        if not self.worldbuilding_data:
            return
        
        cities = [s for s in settlements if s.settlement_type == SettlementType.CITY]
        towns = [s for s in settlements if s.settlement_type == SettlementType.TOWN]
        villages = [s for s in settlements if s.settlement_type == SettlementType.VILLAGE]
        
        # Assign city names
        city_index = 1
        for city in cities:
            city_key = f"City {city_index}"
            if city_key in self.worldbuilding_data:
                city_data = self.worldbuilding_data[city_key]
                if "leader" in city_data and "name" in city_data["leader"]:
                    leader_name = city_data["leader"]["name"]
                    # Extract name part (everything after the last space, which is the title)
                    # Format: "Title Name" -> "Name"
                    name_parts = leader_name.split()
                    if len(name_parts) > 1:
                        city.name = " ".join(name_parts[1:])  # Everything after the title
                    else:
                        city.name = leader_name
            city_index += 1
        
        # Assign town names (under cities)
        city_index = 1
        for city in cities:
            city_key = f"City {city_index}"
            if city_key in self.worldbuilding_data:
                city_data = self.worldbuilding_data[city_key]
                vassal_towns = [t for t in towns if t.vassal_to == city]
                town_index = 1
                for town in vassal_towns:
                    town_key = f"Vassal Town {town_index}"
                    if town_key in city_data:
                        town_data = city_data[town_key]
                        if "leader" in town_data and "name" in town_data["leader"]:
                            leader_name = town_data["leader"]["name"]
                            name_parts = leader_name.split()
                            if len(name_parts) > 1:
                                town.name = " ".join(name_parts[1:])
                            else:
                                town.name = leader_name
                    town_index += 1
            city_index += 1
        
        # Assign free town names
        free_town_key = "City NONE FOR FREE TOWN"
        if free_town_key in self.worldbuilding_data:
            free_town_data = self.worldbuilding_data[free_town_key]
            free_towns = [t for t in towns if t.vassal_to is None]
            town_index = 1
            for town in free_towns:
                town_key = f"Vassal Town {town_index}"
                if town_key in free_town_data:
                    town_data = free_town_data[town_key]
                    if "leader" in town_data and "name" in town_data["leader"]:
                        leader_name = town_data["leader"]["name"]
                        name_parts = leader_name.split()
                        if len(name_parts) > 1:
                            town.name = " ".join(name_parts[1:])
                        else:
                            town.name = leader_name
                town_index += 1
        
        # Assign village names
        city_index = 1
        for city in cities:
            city_key = f"City {city_index}"
            if city_key in self.worldbuilding_data:
                city_data = self.worldbuilding_data[city_key]
                vassal_towns = [t for t in towns if t.vassal_to == city]
                town_index = 1
                for town in vassal_towns:
                    town_key = f"Vassal Town {town_index}"
                    if town_key in city_data:
                        town_data = city_data[town_key]
                        vassal_villages = [v for v in villages if v.vassal_to == town]
                        village_index = 1
                        for village in vassal_villages:
                            village_key = f"Vassal Village {village_index}"
                            if village_key in town_data:
                                village_data = town_data[village_key]
                                # Use the "name" field from village_data (village name, not leader name)
                                if "name" in village_data:
                                    village.name = village_data["name"]
                            village_index += 1
                    town_index += 1
            city_index += 1
        
        # Assign village names for free towns
        if free_town_key in self.worldbuilding_data:
            free_town_data = self.worldbuilding_data[free_town_key]
            free_towns = [t for t in towns if t.vassal_to is None]
            town_index = 1
            for town in free_towns:
                town_key = f"Vassal Town {town_index}"
                if town_key in free_town_data:
                    town_data = free_town_data[town_key]
                    vassal_villages = [v for v in villages if v.vassal_to == town]
                    village_index = 1
                    for village in vassal_villages:
                        village_key = f"Vassal Village {village_index}"
                        if village_key in town_data:
                            village_data = town_data[village_key]
                            # Use the "name" field from village_data (village name, not leader name)
                            if "name" in village_data:
                                village.name = village_data["name"]
                        village_index += 1
                town_index += 1
    
    # Keep old methods for backwards compatibility
    def generate_random(self) -> List[List[Terrain]]:
        """Legacy method - use generate() instead."""
        return self.generate()
    
    def generate_with_clusters(self) -> List[List[Terrain]]:
        """Legacy method - use generate() instead."""
        return self.generate()

