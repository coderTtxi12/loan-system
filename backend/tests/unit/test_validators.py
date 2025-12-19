"""Unit tests for validation utilities."""
import pytest
from decimal import Decimal

from app.strategies.base import ValidationResult


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_initial_state(self):
        """Test initial validation result state."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.requires_review is False
        assert result.risk_factors == {}

    def test_add_error(self):
        """Test adding error."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding warning."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        assert len(result.warnings) == 1
        assert "Test warning" in result.warnings
        # Warnings don't make result invalid
        assert result.is_valid is True

    def test_merge_results(self):
        """Test merging two validation results."""
        result1 = ValidationResult(is_valid=True)
        result1.add_warning("Warning 1")
        result1.risk_factors["factor1"] = "value1"

        result2 = ValidationResult(is_valid=True)
        result2.add_error("Error 1")
        result2.requires_review = True
        result2.risk_factors["factor2"] = "value2"

        merged = result1.merge(result2)
        assert merged.is_valid is False  # Has error
        assert merged.requires_review is True
        assert "Warning 1" in merged.warnings
        assert "Error 1" in merged.errors
        assert merged.risk_factors["factor1"] == "value1"
        assert merged.risk_factors["factor2"] == "value2"

    def test_merge_preserves_requires_review(self):
        """Test that merge preserves requires_review flag."""
        result1 = ValidationResult(is_valid=True, requires_review=True)
        result2 = ValidationResult(is_valid=True, requires_review=False)
        
        merged = result1.merge(result2)
        assert merged.requires_review is True  # OR operation
