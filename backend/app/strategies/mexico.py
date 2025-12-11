"""Mexico (MX) country strategy implementation."""
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.strategies.base import (
    BankingInfo,
    CountryStrategy,
    DocumentType,
    ValidationResult,
)


class MexicoStrategy(CountryStrategy):
    """
    Strategy for processing loan applications in Mexico.

    Document: CURP (Clave Única de Registro de Población)
    Currency: MXN
    Provider: Simulated Buró de Crédito
    """

    # Business rule thresholds
    REVIEW_THRESHOLD_MXN = Decimal("300000")  # Amounts above this require review
    MAX_AMOUNT_TO_INCOME_RATIO = Decimal("6")  # Max 6x monthly income
    MIN_CREDIT_SCORE = 550  # Buró de Crédito minimum

    # Valid Mexican states for CURP
    VALID_STATES = {
        "AS", "BC", "BS", "CC", "CL", "CM", "CS", "CH", "DF", "DG",
        "GT", "GR", "HG", "JC", "MC", "MN", "MS", "NT", "NL", "OC",
        "PL", "QT", "QR", "SP", "SL", "SR", "TC", "TS", "TL", "VZ",
        "YN", "ZS", "NE",  # NE = Nacido en el extranjero
    }

    @property
    def country_code(self) -> str:
        return "MX"

    @property
    def country_name(self) -> str:
        return "México"

    @property
    def currency(self) -> str:
        return "MXN"

    @property
    def supported_document_types(self) -> list[DocumentType]:
        return [DocumentType.CURP]

    def validate_document(
        self,
        document_type: str,
        document_number: str,
    ) -> ValidationResult:
        """
        Validate Mexican CURP.

        CURP format (18 characters):
        - 4 letters: First surname initial, first vowel of surname,
                     second surname initial, first name initial
        - 6 digits: Birth date (YYMMDD)
        - 1 letter: Gender (H=Male, M=Female)
        - 2 letters: State of birth code
        - 3 letters: First consonants of surnames and name
        - 2 characters: Homoclave (digit + check digit)
        """
        result = ValidationResult(is_valid=True)

        if document_type.upper() != "CURP":
            result.add_error(
                f"Unsupported document type '{document_type}' for Mexico. "
                f"Expected CURP."
            )
            return result

        # Normalize input
        curp = document_number.upper().replace(" ", "").replace("-", "")

        # Check length
        if len(curp) != 18:
            result.add_error(
                f"CURP must be 18 characters. Got {len(curp)}."
            )
            return result

        # Validate format with regex
        curp_pattern = r"^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]\d$"
        if not re.match(curp_pattern, curp):
            result.add_error(
                "CURP format is invalid. Expected: 4 letters + 6 digits + "
                "gender (H/M) + 2 letters state + 3 letters + 2 chars homoclave."
            )
            return result

        # Validate birth date
        date_str = curp[4:10]
        try:
            year = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])

            # Determine century (people born 2000+ have different marker)
            # For simplicity, assume 00-30 is 2000s, 31-99 is 1900s
            full_year = 2000 + year if year <= 30 else 1900 + year

            birth_date = datetime(full_year, month, day)

            # Check if date is in the past
            if birth_date > datetime.now():
                result.add_error("Birth date in CURP cannot be in the future.")

            # Check minimum age (18 years)
            age = (datetime.now() - birth_date).days / 365.25
            if age < 18:
                result.add_error(
                    f"Applicant must be at least 18 years old. "
                    f"CURP indicates age of {int(age)} years."
                )

        except ValueError:
            result.add_error(
                f"Invalid birth date in CURP: {date_str}. "
                f"Expected valid YYMMDD format."
            )

        # Validate state code
        state_code = curp[11:13]
        if state_code not in self.VALID_STATES:
            result.add_error(
                f"Invalid state code '{state_code}' in CURP. "
                f"Must be a valid Mexican state."
            )

        return result

    def validate_business_rules(
        self,
        amount_requested: Decimal,
        monthly_income: Decimal,
        banking_info: Optional[BankingInfo] = None,
    ) -> ValidationResult:
        """
        Apply Mexican business rules.

        Rules:
        1. Amounts > MXN 300,000 require manual review
        2. Amount cannot exceed 6x monthly income
        3. Buró de Crédito score must be >= 550
        """
        result = ValidationResult(is_valid=True)

        # Rule 1: High amount review
        if amount_requested > self.REVIEW_THRESHOLD_MXN:
            result.requires_review = True
            result.add_warning(
                f"Amount MXN ${amount_requested:,.2f} exceeds review threshold "
                f"of MXN ${self.REVIEW_THRESHOLD_MXN:,.2f}. Manual review required."
            )
            result.risk_factors["high_amount"] = True

        # Rule 2: Amount to income ratio
        if monthly_income > 0:
            ratio = amount_requested / monthly_income
            result.risk_factors["amount_to_income_ratio"] = float(ratio)

            if ratio > self.MAX_AMOUNT_TO_INCOME_RATIO:
                result.add_error(
                    f"Requested amount is {ratio:.1f}x monthly income. "
                    f"Maximum allowed is {self.MAX_AMOUNT_TO_INCOME_RATIO}x."
                )
        else:
            result.add_error("Monthly income must be greater than zero.")

        # Rule 3: Credit score (requires banking info)
        if banking_info and banking_info.credit_score is not None:
            result.risk_factors["credit_score"] = banking_info.credit_score

            if banking_info.credit_score < self.MIN_CREDIT_SCORE:
                result.add_error(
                    f"Buró de Crédito score {banking_info.credit_score} "
                    f"is below minimum required {self.MIN_CREDIT_SCORE}."
                )

            # Additional checks
            if banking_info.has_defaults:
                result.requires_review = True
                result.add_warning(
                    f"Applicant has {banking_info.default_count} defaults "
                    "in Buró de Crédito. Manual review required."
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
        Fetch banking info from Buró de Crédito (simulated).

        In production, this would call the actual Buró de Crédito API.
        """
        # Generate simulated data based on document
        seed = hash(document_number) % 1000

        # Mexican credit scores typically range 400-850
        credit_score = 450 + (seed % 400)  # 450-849

        return BankingInfo(
            provider_name="BURO_CREDITO_MX",
            credit_score=credit_score,
            total_debt=Decimal(str(seed * 500)),  # 0-499,500 MXN
            payment_history_score=50 + (seed % 50),  # 50-99
            account_age_months=6 + (seed % 180),  # 6-185 months
            has_defaults=seed < 150,  # 15% chance
            default_count=1 if seed < 100 else (2 if seed < 150 else 0),
            monthly_obligations=Decimal(str(1000 + (seed % 15000))),  # 1k-16k MXN
            available_credit=Decimal(str(10000 + (seed % 100000))),  # 10k-110k MXN
            employment_verified=seed % 10 > 3,  # 60% verified
            income_verified=seed % 10 > 4,  # 50% verified
            raw_data={
                "provider": "Buró de Crédito",
                "query_date": datetime.now().isoformat(),
                "folio": f"BC-MX-{seed:08d}",
                "score_type": "BC Score",
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
        - Amount to income ratio (40%)
        - Buró de Crédito score (40%)
        - Defaults (20%)
        """
        score = 400  # Base score

        # Factor 1: Amount to income ratio (0-400 points)
        if monthly_income > 0:
            ratio = float(amount_requested / monthly_income)
            # Ratio of 6+ gets max points
            ratio_score = min(400, int(ratio * 67))
            score += ratio_score

        if banking_info:
            # Factor 2: Credit score (0-400 points, inverted)
            if banking_info.credit_score:
                # BC score 450-850 maps to 400-0 risk
                bc_score = banking_info.credit_score
                credit_factor = max(0, 400 - int((bc_score - 450) * 1.0))
                score = score - 200 + credit_factor

            # Factor 3: Defaults (0-200 points)
            if banking_info.has_defaults:
                score += 100 + (banking_info.default_count * 50)

        # Clamp to 0-1000
        return max(0, min(1000, score))
