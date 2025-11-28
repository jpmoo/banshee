"""
Settlement system for the RPG map.
Settlements are placed based on resource distribution.
"""
from enum import Enum
from typing import Tuple, List, Set, Optional, Dict


class SettlementType(Enum):
    """Types of settlements."""
    TOWN = "town"
    VILLAGE = "village"
    CITY = "city"


# Standard resource names (4 resources total)
RESOURCES = ["lumber", "fish", "agricultural", "ore"]

# Map old resource names to standard names
RESOURCE_NAME_MAP = {
    "fish and fowl": "fish",
    "grain and livestock": "agricultural",
    "lumber": "lumber",
    "ore": "ore",
    "fish": "fish",
    "agricultural": "agricultural"
}


def normalize_resource_name(resource: str) -> str:
    """Normalize resource names to standard format."""
    return RESOURCE_NAME_MAP.get(resource, resource)


class Settlement:
    """Represents a settlement on the map."""
    
    def __init__(self, settlement_type: SettlementType, x: int, y: int, name: str = None, 
                 vassal_to: Optional['Settlement'] = None, supplies_resource: str = None):
        """
        Initialize a settlement.
        
        Args:
            settlement_type: Type of settlement
            x: X coordinate in tiles
            y: Y coordinate in tiles
            name: Optional name for the settlement
            vassal_to: For villages, the town this village is vassal to
            supplies_resource: For villages, the resource this village supplies to its town
        """
        self.settlement_type = settlement_type
        self.x = x
        self.y = y
        self.name = name
        self.vassal_to = vassal_to  # For villages: the town they serve; for towns: the city they serve
        self.vassal_villages = []  # For towns: list of villages that are vassals
        self.vassal_towns = []  # For cities: list of towns that are vassals
        self.supplies_resource = supplies_resource  # For villages: resource they supply
        self.resource_villages = {}  # For towns: dict mapping resource names to villages
        
        # Economy system
        # Resources: only towns and cities have resources
        self.resources: Dict[str, int] = {resource: 0 for resource in RESOURCES}
        # Trade goods: only towns and cities have trade goods
        self.trade_goods: int = 0
        # Money: placeholder for all settlements
        self.money: int = 0
    
    def get_position(self) -> Tuple[int, int]:
        """Get the position of the settlement."""
        return (self.x, self.y)
    
    def add_resource_from_caravan(self, resource: str, amount: int = 10):
        """
        Add resources from a caravan arrival.
        Only towns can receive resources from caravans.
        
        Args:
            resource: The resource type (will be normalized)
            amount: Amount of resource to add (default 10)
        """
        if self.settlement_type != SettlementType.TOWN:
            return
        
        normalized_resource = normalize_resource_name(resource)
        if normalized_resource in self.resources:
            self.resources[normalized_resource] += amount
            # Check if we can create trade goods
            self._check_and_create_trade_goods()
    
    def _check_and_create_trade_goods(self):
        """
        Check if town has 100 of each resource and create a trade good if so.
        Keeps excess resources.
        """
        if self.settlement_type != SettlementType.TOWN:
            return
        
        # Check if we have at least 100 of each resource
        can_create = all(self.resources[resource] >= 100 for resource in RESOURCES)
        
        if can_create:
            # Create one trade good
            self.trade_goods += 1
            # Deduct 100 of each resource (keep excess)
            for resource in RESOURCES:
                self.resources[resource] -= 100
            
            # Check if we need to transfer trade goods to city
            self._check_and_transfer_trade_goods()
    
    def _check_and_transfer_trade_goods(self):
        """
        If town has 10 or more trade goods and is vassal to a city,
        transfer 10 trade goods to the city and reset counter.
        """
        if self.settlement_type != SettlementType.TOWN:
            return
        
        if self.trade_goods >= 10 and self.vassal_to and self.vassal_to.settlement_type == SettlementType.CITY:
            # Transfer 10 trade goods to city
            self.vassal_to.trade_goods += 10
            self.trade_goods -= 10
    
    def process_economy(self):
        """
        Process economy updates for this settlement.
        Should be called periodically (e.g., each game tick).
        """
        if self.settlement_type == SettlementType.TOWN:
            # Check if we can create trade goods (in case resources were added externally)
            self._check_and_create_trade_goods()
            # Check if we need to transfer trade goods
            self._check_and_transfer_trade_goods()

