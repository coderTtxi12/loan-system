"""Colombia (CO) country strategy implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.strategies.base import (
    BankingInfo,
    CountryStrategy,
    DocumentType,
    ValidationResult,
)


class ColombiaStrategy(CountryStrategy):
    """
    Strategy for processing loan applications in Colombia.

    Document: CC (Cédula de Ciudadanía) or CE (Cédula de Extranjería)
    Currency: COP
    Provider: Simulated DataCrédito/TransUnion Colombia
    """

    # Business rule thresholds
    REVIEW_THRESHOLD_COP = Decimal("50000000")  # 50M COP requires review
    MAX_TOTAL_DEBT_TO_INCOME_RATIO = Decimal("0.50")  # 50% max
    MIN_CREDIT_SCORE = 500

    @property
    def country_code(self) -> str:
        return "CO"

    @property
    def country_name(self) -> str:
        return "Colombia"

    @property
    def currency(self) -> str:
        return "COP"

    @property
    def supported_document_types(self) -> list[DocumentType]:
        return [DocumentType.CC, DocumentType.CE]

    def validate_document(
        self,
        document_type: str,
        document_number: str,
    ) -> ValidationResult:
        """
        Validate Colombian Cédula de Ciudadanía or Cédula de Extranjería.

        CC format: 6-10 digits
        CE format: 6-7 digits (for foreigners)
        """
        result = ValidationResult(is_valid=True)

        # Normalize input
        doc_number = document_number.replace(" ", "").replace("-", "").replace(".", "")

        if document_type.upper() == "CC":
            result = self._validate_cc(doc_number)
        elif document_type.upper() == "CE":
            result = self._validate_ce(doc_number)
        else:
            result.add_error(
                f"Unsupported document type '{document_type}' for Colombia. "
                f"Expected CC or CE."
            )

        return result

    def _validate_cc(self, cc: str) -> ValidationResult:
        """Validate Colombian Cédula de Ciudadanía."""
        result = ValidationResult(is_valid=True)

        # Check if all digits
        if not cc.isdigit():
            result.add_error("Cédula de Ciudadanía must contain only digits.")
            return result

        # Check length (6-10 digits)
        if len(cc) < 6 or len(cc) > 10:
            result.add_error(
                f"Cédula de Ciudadanía must be 6-10 digits. Got {len(cc)}."
            )
            return result

        # Basic validation: first digit should not be 0
        if cc[0] == "0":
            result.add_error("Cédula de Ciudadanía cannot start with 0.")

        return result

    def _validate_ce(self, ce: str) -> ValidationResult:
        """Validate Colombian Cédula de Extranjería."""
        result = ValidationResult(is_valid=True)

        # Check if all digits
        if not ce.isdigit():
            result.add_error("Cédula de Extranjería must contain only digits.")
            return result

        # Check length (6-7 digits typically)
        if len(ce) < 6 or len(ce) > 7:
            result.add_error(
                f"Cédula de Extranjería must be 6-7 digits. Got {len(ce)}."
            )

        return result

    def validate_business_rules(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Apply Colombian business rules.

        Rules:
        1. Amounts > COP 50,000,000 require manual review
        2. Total debt (existing + new) to income ratio <= 50%
        3. Credit score must be >= 500
        """
        result = ValidationResult(is_valid=True)

        # Rule 1: High amount review
        if amount_requested > self.REVIEW_THRESHOLD_COP:
            result.requires_review = True
            result.add_warning(
                f"Amount COP ${amount_requested:,.0f} exceeds review threshold "
                f"of COP ${self.REVIEW_THRESHOLD_COP:,.0f}. Manual review required."
            )
            result.risk_factors["high_amount"] = True

        # Rule 2: Total debt to income ratio
        if banking_info and monthly_income > 0:
            existing_debt = banking_info.monthly_obligations or Decimal("0")
            # Estimate new monthly payment (simplified: 48 months term)
            estimated_new_payment = amount_requested / 48

            total_monthly_debt = existing_debt + estimated_new_payment
            debt_ratio = total_monthly_debt / monthly_income

            result.risk_factors["total_debt_to_income_ratio"] = float(debt_ratio)
            result.risk_factors["existing_monthly_debt"] = float(existing_debt)
            result.risk_factors["estimated_new_payment"] = float(estimated_new_payment)

            if debt_ratio > self.MAX_TOTAL_DEBT_TO_INCOME_RATIO:
                result.add_error(
                    f"Total debt-to-income ratio {debt_ratio:.1%} exceeds "
                    f"maximum allowed {self.MAX_TOTAL_DEBT_TO_INCOME_RATIO:.0%}."
                )

            # Check existing total debt from DataCrédito
            if banking_info.total_debt:
                total_debt_ratio = banking_info.total_debt / (monthly_income * 12)
                result.risk_factors["annual_debt_ratio"] = float(total_debt_ratio)

                if total_debt_ratio > 2:  # More than 2x annual income in debt
                    result.add_warning(
                        f"Existing debt is {total_debt_ratio:.1f}x annual income. "
                        "Higher risk applicant."
                    )

        # Rule 3: Credit score
        if banking_info and banking_info.credit_score is not None:
            result.risk_factors["credit_score"] = banking_info.credit_score

            if banking_info.credit_score < self.MIN_CREDIT_SCORE:
                result.add_error(
                    f"DataCrédito score {banking_info.credit_score} "
                    f"is below minimum required {self.MIN_CREDIT_SCORE}."
                )

            # Defaults check
            if banking_info.has_defaults:
                result.requires_review = True
                result.add_warning(
                    f"Applicant reported in centrales de riesgo with "
                    f"{banking_info.default_count} negative records."
                )
                result.risk_factors["has_defaults"] = True

        return result

    async def fetch_banking_info(
        self,
        document_type: str,
        document_number: str,
        full_name: str,
    ) -> BankingInfo:
        """
        Fetch banking info from DataCrédito/TransUnion (simulated).

        In production, this would call the actual DataCrédito API.
        """
        seed = hash(document_number) % 1000

        # Colombian credit scores typically 150-950
        credit_score = 300 + (seed % 500)  # 300-799

        return BankingInfo(
            provider_name="DATACREDITO_CO",
            credit_score=credit_score,
            total_debt=Decimal(str(seed * 50000)),  # 0-49.95M COP
            payment_history_score=40 + (seed % 60),  # 40-99
            account_age_months=3 + (seed % 120),  # 3-122 months
            has_defaults=seed < 200,  # 20% chance
            default_count=1 if seed < 150 else (2 if seed < 200 else 0),
            monthly_obligations=Decimal(str(200000 + (seed % 3000000))),  # 200k-3.2M COP
            available_credit=Decimal(str(1000000 + (seed % 20000000))),  # 1M-21M COP
            employment_verified=seed % 10 > 4,  # 50% verified
            income_verified=seed % 10 > 5,  # 40% verified
            raw_data={
                "provider": "DataCrédito TransUnion",
                "query_date": datetime.now().isoformat(),
                "report_number": f"DC-CO-{seed:08d}",
                "score_type": "Score de Crédito",
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
        - Debt to income ratio (35%)
        - Credit score (35%)
        - Defaults and negative records (30%)
        """
        score = 350  # Base score

        # Factor 1: Debt to income ratio (0-350 points)
        if monthly_income > 0 and banking_info and banking_info.monthly_obligations:
            ratio = float(
                (banking_info.monthly_obligations + amount_requested / 48)
                / monthly_income
            )
            ratio_score = min(350, int(ratio * 700))
            score += ratio_score

        if banking_info:
            # Factor 2: Credit score (0-350 points, inverted)
            if banking_info.credit_score:
                # Score 300-800 maps to 350-0 risk
                credit_factor = max(0, 350 - int((banking_info.credit_score - 300) * 0.7))
                score = score - 175 + credit_factor

            # Factor 3: Defaults (0-300 points)
            if banking_info.has_defaults:
                score += 150 + (banking_info.default_count * 75)

        return max(0, min(1000, score))
