from typing import TypedDict, Optional, List, Dict, Any
from core.schemas import ProductSchema, QuestionSchema, FAQPageSchema, ProductPageSchema, ComparisonPageSchema

class AgentState(TypedDict, total=False):
    # Input/Output Data
    raw_data: Dict[str, Any]
    clean_data: Optional[ProductSchema]
    questions: Optional[List[QuestionSchema]]
    faq_page: Optional[FAQPageSchema]
    product_page: Optional[ProductPageSchema]
    comparison_page: Optional[ComparisonPageSchema]
    
    # Feedback Loop State
    review_feedback: Optional[str]
    revision_count: int
    
    # Customization
    tone: str  # e.g. "Professional", "Witty", "Luxury"
    
    # Enhanced Error Tracking
    error: Optional[str]  # Latest error message
    errors: Optional[Dict[str, str]]  # Error messages per agent
    
    # Retry Tracking per Agent
    parser_retries: Optional[int]
    qgen_retries: Optional[int]
    faq_retries: Optional[int]
    product_page_retries: Optional[int]
    comparison_retries: Optional[int]
    reviewer_retries: Optional[int]
    
    # Quality Metrics
    quality_score: Optional[float]  # Overall quality score (0-1)
    faq_count: Optional[int]  # Number of FAQs generated
    validation_passed: Optional[bool]  # Whether all validations passed

