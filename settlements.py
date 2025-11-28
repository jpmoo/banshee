"""
Settlement system for the RPG map.
Settlements are placed based on resource distribution.
"""
from enum import Enum
from typing import Tuple, List, Set, Optional


class SettlementType(Enum):
    """Types of settlements."""
    TOWN = "town"
    VILLAGE = "village"
    CITY = "city"


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
        
        # Economy tracking
        # Resources (only for towns)
        if settlement_type == SettlementType.TOWN:
            self.resources = {
                'lumber': 0,
                'fish and fowl': 0,
                'grain and livestock': 0,
                'ore': 0
            }
        else:
            self.resources = None
        
        # Trade goods (for towns and cities)
        if settlement_type in [SettlementType.TOWN, SettlementType.CITY]:
            self.trade_goods = 0
        else:
            self.trade_goods = None
        
        # Money placeholder (for towns and cities)
        if settlement_type in [SettlementType.TOWN, SettlementType.CITY]:
            self.money = 0  # Placeholder for future implementation
        else:
            self.money = None
    
    def get_position(self) -> Tuple[int, int]:
        """Get the position of the settlement."""
        return (self.x, self.y)
    
    def add_resource(self, resource: str, amount: int = 10):
        """
        Add resources to a town.
        
        Args:
            resource: Resource type (lumber, fish and fowl, grain and livestock, ore)
            amount: Amount to add (default 10)
        """
        if self.settlement_type != SettlementType.TOWN:
            return
        
        if resource in self.resources:
            self.resources[resource] += amount
    
    def produce_trade_goods(self) -> int:
        """
        Produce trade goods from resources if town has 100 of each resource.
        Consumes 100 of each resource per trade good produced.
        
        Returns:
            Number of trade goods produced
        """
        if self.settlement_type != SettlementType.TOWN:
            return 0
        
        trade_goods_produced = 0
        
        # Check if we have enough resources to produce trade goods
        # Need 100 of each resource per trade good
        while all(self.resources[res] >= 100 for res in self.resources):
            # Consume 100 of each resource
            for resource in self.resources:
                self.resources[resource] -= 100
            # Produce 1 trade good
            self.trade_goods += 1
            trade_goods_produced += 1
        
        return trade_goods_produced
    
    def transfer_trade_goods_to_liege(self) -> int:
        """
        Transfer trade goods to liege city if town has 10 or more.
        Resets town's trade goods to 0 after transfer.
        
        Returns:
            Number of trade goods transferred
        """
        if self.settlement_type != SettlementType.TOWN:
            return 0
        
        if not self.vassal_to or self.vassal_to.settlement_type != SettlementType.CITY:
            return 0
        
        if self.trade_goods >= 10:
            transferred = self.trade_goods
            self.vassal_to.trade_goods += transferred
            self.trade_goods = 0
            return transferred
        
        return 0

