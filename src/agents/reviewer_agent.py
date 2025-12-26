from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.logger import get_logger
from core.retry_utils import retry_with_exponential_backoff, RetryConfig
from pydantic import BaseModel, Field

logger = get_logger(__name__)

class ReviewOutput(BaseModel):
    is_approved: bool = Field(description="Whether the content is approved")
    feedback: str = Field(description="Constructive feedback if rejected")

@retry_with_exponential_backoff(
    max_retries=RetryConfig.REVIEWER_MAX_RETRIES,
    initial_delay=0.5,
    exponential_base=2.0
)
def _invoke_reviewer_llm(chain, state: AgentState) -> ReviewOutput:
    """Invoke reviewer LLM with retry logic."""
    return chain.invoke({
        "faq": str(state.get('faq_page')),
        "prod": str(state.get('product_page')),
        "comp": str(state.get('comparison_page'))
    })

def reviewer_node(state: AgentState):
    logger.info("Reviewing generated content...")
    
    # Enhanced heuristic checks first
    faq = state.get('faq_page')
    
    # CRITICAL: FAQ must have at least 15 questions
    if faq and len(faq.faqs) < 15:
        logger.warning(f"FAQ page rejected: Too few questions ({len(faq.faqs)}). Required: 15+")
        return {
            "review_feedback": f"FAQ Page has only {len(faq.faqs)} questions. Must generate at least 15 high-quality FAQs.",
            "revision_count": state.get("revision_count", 0) + 1
        }
    
    # Check for external search indicators (basic heuristic)
    if faq:
        for idx, faq_item in enumerate(faq.faqs):
            answer_lower = faq_item.answer.lower()
            if any(phrase in answer_lower for phrase in ["according to search", "based on results", "found on website"]):
                logger.warning(f"FAQ #{idx+1} may contain external search content")
                return {
                    "review_feedback": f"FAQ #{idx+1} appears to contain external search content. All content must be LLM-generated only.",
                    "revision_count": state.get("revision_count", 0) + 1
                }

    # LLM Review with retry mechanism
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ReviewOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Quality Assurance Editor. Review the generated content with strict criteria.
        
        CRITICAL Requirements:
        1. FAQ Page MUST have at least 15 high-quality, diverse questions covering Usage, Safety, Purchase, and Informational categories.
        2. Product Page must have a compelling Hero section with clear value proposition.
        3. Comparison Page must compare against at least 1 competitor with meaningful data.
        4. All content must be LLM-generated - NO external search results or citations.
        5. Answers must be comprehensive (minimum 20 characters each).
        6. No placeholder text, generic responses, or low-quality content.
        
        Quality Checks:
        - Are answers helpful and specific to the product?
        - Is the tone consistent and professional?
        - Are there any grammar or formatting issues?
        - Does content provide real value to customers?
        
        If approved, set is_approved=True.
        If rejected, provide specific, actionable feedback for improvement.
        """),
        ("user", """
        FAQ Page: {faq}
        Product Page: {prod}
        Comparison Page: {comp}
        """)
    ])
    
    try:
        # Fixed syntax error: separate chain creation from invocation
        chain = prompt | structured_llm
        result = _invoke_reviewer_llm(chain, state)
        
        if result.is_approved:
            logger.info("✓ Content approved by Reviewer.")
            return {"review_feedback": None}
        else:
            logger.warning(f"✗ Content rejected by Reviewer: {result.feedback}")
            return {
                "review_feedback": result.feedback,
                "revision_count": state.get("revision_count", 0) + 1
            }
            
    except Exception as e:
        logger.error(f"Reviewer failed after retries: {e}")
        # Enhanced error propagation - don't fail silently
        return {
            "review_feedback": f"Reviewer encountered an error: {str(e)}. Please retry.",
            "revision_count": state.get("revision_count", 0) + 1,
            "error": str(e)
        }
