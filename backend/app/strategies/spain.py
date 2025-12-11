"""Spain (ES) country strategy implementation."""
import random
from decimal import Decimal
from typing import Optional

from app.strategies.base import (
    BankingInfo,
    CountryStrategy,
    DocumentType,
    ValidationResult,
)


class SpainStrategy(CountryStrategy):
    """
    Strategy for processing loan applications in Spain.

    Document: DNI (Documento Nacional de Identidad)
    Currency: EUR
    Provider: Simulated Spanish banking provider
    """

    # Business rule thresholds
    REVIEW_THRESHOLD_EUR = Decimal("15000")  # Amounts above this require review
    MAX_DEBT_TO_INCOME_RATIO = Decimal("0.60")  # 60% max
    MIN_PAYMENT_HISTORY_SCORE = 50  # 0-100 scale
    MIN_ACCOUNT_AGE_MONTHS = 6

    # DNI validation constants
    DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

    @property
    def country_code(self) -> str:
        return "ES"

    @property
    def country_name(self) -> str:
        return "España"

    @property
    def currency(self) -> str:
        return "EUR"

    @property
    def supported_document_types(self) -> list[DocumentType]:
        return [DocumentType.DNI, DocumentType.NIE]

    def validate_document(
        self,
        document_type: str,
        document_number: str,
    ) -> ValidationResult:
        """
        Validate Spanish DNI or NIE.

        DNI format: 8 digits + 1 letter (e.g., 12345678Z)
        The letter is a checksum calculated from the 8 digits.
        """
        result = ValidationResult(is_valid=True)

        # Normalize input
        doc_number = document_number.upper().replace(" ", "").replace("-", "")

        if document_type.upper() == "DNI":
            result = self._validate_dni(doc_number)
        elif document_type.upper() == "NIE":
            result = self._validate_nie(doc_number)
        else:
            result.add_error(
                f"Unsupported document type '{document_type}' for Spain. "
                f"Expected DNI or NIE."
            )

        return result

    def _validate_dni(self, dni: str) -> ValidationResult:
        """Validate Spanish DNI format and checksum."""
        result = ValidationResult(is_valid=True)

        # Check length
        if len(dni) != 9:
            result.add_error(
                f"DNI must be 9 characters (8 digits + 1 letter). Got {len(dni)}."
            )
            return result

        # Check format: 8 digits + 1 letter
        number_part = dni[:-1]
        letter = dni[-1]

        if not number_part.isdigit():
            result.add_error("DNI must start with 8 digits.")
            return result

        if not letter.isalpha():
            result.add_error("DNI must end with a letter.")
            return result

        # Validate checksum letter
        expected_letter = self.DNI_LETTERS[int(number_part) % 23]
        if letter != expected_letter:
            result.add_error(
                f"Invalid DNI checksum. Expected letter '{expected_letter}'."
            )

        return result

    def _validate_nie(self, nie: str) -> ValidationResult:
        """Validate Spanish NIE format and checksum."""
        result = ValidationResult(is_valid=True)

        # Check length
        if len(nie) != 9:
            result.add_error(
                f"NIE must be 9 characters. Got {len(nie)}."
            )
            return result

        # NIE format: X/Y/Z + 7 digits + letter
        first_char = nie[0]
        if first_char not in "XYZ":
            result.add_error("NIE must start with X, Y, or Z.")
            return result

        # Convert first letter to number for checksum
        prefix_map = {"X": "0", "Y": "1", "Z": "2"}
        number_str = prefix_map[first_char] + nie[1:-1]

        if not nie[1:-1].isdigit():
            result.add_error("NIE must have 7 digits after the prefix.")
            return result

        # Validate checksum
        expected_letter = self.DNI_LETTERS[int(number_str) % 23]
        if nie[-1] != expected_letter:
            result.add_error(
                f"Invalid NIE checksum. Expected letter '{expected_letter}'."
            )

        return result

    def validate_business_rules(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Apply Spanish business rules.

        Rules:
        1. Amounts > €15,000 require manual review
        2. Debt-to-income ratio must be <= 60%
        3. Payment history score must be >= 50
        4. Account age must be >= 6 months
        """
        result = ValidationResult(is_valid=True)

        # Rule 1: High amount review
        if amount_requested > self.REVIEW_THRESHOLD_EUR:
            result.requires_review = True
            result.add_warning(
                f"Amount €{amount_requested:,.2f} exceeds review threshold "
                f"of €{self.REVIEW_THRESHOLD_EUR:,.2f}. Manual review required."
            )
            result.risk_factors["high_amount"] = True

        # Rules that require banking info
        if banking_info:
            # Rule 2: Debt-to-income ratio
            if banking_info.monthly_obligations and monthly_income > 0:
                total_monthly_debt = banking_info.monthly_obligations
                # Estimate monthly payment for requested loan (simplified)
                estimated_payment = amount_requested / 36  # 3 year term estimate
                new_debt_ratio = (total_monthly_debt + estimated_payment) / monthly_income

                result.risk_factors["debt_to_income_ratio"] = float(new_debt_ratio)

                if new_debt_ratio > self.MAX_DEBT_TO_INCOME_RATIO:
                    result.add_error(
                        f"Debt-to-income ratio {new_debt_ratio:.1%} exceeds "
                        f"maximum allowed {self.MAX_DEBT_TO_INCOME_RATIO:.0%}."
                    )

            # Rule 3: Payment history
            if banking_info.payment_history_score is not None:
                result.risk_factors["payment_history_score"] = banking_info.payment_history_score

                if banking_info.payment_history_score < self.MIN_PAYMENT_HISTORY_SCORE:
                    result.add_error(
                        f"Payment history score {banking_info.payment_history_score} "
                        f"is below minimum required {self.MIN_PAYMENT_HISTORY_SCORE}."
                    )

            # Rule 4: Account age
            if banking_info.account_age_months is not None:
                result.risk_factors["account_age_months"] = banking_info.account_age_months

                if banking_info.account_age_months < self.MIN_ACCOUNT_AGE_MONTHS:
                    result.add_warning(
                        f"Account age {banking_info.account_age_months} months "
                        f"is below recommended {self.MIN_ACCOUNT_AGE_MONTHS} months."
                    )

            # Check for defaults
            if banking_info.has_defaults:
                result.requires_review = True
                result.add_warning(
                    f"Applicant has {banking_info.default_count} previous defaults. "
                    "Manual review required."
                )
                result.risk_factors["has_defaults"] = True
                result.risk_factors["default_count"] = banking_info.default_count

        return result

    async def fetch_banking_info(
        self,
        document_type: str,
        document_number: str,
        full_name: str,
    ) -> BankingInfo:
        """
        Fetch banking info from Spanish provider (simulated).

        In production, this would call CIRBE or similar Spanish credit bureau.
        """
        # Simulate API call delay would happen here
        # await asyncio.sleep(0.1)

        # Generate simulated banking data
        # Use document hash for reproducible results in testing
        seed = hash(document_number) % 1000

        return BankingInfo(
            provider_name="CIRBE_ES",
            credit_score=600 + (seed % 300),  # 600-899
            total_debt=Decimal(str(seed * 100)),  # 0-99,900
            payment_history_score=60 + (seed % 40),  # 60-99
            account_age_months=12 + (seed % 120),  # 12-131 months
            has_defaults=seed < 100,  # 10% chance
            default_count=1 if seed < 100 else 0,
            monthly_obligations=Decimal(str(200 + (seed % 800))),  # 200-999
            available_credit=Decimal(str(5000 + (seed % 20000))),  # 5k-25k
            employment_verified=seed % 10 > 2,  # 70% verified
            income_verified=seed % 10 > 3,  # 60% verified
            raw_data={
                "provider": "CIRBE",
                "query_date": "2024-01-15",
                "report_id": f"CIRBE-{seed:06d}",
            },
        )

    def calculate_risk_score(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> int:
        """
        Calculate risk score (0-1000, lower is better).

        Factors:
        - Amount to income ratio (30%)
        - Credit score (30%)
        - Payment history (20%)
        - Defaults (20%)
        """
        score = 500  # Base score

        # Factor 1: Amount to income ratio (0-300 points)
        if monthly_income > 0:
            ratio = float(amount_requested / monthly_income)
            ratio_score = min(300, int(ratio * 50))
            score += ratio_score

        if banking_info:
            # Factor 2: Credit score (0-300 points, inverted - higher credit = lower risk)
            if banking_info.credit_score:
                # Credit score 600-900 maps to 300-0 risk
                credit_factor = max(0, 300 - (banking_info.credit_score - 600))
                score = score - 150 + credit_factor  # Adjust base

            # Factor 3: Payment history (0-200 points)
            if banking_info.payment_history_score is not None:
                # Score 0-100 maps to 200-0 risk
                history_factor = 200 - (banking_info.payment_history_score * 2)
                score += history_factor

            # Factor 4: Defaults (0-200 points)
            if banking_info.has_defaults:
                score += 100 + (banking_info.default_count * 50)

        # Clamp to 0-1000
        return max(0, min(1000, score))
