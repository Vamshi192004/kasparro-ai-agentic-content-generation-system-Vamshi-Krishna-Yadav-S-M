from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.logger import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

class ReviewOutput(BaseModel):
    is_approved: bool = Field(description="Whether the content is approved")
    feedback: str = Field(description="Constructive feedback if rejected")

def reviewer_node(state: AgentState):
    logger.info("Reviewing generated content...")
    
    # Simple heuristic check first
    faq = state.get('faq_page')
    if faq and len(faq.faqs) < 3:
        logger.warning("FAQ page rejected: Too few questions.")
        return {
            "review_feedback": "FAQ Page has too few questions. Generate at least 5.",
            "revision_count": state.get("revision_count", 0) + 1
        }

    # LLM Review
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ReviewOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Quality Assurance Editor. Review the generated content.
        
        Criteria:
        1. FAQ Page must have at least 3 high-quality questions.
        2. Product Page must have a compelling Hero section.
        3. Comparison Page must compare against at least 1 competitor.
        
        If approved, set is_approved=True.
        If rejected, provide specific feedback.
        """),
        ("user", """
        FAQ Page: {faq}
        Product Page: {prod}
        Comparison Page: {comp}
        """)
    ])
    
    try:
        result = chain = prompt | structured_llm
        result = chain.invoke({
            "faq": str(state.get('faq_page')),
            "prod": str(state.get('product_page')),
            "comp": str(state.get('comparison_page'))
        })
        
        if result.is_approved:
            logger.info("Content approved by Reviewer.")
            return {"review_feedback": None}
        else:
            logger.warning(f"Content rejected: {result.feedback}")
            return {
                "review_feedback": result.feedback,
                "revision_count": state.get("revision_count", 0) + 1
            }
            
    except Exception as e:
        logger.error(f"Reviewer failed: {e}")
        # Fail open if reviewer crashes
        return {"review_feedback": None}
