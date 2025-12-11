"""Brazil (BR) country strategy implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.strategies.base import (
    BankingInfo,
    CountryStrategy,
    DocumentType,
    ValidationResult,
)


class BrazilStrategy(CountryStrategy):
    """
    Strategy for processing loan applications in Brazil.

    Document: CPF (Cadastro de Pessoas Físicas)
    Currency: BRL
    Provider: Simulated Serasa/SPC Brasil
    """

    # Business rule thresholds
    REVIEW_THRESHOLD_BRL = Decimal("100000")  # 100k BRL requires review
    MIN_SERASA_SCORE = 500  # 0-1000 scale
    MAX_COMMITMENT_RATIO = Decimal("0.35")  # 35% max of income committed

    @property
    def country_code(self) -> str:
        return "BR"

    @property
    def country_name(self) -> str:
        return "Brasil"

    @property
    def currency(self) -> str:
        return "BRL"

    @property
    def supported_document_types(self) -> list[DocumentType]:
        return [DocumentType.CPF]

    def validate_document(
        self,
        document_type: str,
        document_number: str,
    ) -> ValidationResult:
        """
        Validate Brazilian CPF.

        CPF format: 11 digits (XXX.XXX.XXX-XX or XXXXXXXXXXX)
        Includes two check digits calculated using modulo 11.
        """
        result = ValidationResult(is_valid=True)

        if document_type.upper() != "CPF":
            result.add_error(
                f"Unsupported document type '{document_type}' for Brazil. "
                f"Expected CPF."
            )
            return result

        # Normalize: remove dots, dashes, spaces
        cpf = document_number.replace(".", "").replace("-", "").replace(" ", "")

        # Check length
        if len(cpf) != 11:
            result.add_error(
                f"CPF must be 11 digits. Got {len(cpf)}."
            )
            return result

        # Check if all digits
        if not cpf.isdigit():
            result.add_error("CPF must contain only digits.")
            return result

        # Check for invalid CPFs (all same digit)
        if cpf == cpf[0] * 11:
            result.add_error(
                "Invalid CPF: all digits are the same."
            )
            return result

        # Validate check digits
        if not self._validate_cpf_check_digits(cpf):
            result.add_error(
                "Invalid CPF: check digits do not match."
            )

        return result

    def _validate_cpf_check_digits(self, cpf: str) -> bool:
        """
        Validate CPF check digits using modulo 11 algorithm.

        First check digit: weighted sum of first 9 digits
        Second check digit: weighted sum of first 10 digits
        """
        # Calculate first check digit
        total = 0
        for i, digit in enumerate(cpf[:9]):
            total += int(digit) * (10 - i)

        remainder = total % 11
        first_check = 0 if remainder < 2 else 11 - remainder

        if int(cpf[9]) != first_check:
            return False

        # Calculate second check digit
        total = 0
        for i, digit in enumerate(cpf[:10]):
            total += int(digit) * (11 - i)

        remainder = total % 11
        second_check = 0 if remainder < 2 else 11 - remainder

        return int(cpf[10]) == second_check

    def validate_business_rules(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Apply Brazilian business rules.

        Rules:
        1. Amounts > BRL 100,000 require manual review
        2. Serasa score must be >= 500
        3. Monthly commitment (including new loan) <= 35% of income
        """
        result = ValidationResult(is_valid=True)

        # Rule 1: High amount review
        if amount_requested > self.REVIEW_THRESHOLD_BRL:
            result.requires_review = True
            result.add_warning(
                f"Amount R$ {amount_requested:,.2f} exceeds review threshold "
                f"of R$ {self.REVIEW_THRESHOLD_BRL:,.2f}. Manual review required."
            )
            result.risk_factors["high_amount"] = True

        # Rule 2: Serasa score
        if banking_info and banking_info.credit_score is not None:
            result.risk_factors["serasa_score"] = banking_info.credit_score

            if banking_info.credit_score < self.MIN_SERASA_SCORE:
                result.add_error(
                    f"Serasa score {banking_info.credit_score} "
                    f"is below minimum required {self.MIN_SERASA_SCORE}."
                )

            # Check for negative records (SPC/Serasa)
            if banking_info.has_defaults:
                result.requires_review = True
                result.add_warning(
                    f"Applicant has {banking_info.default_count} negative records "
                    "in Serasa/SPC. Manual review required."
                )
                result.risk_factors["negativado"] = True

        # Rule 3: Monthly commitment ratio
        if monthly_income > 0:
            # Estimate monthly payment (36 months term typical in Brazil)
            estimated_payment = amount_requested / 36
            existing_obligations = Decimal("0")

            if banking_info and banking_info.monthly_obligations:
                existing_obligations = banking_info.monthly_obligations

            total_commitment = existing_obligations + estimated_payment
            commitment_ratio = total_commitment / monthly_income

            result.risk_factors["commitment_ratio"] = float(commitment_ratio)
            result.risk_factors["estimated_payment"] = float(estimated_payment)

            if commitment_ratio > self.MAX_COMMITMENT_RATIO:
                result.add_error(
                    f"Monthly commitment ratio {commitment_ratio:.1%} exceeds "
                    f"maximum allowed {self.MAX_COMMITMENT_RATIO:.0%}."
                )
        else:
            result.add_error("Monthly income must be greater than zero.")

        return result

    async def fetch_banking_info(
        self,
        document_type: str,
        document_number: str,
        full_name: str,
    ) -> BankingInfo:
        """
        Fetch banking info from Serasa/SPC Brasil (simulated).

        In production, this would call the actual Serasa API.
        """
        seed = hash(document_number) % 1000

        # Serasa score is 0-1000
        serasa_score = 300 + (seed % 600)  # 300-899

        return BankingInfo(
            provider_name="SERASA_BR",
            credit_score=serasa_score,
            total_debt=Decimal(str(seed * 200)),  # 0-199,800 BRL
            payment_history_score=45 + (seed % 55),  # 45-99
            account_age_months=6 + (seed % 150),  # 6-155 months
            has_defaults=seed < 180,  # 18% chance (negativado)
            default_count=1 if seed < 120 else (2 if seed < 180 else 0),
            monthly_obligations=Decimal(str(500 + (seed % 5000))),  # 500-5,500 BRL
            available_credit=Decimal(str(2000 + (seed % 30000))),  # 2k-32k BRL
            employment_verified=seed % 10 > 3,  # 60% verified
            income_verified=seed % 10 > 4,  # 50% verified
            raw_data={
                "provider": "Serasa Experian",
                "query_date": datetime.now().isoformat(),
                "protocol": f"SERASA-{seed:010d}",
                "score_type": "Serasa Score",
                "negativado": seed < 180,
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
        - Serasa score (40%)
        - Commitment ratio (30%)
        - Negative records (30%)
        """
        score = 400  # Base score

        # Factor 1: Commitment ratio (0-300 points)
        if monthly_income > 0:
            estimated_payment = amount_requested / 36
            existing = Decimal("0")
            if banking_info and banking_info.monthly_obligations:
                existing = banking_info.monthly_obligations

            commitment_ratio = float((existing + estimated_payment) / monthly_income)
            # 35%+ commitment = max points
            ratio_score = min(300, int(commitment_ratio * 857))
            score += ratio_score

        if banking_info:
            # Factor 2: Serasa score (0-400 points, inverted)
            if banking_info.credit_score:
                # Score 300-900 maps to 400-0 risk
                serasa_factor = max(0, 400 - int((banking_info.credit_score - 300) * 0.67))
                score = score - 200 + serasa_factor

            # Factor 3: Negative records (0-300 points)
            if banking_info.has_defaults:
                score += 150 + (banking_info.default_count * 75)

        return max(0, min(1000, score))
