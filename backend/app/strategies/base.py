"""Base strategy pattern for country-specific loan processing."""
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


class DocumentType(str, enum.Enum):
    """Document types by country."""

    # Spain
    DNI = "DNI"  # Documento Nacional de Identidad
    NIE = "NIE"  # Número de Identidad de Extranjero

    # Mexico
    CURP = "CURP"  # Clave Única de Registro de Población

    # Colombia
    CC = "CC"  # Cédula de Ciudadanía
    CE = "CE"  # Cédula de Extranjería

    # Brazil
    CPF = "CPF"  # Cadastro de Pessoas Físicas


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_review: bool = False
    risk_factors: dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            requires_review=self.requires_review or other.requires_review,
            risk_factors={**self.risk_factors, **other.risk_factors},
        )


@dataclass
class BankingInfo:
    """Banking information from external provider."""

    provider_name: str
    credit_score: Optional[int] = None  # 0-1000 typically
    total_debt: Optional[Decimal] = None
    payment_history_score: Optional[int] = None  # 0-100
    account_age_months: Optional[int] = None
    has_defaults: bool = False
    default_count: int = 0
    monthly_obligations: Optional[Decimal] = None
    available_credit: Optional[Decimal] = None
    employment_verified: bool = False
    income_verified: bool = False
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "provider_name": self.provider_name,
            "credit_score": self.credit_score,
            "total_debt": str(self.total_debt) if self.total_debt else None,
            "payment_history_score": self.payment_history_score,
            "account_age_months": self.account_age_months,
            "has_defaults": self.has_defaults,
            "default_count": self.default_count,
            "monthly_obligations": str(self.monthly_obligations) if self.monthly_obligations else None,
            "available_credit": str(self.available_credit) if self.available_credit else None,
            "employment_verified": self.employment_verified,
            "income_verified": self.income_verified,
        }


class CountryStrategy(ABC):
    """
    Abstract base class for country-specific loan processing.

    Each country implementation must provide:
    - Document validation
    - Business rules validation
    - Banking provider integration
    - Risk score calculation
    """

    @property
    @abstractmethod
    def country_code(self) -> str:
        """ISO 2-letter country code."""
        ...

    @property
    @abstractmethod
    def country_name(self) -> str:
        """Human-readable country name."""
        ...

    @property
    @abstractmethod
    def currency(self) -> str:
        """Default currency code (ISO 4217)."""
        ...

    @property
    @abstractmethod
    def supported_document_types(self) -> list[DocumentType]:
        """List of supported document types for this country."""
        ...

    @abstractmethod
    def validate_document(
        self,
        document_type: str,
        document_number: str,
    ) -> ValidationResult:
        """
        Validate the document number format and checksum.

        Args:
            document_type: Type of document (DNI, CURP, etc.)
            document_number: The document number to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        ...

    @abstractmethod
    def validate_business_rules(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Apply country-specific business rules.

        Args:
            amount_requested: Loan amount requested
            monthly_income: Applicant's monthly income
            banking_info: Optional banking information from provider

        Returns:
            ValidationResult with validation status and risk factors
        """
        ...

    @abstractmethod
    async def fetch_banking_info(
        self,
        document_type: str,
        document_number: str,
        full_name: str,
    ) -> BankingInfo:
        """
        Fetch banking information from the country's provider.

        Args:
            document_type: Type of document
            document_number: The document number
            full_name: Applicant's full name

        Returns:
            BankingInfo from the external provider
        """
        ...

    @abstractmethod
    def calculate_risk_score(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> int:
        """
        Calculate a risk score for the application.

        Args:
            amount_requested: Loan amount requested
            monthly_income: Applicant's monthly income
            banking_info: Optional banking information

        Returns:
            Risk score from 0 (lowest risk) to 1000 (highest risk)
        """
        ...

    def validate_all(
        self,
        document_type: str,
        document_number: str,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Run all validations (document + business rules).

        Args:
            document_type: Type of document
            document_number: The document number
            amount_requested: Loan amount requested
            monthly_income: Applicant's monthly income
            banking_info: Optional banking information

        Returns:
            Combined ValidationResult
        """
        doc_result = self.validate_document(document_type, document_number)
        rules_result = self.validate_business_rules(
            amount_requested, monthly_income, banking_info
        )
        return doc_result.merge(rules_result)
