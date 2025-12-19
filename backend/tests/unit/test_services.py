"""Unit tests for services."""
import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.loan_service import LoanService
from app.strategies.base import BankingInfo, ValidationResult
from app.models.loan import LoanStatus


class TestLoanService:
    """Tests for LoanService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_strategy_registry(self):
        """Mock strategy registry."""
        with patch('app.services.loan_service.StrategyRegistry') as mock:
            yield mock

    @pytest.fixture
    def mock_strategy(self):
        """Mock country strategy."""
        strategy = Mock()
        strategy.country_code = "MX"
        strategy.currency = "MXN"
        strategy.validate_document = Mock(return_value=ValidationResult(is_valid=True))
        strategy.validate_business_rules = Mock(return_value=ValidationResult(is_valid=True))
        strategy.calculate_risk_score = Mock(return_value=500)
        strategy.fetch_banking_info = AsyncMock(return_value=BankingInfo(
            provider_name="BURO_CREDITO_MX",
            credit_score=600,
        ))
        return strategy

    @pytest.mark.asyncio
    async def test_create_loan_application_success(self, mock_db_session, mock_strategy_registry, mock_strategy):
        """Test successful loan application creation."""
        # Setup mocks
        mock_strategy_registry.is_supported.return_value = True
        mock_strategy_registry.get_or_raise.return_value = mock_strategy

        # Mock repositories
        with patch('app.services.loan_service.LoanRepository') as mock_repo_class, \
             patch('app.services.loan_service.JobRepository') as mock_job_repo_class:
            
            mock_loan_repo = Mock()
            mock_loan_repo.get_by_document_hash = AsyncMock(return_value=None)
            mock_loan_repo.create = AsyncMock(return_value=Mock(
                id=uuid4(),
                status=LoanStatus.PENDING,
            ))
            mock_repo_class.return_value = mock_loan_repo

            mock_job_repo = Mock()
            mock_job_repo.enqueue = AsyncMock()
            mock_job_repo_class.return_value = mock_job_repo

            service = LoanService(mock_db_session)

            # Create loan application
            result = await service.create_loan_application(
                country_code="MX",
                document_type="CURP",
                document_number="KYBB010115HDFDFCX0",
                full_name="John Doe",
                amount_requested=Decimal("10000"),
                monthly_income=Decimal("50000"),
            )

            # Verify
            assert result is not None
            mock_strategy.validate_document.assert_called_once()
            mock_strategy.validate_business_rules.assert_called_once()
            mock_loan_repo.create.assert_called_once()
            mock_job_repo.enqueue.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_loan_application_invalid_document(self, mock_db_session, mock_strategy_registry, mock_strategy):
        """Test loan application with invalid document."""
        from app.core.exceptions import ValidationError

        # Setup mocks
        mock_strategy_registry.is_supported.return_value = True
        mock_strategy_registry.get_or_raise.return_value = mock_strategy
        mock_strategy.validate_document.return_value = ValidationResult(
            is_valid=False,
            errors=["Invalid document format"]
        )

        service = LoanService(mock_db_session)

        # Attempt to create loan application
        with pytest.raises(ValidationError) as exc_info:
            await service.create_loan_application(
                country_code="MX",
                document_type="CURP",
                document_number="INVALID",
                full_name="John Doe",
                amount_requested=Decimal("10000"),
                monthly_income=Decimal("50000"),
            )

        assert "Document validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_loan_application_business_rules_fail(self, mock_db_session, mock_strategy_registry, mock_strategy):
        """Test loan application failing business rules."""
        from app.core.exceptions import ValidationError

        # Setup mocks
        mock_strategy_registry.is_supported.return_value = True
        mock_strategy_registry.get_or_raise.return_value = mock_strategy
        mock_strategy.validate_business_rules.return_value = ValidationResult(
            is_valid=False,
            errors=["Credit score too low"]
        )

        service = LoanService(mock_db_session)

        # Attempt to create loan application
        with pytest.raises(ValidationError) as exc_info:
            await service.create_loan_application(
                country_code="MX",
                document_type="CURP",
                document_number="KYBB010115HDFDFCX0",
                full_name="John Doe",
                amount_requested=Decimal("10000"),
                monthly_income=Decimal("50000"),
            )

        assert "Business rules validation failed" in str(exc_info.value)
