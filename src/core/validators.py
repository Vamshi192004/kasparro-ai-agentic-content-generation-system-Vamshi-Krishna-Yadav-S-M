"""
Content quality validators and business requirement validators.
"""
from typing import List, Dict, Any, Optional
from core.logger import get_logger
import re

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ContentQualityValidator:
    """Validates content quality beyond basic schema checks."""
    
    # Minimum quality thresholds
    MIN_ANSWER_LENGTH = 20
    MIN_DESCRIPTION_LENGTH = 50
    MIN_HEADLINE_LENGTH = 10
    MAX_HEADLINE_LENGTH = 100
    
    # Suspicious patterns that might indicate external search usage
    EXTERNAL_SEARCH_PATTERNS = [
        r"according to.*search",
        r"based on.*results",
        r"found on.*website",
        r"source:.*http",
        r"retrieved from",
        r"as per.*online"
    ]
    
    @classmethod
    def validate_faq_quality(cls, faqs: List[Any]) -> bool:
        """
        Validate FAQ content quality.
        
        Args:
            faqs: List of FAQ objects
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if len(faqs) < 15:
            raise ValidationError(
                f"FAQ list must contain at least 15 questions, got {len(faqs)}"
            )
        
        for idx, faq in enumerate(faqs):
            # Check answer length
            if len(faq.answer) < cls.MIN_ANSWER_LENGTH:
                raise ValidationError(
                    f"FAQ #{idx + 1} answer is too short ({len(faq.answer)} chars). "
                    f"Minimum: {cls.MIN_ANSWER_LENGTH} chars"
                )
            
            # Check question length
            if len(faq.question) < 5:
                raise ValidationError(
                    f"FAQ #{idx + 1} question is too short"
                )
            
            # Check for external search indicators
            cls._check_external_search(faq.answer, f"FAQ #{idx + 1} answer")
        
        # Check for category diversity
        categories = [faq.category for faq in faqs]
        unique_categories = set(categories)
        
        if len(unique_categories) < 3:
            raise ValidationError(
                f"FAQs should cover at least 3 different categories, got {len(unique_categories)}"
            )
        
        logger.info(f"FAQ quality validation passed: {len(faqs)} questions across {len(unique_categories)} categories")
        return True
    
    @classmethod
    def validate_product_description(cls, description: str) -> bool:
        """
        Validate product description quality.
        
        Args:
            description: Product description text
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if len(description) < cls.MIN_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Product description is too short ({len(description)} chars). "
                f"Minimum: {cls.MIN_DESCRIPTION_LENGTH} chars"
            )
        
        cls._check_external_search(description, "Product description")
        
        # Check for placeholder text
        placeholders = ["lorem ipsum", "placeholder", "todo", "tbd", "xxx"]
        desc_lower = description.lower()
        
        for placeholder in placeholders:
            if placeholder in desc_lower:
                raise ValidationError(
                    f"Product description contains placeholder text: '{placeholder}'"
                )
        
        logger.info("Product description quality validation passed")
        return True
    
    @classmethod
    def validate_headline(cls, headline: str) -> bool:
        """
        Validate headline quality.
        
        Args:
            headline: Headline text
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        headline_len = len(headline)
        
        if headline_len < cls.MIN_HEADLINE_LENGTH:
            raise ValidationError(
                f"Headline is too short ({headline_len} chars). "
                f"Minimum: {cls.MIN_HEADLINE_LENGTH} chars"
            )
        
        if headline_len > cls.MAX_HEADLINE_LENGTH:
            raise ValidationError(
                f"Headline is too long ({headline_len} chars). "
                f"Maximum: {cls.MAX_HEADLINE_LENGTH} chars"
            )
        
        cls._check_external_search(headline, "Headline")
        
        logger.info("Headline quality validation passed")
        return True
    
    @classmethod
    def validate_features_list(cls, features: List[str], min_count: int = 3) -> bool:
        """
        Validate features list quality.
        
        Args:
            features: List of feature strings
            min_count: Minimum number of features required
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if len(features) < min_count:
            raise ValidationError(
                f"Features list must contain at least {min_count} items, got {len(features)}"
            )
        
        for idx, feature in enumerate(features):
            if len(feature) < 3:
                raise ValidationError(
                    f"Feature #{idx + 1} is too short: '{feature}'"
                )
            
            cls._check_external_search(feature, f"Feature #{idx + 1}")
        
        # Check for duplicates
        if len(features) != len(set(features)):
            raise ValidationError("Features list contains duplicates")
        
        logger.info(f"Features list quality validation passed: {len(features)} features")
        return True
    
    @classmethod
    def _check_external_search(cls, text: str, field_name: str) -> None:
        """
        Check if text contains indicators of external search usage.
        
        Args:
            text: Text to check
            field_name: Name of the field being checked (for error messages)
            
        Raises:
            ValidationError: If external search indicators are found
        """
        text_lower = text.lower()
        
        for pattern in cls.EXTERNAL_SEARCH_PATTERNS:
            if re.search(pattern, text_lower):
                raise ValidationError(
                    f"{field_name} contains external search indicator: '{pattern}'. "
                    f"All content must be LLM-generated only."
                )


class BusinessRequirementValidator:
    """Validates business requirements beyond schema validation."""
    
    @classmethod
    def validate_price(cls, price: float, currency: str) -> bool:
        """
        Validate price is reasonable.
        
        Args:
            price: Price value
            currency: Currency code
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if price <= 0:
            raise ValidationError(f"Price must be positive, got {price}")
        
        # Reasonable price ranges (can be adjusted based on business needs)
        if price > 100000:
            logger.warning(f"Price seems unusually high: {price} {currency}")
        
        if price < 0.01:
            raise ValidationError(f"Price is too low: {price} {currency}")
        
        return True
    
    @classmethod
    def validate_currency(cls, currency: str) -> bool:
        """
        Validate currency code.
        
        Args:
            currency: Currency code
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        # Common currency codes
        valid_currencies = {
            "USD", "EUR", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", 
            "CHF", "SEK", "NZD", "KRW", "SGD", "HKD", "NOK", "MXN"
        }
        
        if currency not in valid_currencies:
            logger.warning(f"Unusual currency code: {currency}")
        
        if len(currency) != 3:
            raise ValidationError(
                f"Currency code must be 3 characters, got '{currency}'"
            )
        
        return True
    
    @classmethod
    def validate_comparison_table(cls, comparison_rows: List[Any]) -> bool:
        """
        Validate comparison table has meaningful data.
        
        Args:
            comparison_rows: List of comparison row objects
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if len(comparison_rows) < 2:
            raise ValidationError(
                f"Comparison table must have at least 2 rows, got {len(comparison_rows)}"
            )
        
        # Check for meaningful comparisons
        features = [row.feature for row in comparison_rows]
        if len(set(features)) != len(features):
            raise ValidationError("Comparison table contains duplicate features")
        
        # Ensure values are not empty
        for idx, row in enumerate(comparison_rows):
            if not row.product_value or not row.competitor_value:
                raise ValidationError(
                    f"Comparison row #{idx + 1} has empty values"
                )
        
        logger.info(f"Comparison table validation passed: {len(comparison_rows)} rows")
        return True
