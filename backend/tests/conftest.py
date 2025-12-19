"""Pytest configuration and fixtures."""
import pytest
from decimal import Decimal

from app.strategies.base import BankingInfo


@pytest.fixture
def sample_banking_info():
    """Sample banking info for testing."""
    return BankingInfo(
        provider_name="TEST_PROVIDER",
        credit_score=650,
        total_debt=Decimal("50000"),
        payment_history_score=75,
        account_age_months=24,
        has_defaults=False,
        default_count=0,
        monthly_obligations=Decimal("5000"),
        available_credit=Decimal("100000"),
        employment_verified=True,
        income_verified=True,
    )


@pytest.fixture
def banking_info_with_defaults():
    """Banking info with defaults for testing."""
    return BankingInfo(
        provider_name="TEST_PROVIDER",
        credit_score=550,
        total_debt=Decimal("80000"),
        payment_history_score=60,
        account_age_months=12,
        has_defaults=True,
        default_count=2,
        monthly_obligations=Decimal("8000"),
        available_credit=Decimal("50000"),
        employment_verified=True,
        income_verified=False,
    )


@pytest.fixture
def low_credit_score_banking_info():
    """Banking info with low credit score."""
    return BankingInfo(
        provider_name="TEST_PROVIDER",
        credit_score=450,
        total_debt=Decimal("100000"),
        payment_history_score=50,
        account_age_months=6,
        has_defaults=False,
        default_count=0,
        monthly_obligations=Decimal("10000"),
        available_credit=Decimal("20000"),
        employment_verified=False,
        income_verified=False,
    )
