"""Country Strategies Package.

This module provides the Strategy pattern implementation for
country-specific loan processing rules and validations.
"""
from app.strategies.base import (
    BankingInfo,
    CountryStrategy,
    DocumentType,
    ValidationResult,
)
from app.strategies.brazil import BrazilStrategy
from app.strategies.colombia import ColombiaStrategy
from app.strategies.mexico import MexicoStrategy
from app.strategies.registry import StrategyRegistry
from app.strategies.spain import SpainStrategy

# Register all country strategies
StrategyRegistry.register(SpainStrategy())
StrategyRegistry.register(MexicoStrategy())
StrategyRegistry.register(ColombiaStrategy())
StrategyRegistry.register(BrazilStrategy())

__all__ = [
    # Base classes
    "CountryStrategy",
    "DocumentType",
    "ValidationResult",
    "BankingInfo",
    # Registry
    "StrategyRegistry",
    # Country implementations
    "SpainStrategy",
    "MexicoStrategy",
    "ColombiaStrategy",
    "BrazilStrategy",
]
