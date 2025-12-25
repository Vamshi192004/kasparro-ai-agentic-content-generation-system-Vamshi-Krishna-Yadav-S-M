from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

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

class QuestionSchema(BaseModel):
    category: str = Field(description="Category (Usage, Safety, Purchase, Informational)")
    question: str = Field(min_length=5, description="The question text")
    answer: str = Field(min_length=5, description="The answer text")

class QuestionList(BaseModel):
    questions: List[QuestionSchema] = Field(min_length=5, description="List of at least 5 generated questions")

class FAQPageSchema(BaseModel):
    title: str = Field(min_length=5, description="SEO Title")
    description: str = Field(min_length=10)
    faqs: List[QuestionSchema] = Field(min_length=3, description="At least 3 FAQs")
    disclaimer: str

class ProductPageSchema(BaseModel):
    hero_headline: str = Field(min_length=5)
    hero_subheadline: str
    price_display: str
    features_list: List[str] = Field(min_length=3)
    benefits_list: List[str] = Field(min_length=3)
    specs_display: dict
    usage_instructions: str = Field(min_length=10)
    cta_text: str

class ComparisonRow(BaseModel):
    feature: str
    product_value: str
    competitor_value: str

class ComparisonPageSchema(BaseModel):
    title: str
    comparison_table: List[ComparisonRow] = Field(min_length=2)
    summary: str = Field(min_length=10)
