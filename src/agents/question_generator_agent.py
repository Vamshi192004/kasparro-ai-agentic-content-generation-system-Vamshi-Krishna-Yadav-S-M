from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import QuestionSchema, QuestionList
from core.logger import get_logger
from core.retry_utils import retry_with_exponential_backoff, RetryConfig
from typing import List

logger = get_logger(__name__)

@retry_with_exponential_backoff(
    max_retries=RetryConfig.QGEN_MAX_RETRIES,
    initial_delay=1.0,
    exponential_base=2.0
)
def _invoke_qgen_llm(chain, product) -> QuestionList:
    """Invoke question generation LLM with retry logic."""
    return chain.invoke({
        "name": product.name,
        "desc": product.description,
        "features": ", ".join(product.features),
        "specs": str(product.specs)
    })

def qgen_node(state: AgentState):
    logger.info("Generating questions...")
    product = state['clean_data']
    if not product:
        logger.error("No clean_data available for question generation")
        return {"questions": []}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    structured_llm = llm.with_structured_output(QuestionList)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Customer Success AI Agent with deep expertise in e-commerce and customer psychology.
        
        CRITICAL REQUIREMENT: Generate at least 15 comprehensive, high-quality Frequently Asked Questions (FAQs).
        
        Categories to cover (distribute questions across all):
        - **Usage** (3-5 questions): Practical instructions, application tips, best practices, how-to guides
        - **Safety** (3-5 questions): Allergens, skin types, age restrictions, pregnancy safety, side effects, contraindications
        - **Purchase** (3-5 questions): Shipping, returns, refund policy, availability, bulk orders, pricing
        - **Informational** (4-6 questions): Ingredients, science behind the product, sustainability, certifications, manufacturing
        
        Quality Requirements:
        1. Each answer must be at least 20 characters and provide real value
        2. Questions should anticipate what skeptical or confused customers would ask
        3. Answers must be specific to THIS product - no generic responses
        4. Use professional, helpful tone
        5. NO external search results or citations - generate from product context only
        6. Avoid placeholder text or vague answers
        
        Reasoning Process:
        1. Analyze product features: {features}
        2. Analyze specifications: {specs}
        3. Consider what makes this product unique
        4. Think about common customer objections and concerns
        5. Anticipate questions from different customer segments (new users, experienced users, gift buyers)
        6. Generate comprehensive, helpful answers for each question
        
        Remember: Quality AND quantity matter. Generate 15+ excellent questions.
        """),
        ("user", "Product Name: {name}\nDescription: {desc}")
    ])

    chain = prompt | structured_llm
    
    try:
        result = _invoke_qgen_llm(chain, product)
        logger.info(f"✓ Generated {len(result.questions)} questions")
        
        # Validate minimum count
        if len(result.questions) < 15:
            logger.warning(f"Generated only {len(result.questions)} questions, retrying...")
            raise ValueError(f"Insufficient questions generated: {len(result.questions)}/15")
        
        return {"questions": result.questions}
        
    except Exception as e:
        logger.error(f"Question Generator failed after retries: {e}")
        # Return empty list to trigger error handling in graph
        return {
            "questions": [],
            "error": f"Question generation failed: {str(e)}"
        }

