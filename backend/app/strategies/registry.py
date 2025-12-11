"""Strategy registry for country-specific implementations."""
from typing import Optional

from app.strategies.base import CountryStrategy


class StrategyRegistry:
    """
    Registry for country strategy implementations.

    Provides a central place to register and retrieve
    country-specific loan processing strategies.
    """

    _strategies: dict[str, CountryStrategy] = {}

    @classmethod
    def register(cls, strategy: CountryStrategy) -> None:
        """
        Register a country strategy.

        Args:
            strategy: The strategy instance to register
        """
        cls._strategies[strategy.country_code] = strategy

    @classmethod
    def get(cls, country_code: str) -> Optional[CountryStrategy]:
        """
        Get a strategy by country code.

        Args:
            country_code: ISO 2-letter country code

        Returns:
            The strategy instance or None if not found
        """
        return cls._strategies.get(country_code.upper())

    @classmethod
    def get_or_raise(cls, country_code: str) -> CountryStrategy:
        """
        Get a strategy by country code or raise an error.

        Args:
            country_code: ISO 2-letter country code

        Returns:
            The strategy instance

        Raises:
            ValueError: If country is not supported
        """
        strategy = cls.get(country_code)
        if strategy is None:
            supported = ", ".join(cls.get_all_country_codes())
            raise ValueError(
                f"Country '{country_code}' is not supported. "
                f"Supported countries: {supported}"
            )
        return strategy

    @classmethod
    def get_all_country_codes(cls) -> list[str]:
        """
        Get all registered country codes.

        Returns:
            List of ISO 2-letter country codes
        """
        return list(cls._strategies.keys())

    @classmethod
    def is_supported(cls, country_code: str) -> bool:
        """
        Check if a country is supported.

        Args:
            country_code: ISO 2-letter country code

        Returns:
            True if the country has a registered strategy
        """
        return country_code.upper() in cls._strategies

    @classmethod
    def get_all_strategies(cls) -> dict[str, CountryStrategy]:
        """
        Get all registered strategies.

        Returns:
            Dictionary mapping country codes to strategies
        """
        return cls._strategies.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered strategies (useful for testing)."""
        cls._strategies.clear()
