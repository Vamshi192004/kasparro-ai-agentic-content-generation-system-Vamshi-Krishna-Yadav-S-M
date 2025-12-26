from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import FAQPageSchema, ProductPageSchema, ComparisonPageSchema
from core.logger import get_logger
from core.retry_utils import retry_with_exponential_backoff, RetryConfig

logger = get_logger(__name__)

# Retry-wrapped LLM invocation functions
@retry_with_exponential_backoff(
    max_retries=RetryConfig.PAGE_AGENT_MAX_RETRIES,
    initial_delay=1.0,
    exponential_base=2.0
)
def _invoke_faq_llm(chain, product, questions, tone) -> FAQPageSchema:
    """Invoke FAQ generation LLM with retry logic."""
    return chain.invoke({
        "name": product.name,
        "questions": str([q.dict() for q in questions]),
        "tone": tone
    })

@retry_with_exponential_backoff(
    max_retries=RetryConfig.PAGE_AGENT_MAX_RETRIES,
    initial_delay=1.0,
    exponential_base=2.0
)
def _invoke_product_page_llm(chain, product, tone) -> ProductPageSchema:
    """Invoke product page generation LLM with retry logic."""
    return chain.invoke({
        "name": product.name,
        "desc": product.description,
        "features": str(product.features),
        "specs": str(product.specs),
        "tone": tone
    })

@retry_with_exponential_backoff(
    max_retries=RetryConfig.PAGE_AGENT_MAX_RETRIES,
    initial_delay=1.0,
    exponential_base=2.0
)
def _invoke_comparison_llm(chain, product, tone) -> ComparisonPageSchema:
    """Invoke comparison page generation LLM with retry logic."""
    return chain.invoke({
        "product": product.dict(),
        "competitors": str(product.competitors),
        "tone": tone
    })

def faq_node(state: AgentState):
    logger.info("Generating FAQ page...")
    product = state['clean_data']
    questions = state['questions']
    
    if not product or not questions:
        logger.error("Missing product data or questions for FAQ generation")
        return {
            "faq_page": None,
            "error": "Cannot generate FAQ: missing product data or questions"
        }
    
    if len(questions) < 15:
        logger.warning(f"Only {len(questions)} questions available, need 15+")
        return {
            "faq_page": None,
            "error": f"Insufficient questions for FAQ page: {len(questions)}/15"
        }
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
    structured_llm = llm.with_structured_output(FAQPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Content Strategist specializing in customer-focused FAQ pages.
        
        Tone: {tone}
        
        CRITICAL Requirements:
        - Create an FAQ page with ALL provided questions (minimum 15)
        - Title must be SEO-friendly and compelling
        - Organize questions logically by category
        - Ensure answers are comprehensive (20+ characters each)
        - Maintain consistent, professional tone throughout
        - Add a standard disclaimer at the end
        - NO external search or citations - use only provided context
        
        Quality Guidelines:
        - Answers should be reassuring and helpful
        - Use clear, accessible language
        - Address customer concerns directly
        - Provide specific, actionable information
        """),
        ("user", "Product: {name}\nQuestions: {questions}")
    ])

    chain = prompt | structured_llm
    try:
        result = _invoke_faq_llm(chain, product, questions, state.get("tone", "Professional"))
        logger.info(f"✓ Generated FAQ page with {len(result.faqs)} questions")
        return {"faq_page": result}
    except Exception as e:
        logger.error(f"FAQ generation failed after retries: {e}")
        return {
            "faq_page": None,
            "error": f"FAQ generation failed: {str(e)}"
        }

def product_page_node(state: AgentState):
    logger.info("Generating product page...")
    product = state['clean_data']
    if not product:
        logger.error("Missing product data for product page generation")
        return {
            "product_page": None,
            "error": "Cannot generate product page: missing product data"
        }
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    structured_llm = llm.with_structured_output(ProductPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Copywriting Expert specializing in high-converting product landing pages.
        
        Tone: {tone}
        
        CRITICAL Requirements:
        - Hero Headline must be compelling and benefit-focused (10-100 characters)
        - Subheadline should expand on the main value proposition
        - Features list must have at least 3 items
        - Benefits list must have at least 3 items
        - Usage instructions must be clear and actionable (10+ characters)
        - CTA must be action-oriented and compelling
        - NO external search or citations - use only provided context
        
        Tasks:
        1. Write a catchy, benefit-focused Hero Headline and Subheadline
        2. Convert technical features into compelling consumer benefits
        3. Format specifications clearly and professionally
        4. Write clear, step-by-step usage instructions
        5. Create a compelling Call to Action (CTA) that drives conversions
        
        Quality Guidelines:
        - Use persuasive, customer-focused language
        - Highlight unique selling points
        - Address customer pain points
        - Create urgency without being pushy
        """),
        ("user", "Product: {name}\nDescription: {desc}\nFeatures: {features}\nSpecs: {specs}")
    ])

    chain = prompt | structured_llm
    try:
        result = _invoke_product_page_llm(chain, product, state.get("tone", "Persuasive"))
        logger.info(f"✓ Generated product page for {product.name}")
        return {"product_page": result}
    except Exception as e:
        logger.error(f"Product page generation failed after retries: {e}")
        return {
            "product_page": None,
            "error": f"Product page generation failed: {str(e)}"
        }

def comparison_node(state: AgentState):
    logger.info("Generating comparison page...")
    product = state['clean_data']
    if not product:
        logger.error("Missing product data for comparison page generation")
        return {
            "comparison_page": None,
            "error": "Cannot generate comparison page: missing product data"
        }
    
    if not product.competitors or len(product.competitors) == 0:
        logger.warning("No competitor data available")
        # Still try to generate with placeholder competitor
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
    structured_llm = llm.with_structured_output(ComparisonPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Market Analyst specializing in competitive product analysis.
        
        Tone: {tone}
        
        CRITICAL Requirements:
        - Create a comparison table with at least 2 rows
        - Each row must have feature name, product value, and competitor value
        - Summary must be at least 10 characters
        - NO external search or citations - use only provided context
        
        Compare the Main Product against its Competitors on:
        - Price (Value for money)
        - Key Features (quality, effectiveness)
        - Ingredients/Materials (composition, sourcing)
        - Primary Benefit (what makes it stand out)
        - Quality/Performance metrics
        
        Quality Guidelines:
        - Be objective but highlight product strengths
        - Use specific, measurable comparisons where possible
        - Write a compelling summary explaining why the Main Product is the superior choice
        - Maintain professional, analytical tone
        - Focus on customer value, not just features
        """),
        ("user", "Main Product: {product}\nCompetitors: {competitors}")
    ])

    chain = prompt | structured_llm
    try:
        result = _invoke_comparison_llm(chain, product, state.get("tone", "Analytical"))
        logger.info(f"✓ Generated comparison page with {len(result.comparison_table)} comparisons")
        return {"comparison_page": result}
    except Exception as e:
        logger.error(f"Comparison page generation failed after retries: {e}")
        return {
            "comparison_page": None,
            "error": f"Comparison page generation failed: {str(e)}"
        }
