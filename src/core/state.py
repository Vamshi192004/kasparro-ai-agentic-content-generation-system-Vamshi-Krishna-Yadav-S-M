from typing import TypedDict, Optional, List, Dict, Any
from core.schemas import ProductSchema, QuestionSchema, FAQPageSchema, ProductPageSchema, ComparisonPageSchema

class AgentState(TypedDict):
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
    tone: str # e.g. "Professional", "Witty", "Luxury"
