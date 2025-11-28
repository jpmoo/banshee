"""
Simple Perlin noise implementation for map generation.
"""
import math
import random
from typing import List


class PerlinNoise:
    """Simple Perlin noise generator."""
    
    def __init__(self, seed: int = None):
        """Initialize the Perlin noise generator."""
        if seed is not None:
            random.seed(seed)
        
        # Generate permutation table
        self.permutation = list(range(256))
        random.shuffle(self.permutation)
        self.permutation += self.permutation  # Duplicate for wrapping
    
    def _fade(self, t: float) -> float:
        """Fade function for smooth interpolation."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Gradient function."""
        h = hash_val & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x: float, y: float) -> float:
        """
        Generate 2D Perlin noise value at (x, y).
        Returns value in range approximately [-1, 1].
        """
        # Find unit grid cell containing point
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        # Get relative x, y coordinates of point within that cell
        x -= math.floor(x)
        y -= math.floor(y)
        
        # Compute fade curves for each coordinate
        u = self._fade(x)
        v = self._fade(y)
        
        # Hash coordinates of the 4 square corners
        A = self.permutation[X] + Y
        AA = self.permutation[A]
        AB = self.permutation[A + 1]
        B = self.permutation[X + 1] + Y
        BA = self.permutation[B]
        BB = self.permutation[B + 1]
        
        # And add blended results from 4 corners of the square
        return self._lerp(
            self._lerp(
                self._grad(self.permutation[AA], x, y),
                self._grad(self.permutation[BA], x - 1, y),
                u
            ),
            self._lerp(
                self._grad(self.permutation[AB], x, y - 1),
                self._grad(self.permutation[BB], x - 1, y - 1),
                u
            ),
            v
        )
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, scale: float = 1.0) -> float:
        """
        Generate octave noise (fractal noise) by combining multiple noise layers.
        
        Args:
            x, y: Coordinates
            octaves: Number of noise layers
            persistence: Amplitude multiplier for each octave
            scale: Scale factor for coordinates
            
        Returns:
            Noise value in range approximately [-1, 1]
        """
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        
        for _ in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        
        return value / max_value







