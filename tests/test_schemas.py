"""
Unit tests for Pydantic schemas and validators.
"""
import pytest
from pydantic import ValidationError
from core.schemas import (
    ProductSchema, QuestionSchema, QuestionList,
    FAQPageSchema, ProductPageSchema, ComparisonPageSchema, ComparisonRow
)
from core.validators import ContentQualityValidator, BusinessRequirementValidator


class TestProductSchema:
    """Test ProductSchema validation."""
    
    def test_valid_product(self):
        """Test that valid product data passes validation."""
        product = ProductSchema(
            id="test-123",
            name="Test Product",
            category="Skincare",
            price=49.99,
            currency="USD",
            features=["Feature 1", "Feature 2", "Feature 3"],
            specs={"volume": "50ml"},
            description="This is a comprehensive product description that meets the minimum length requirement.",
            competitors=[{"name": "Competitor A", "price": 39.99}]
        )
        
        assert product.name == "Test Product"
        assert product.price == 49.99
        assert len(product.features) == 3
    
    def test_invalid_price(self):
        """Test that negative price fails validation."""
        with pytest.raises(ValidationError):
            ProductSchema(
                id="test-123",
                name="Test Product",
                category="Skincare",
                price=-10.0,  # Invalid
                currency="USD",
                features=["Feature 1", "Feature 2", "Feature 3"],
                specs={"volume": "50ml"},
                description="This is a comprehensive product description that meets the minimum length requirement.",
                competitors=[]
            )
    
    def test_invalid_currency(self):
        """Test that invalid currency code fails validation."""
        with pytest.raises(ValidationError):
            ProductSchema(
                id="test-123",
                name="Test Product",
                category="Skincare",
                price=49.99,
                currency="US",  # Invalid - must be 3 characters
                features=["Feature 1", "Feature 2", "Feature 3"],
                specs={"volume": "50ml"},
                description="This is a comprehensive product description that meets the minimum length requirement.",
                competitors=[]
            )
    
    def test_insufficient_features(self):
        """Test that less than 3 features fails validation."""
        with pytest.raises(ValidationError):
            ProductSchema(
                id="test-123",
                name="Test Product",
                category="Skincare",
                price=49.99,
                currency="USD",
                features=["Feature 1", "Feature 2"],  # Only 2 features
                specs={"volume": "50ml"},
                description="This is a comprehensive product description that meets the minimum length requirement.",
                competitors=[]
            )
    
    def test_short_description(self):
        """Test that short description fails validation."""
        with pytest.raises(ValidationError):
            ProductSchema(
                id="test-123",
                name="Test Product",
                category="Skincare",
                price=49.99,
                currency="USD",
                features=["Feature 1", "Feature 2", "Feature 3"],
                specs={"volume": "50ml"},
                description="Too short",  # Less than 50 characters
                competitors=[]
            )


class TestQuestionSchema:
    """Test QuestionSchema validation."""
    
    def test_valid_question(self):
        """Test that valid question passes validation."""
        question = QuestionSchema(
            category="Usage",
            question="How do I use this product?",
            answer="Apply a small amount to clean skin twice daily for best results."
        )
        
        assert question.category == "Usage"
        assert len(question.answer) >= 20
    
    def test_short_answer(self):
        """Test that short answer fails validation."""
        with pytest.raises(ValidationError):
            QuestionSchema(
                category="Usage",
                question="How do I use this?",
                answer="Apply daily"  # Less than 20 characters
            )


class TestQuestionList:
    """Test QuestionList validation."""
    
    def test_valid_question_list(self):
        """Test that list with 15+ questions passes validation."""
        questions = [
            QuestionSchema(
                category="Usage",
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length."
            )
            for i in range(15)
        ]
        
        question_list = QuestionList(questions=questions)
        assert len(question_list.questions) == 15
    
    def test_insufficient_questions(self):
        """Test that less than 15 questions fails validation."""
        questions = [
            QuestionSchema(
                category="Usage",
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length."
            )
            for i in range(10)  # Only 10 questions
        ]
        
        with pytest.raises(ValidationError):
            QuestionList(questions=questions)
    
    def test_insufficient_category_diversity(self):
        """Test that questions must cover at least 3 categories."""
        # All questions in same category
        questions = [
            QuestionSchema(
                category="Usage",  # All same category
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length."
            )
            for i in range(15)
        ]
        
        with pytest.raises(ValidationError):
            QuestionList(questions=questions)


class TestFAQPageSchema:
    """Test FAQPageSchema validation."""
    
    def test_valid_faq_page(self):
        """Test that valid FAQ page passes validation."""
        faqs = [
            QuestionSchema(
                category=["Usage", "Safety", "Purchase", "Informational"][i % 4],
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length and detail."
            )
            for i in range(15)
        ]
        
        faq_page = FAQPageSchema(
            title="Frequently Asked Questions",
            description="Find answers to common questions about our product.",
            faqs=faqs,
            disclaimer="This information is for educational purposes only."
        )
        
        assert len(faq_page.faqs) == 15
        assert len(faq_page.title) >= 5
    
    def test_insufficient_faqs(self):
        """Test that less than 15 FAQs fails validation."""
        faqs = [
            QuestionSchema(
                category="Usage",
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length."
            )
            for i in range(10)  # Only 10 FAQs
        ]
        
        with pytest.raises(ValidationError):
            FAQPageSchema(
                title="FAQ",
                description="Questions",
                faqs=faqs,
                disclaimer="Disclaimer"
            )


class TestContentQualityValidator:
    """Test ContentQualityValidator."""
    
    def test_validate_faq_quality_pass(self):
        """Test that high-quality FAQs pass validation."""
        faqs = [
            QuestionSchema(
                category=["Usage", "Safety", "Purchase", "Informational"][i % 4],
                question=f"How do I use feature {i}?",
                answer=f"To use feature {i}, follow these detailed steps for optimal results and safety."
            )
            for i in range(15)
        ]
        
        assert ContentQualityValidator.validate_faq_quality(faqs) is True
    
    def test_validate_faq_quality_fail_count(self):
        """Test that insufficient FAQ count fails validation."""
        faqs = [
            QuestionSchema(
                category="Usage",
                question="Question?",
                answer="This is a sufficient answer with enough length."
            )
            for _ in range(10)  # Only 10 FAQs
        ]
        
        with pytest.raises(Exception):
            ContentQualityValidator.validate_faq_quality(faqs)
    
    def test_validate_external_search_detection(self):
        """Test that external search indicators are detected."""
        faqs = [
            QuestionSchema(
                category="Usage",
                question="Question?",
                answer="According to search results, this product is great."  # Contains indicator
            )
        ] + [
            QuestionSchema(
                category=["Safety", "Purchase", "Informational"][i % 3],
                question=f"Question {i}?",
                answer=f"This is a comprehensive answer to question {i} with sufficient length."
            )
            for i in range(14)
        ]
        
        with pytest.raises(Exception):
            ContentQualityValidator.validate_faq_quality(faqs)


class TestBusinessRequirementValidator:
    """Test BusinessRequirementValidator."""
    
    def test_validate_price_pass(self):
        """Test that valid price passes validation."""
        assert BusinessRequirementValidator.validate_price(49.99, "USD") is True
    
    def test_validate_price_fail_negative(self):
        """Test that negative price fails validation."""
        with pytest.raises(Exception):
            BusinessRequirementValidator.validate_price(-10.0, "USD")
    
    def test_validate_price_fail_zero(self):
        """Test that zero price fails validation."""
        with pytest.raises(Exception):
            BusinessRequirementValidator.validate_price(0.0, "USD")
    
    def test_validate_currency_pass(self):
        """Test that valid currency codes pass validation."""
        assert BusinessRequirementValidator.validate_currency("USD") is True
        assert BusinessRequirementValidator.validate_currency("EUR") is True
        assert BusinessRequirementValidator.validate_currency("GBP") is True
    
    def test_validate_currency_fail_length(self):
        """Test that invalid length currency code fails validation."""
        with pytest.raises(Exception):
            BusinessRequirementValidator.validate_currency("US")
    
    def test_validate_comparison_table_pass(self):
        """Test that valid comparison table passes validation."""
        rows = [
            ComparisonRow(feature="Price", product_value="$49.99", competitor_value="$59.99"),
            ComparisonRow(feature="Quality", product_value="Premium", competitor_value="Standard")
        ]
        
        assert BusinessRequirementValidator.validate_comparison_table(rows) is True
    
    def test_validate_comparison_table_fail_count(self):
        """Test that insufficient rows fail validation."""
        rows = [
            ComparisonRow(feature="Price", product_value="$49.99", competitor_value="$59.99")
        ]
        
        with pytest.raises(Exception):
            BusinessRequirementValidator.validate_comparison_table(rows)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
