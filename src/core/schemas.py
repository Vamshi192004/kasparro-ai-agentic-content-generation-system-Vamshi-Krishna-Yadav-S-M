from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from core.validators import ContentQualityValidator, BusinessRequirementValidator

class ProductSchema(BaseModel):
    id: str = Field(description="Unique product identifier")
    name: str = Field(min_length=2, description="Name of the product")
    category: str = Field(min_length=2, description="Product category")
    price: float = Field(gt=0, description="Price amount")
    currency: str = Field(min_length=3, max_length=3, description="Currency code (e.g. USD)")
    features: List[str] = Field(min_length=3, description="List of at least 3 key features")
    specs: dict = Field(description="Dictionary of technical specifications")
    description: str = Field(min_length=10, description="Product description")
    competitors: List[dict] = Field(description="List of competitor data")
    
    @field_validator('description')
    @classmethod
    def validate_description_quality(cls, v: str) -> str:
        """Validate product description quality."""
        ContentQualityValidator.validate_product_description(v)
        return v
    
    @field_validator('features')
    @classmethod
    def validate_features_quality(cls, v: List[str]) -> List[str]:
        """Validate features list quality."""
        ContentQualityValidator.validate_features_list(v, min_count=3)
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate currency code."""
        BusinessRequirementValidator.validate_currency(v)
        return v
    
    @model_validator(mode='after')
    def validate_price_business_rules(self):
        """Validate price against business requirements."""
        BusinessRequirementValidator.validate_price(self.price, self.currency)
        return self

class QuestionSchema(BaseModel):
    category: str = Field(description="Category (Usage, Safety, Purchase, Informational)")
    question: str = Field(min_length=5, description="The question text")
    answer: str = Field(min_length=5, description="The answer text")
    
    @field_validator('answer')
    @classmethod
    def validate_answer_length(cls, v: str) -> str:
        """Validate answer has sufficient length for quality."""
        if len(v) < ContentQualityValidator.MIN_ANSWER_LENGTH:
            raise ValueError(
                f"Answer must be at least {ContentQualityValidator.MIN_ANSWER_LENGTH} characters, got {len(v)}"
            )
        return v

class QuestionList(BaseModel):
    questions: List[QuestionSchema] = Field(
        min_length=15, 
        description="List of at least 15 generated questions"
    )
    
    @field_validator('questions')
    @classmethod
    def validate_question_diversity(cls, v: List[QuestionSchema]) -> List[QuestionSchema]:
        """Validate questions have diverse categories."""
        if len(v) < 15:
            raise ValueError(f"Must generate at least 15 questions, got {len(v)}")
        
        categories = [q.category for q in v]
        unique_categories = set(categories)
        
        if len(unique_categories) < 3:
            raise ValueError(
                f"Questions must cover at least 3 different categories, got {len(unique_categories)}"
            )
        
        return v

class FAQPageSchema(BaseModel):
    title: str = Field(min_length=5, description="SEO Title")
    description: str = Field(min_length=10)
    faqs: List[QuestionSchema] = Field(
        min_length=15, 
        description="At least 15 FAQs required"
    )
    disclaimer: str
    
    @field_validator('faqs')
    @classmethod
    def validate_faq_quality(cls, v: List[QuestionSchema]) -> List[QuestionSchema]:
        """Validate FAQ content quality."""
        ContentQualityValidator.validate_faq_quality(v)
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title_quality(cls, v: str) -> str:
        """Validate title quality."""
        ContentQualityValidator.validate_headline(v)
        return v

class ProductPageSchema(BaseModel):
    hero_headline: str = Field(min_length=5)
    hero_subheadline: str
    price_display: str
    features_list: List[str] = Field(min_length=3)
    benefits_list: List[str] = Field(min_length=3)
    specs_display: dict
    usage_instructions: str = Field(min_length=10)
    cta_text: str
    
    @field_validator('hero_headline')
    @classmethod
    def validate_headline_quality(cls, v: str) -> str:
        """Validate headline quality."""
        ContentQualityValidator.validate_headline(v)
        return v
    
    @field_validator('features_list')
    @classmethod
    def validate_features_quality(cls, v: List[str]) -> List[str]:
        """Validate features list quality."""
        ContentQualityValidator.validate_features_list(v, min_count=3)
        return v
    
    @field_validator('benefits_list')
    @classmethod
    def validate_benefits_quality(cls, v: List[str]) -> List[str]:
        """Validate benefits list quality."""
        ContentQualityValidator.validate_features_list(v, min_count=3)
        return v

class ComparisonRow(BaseModel):
    feature: str
    product_value: str
    competitor_value: str

class ComparisonPageSchema(BaseModel):
    title: str
    comparison_table: List[ComparisonRow] = Field(min_length=2)
    summary: str = Field(min_length=10)
    
    @field_validator('comparison_table')
    @classmethod
    def validate_comparison_quality(cls, v: List[ComparisonRow]) -> List[ComparisonRow]:
        """Validate comparison table quality."""
        BusinessRequirementValidator.validate_comparison_table(v)
        return v

