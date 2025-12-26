from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import ProductSchema
from core.logger import get_logger
from core.retry_utils import retry_with_exponential_backoff, RetryConfig
import json
import os

logger = get_logger(__name__)

@retry_with_exponential_backoff(
    max_retries=RetryConfig.PARSER_MAX_RETRIES,
    initial_delay=1.0,
    exponential_base=2.0
)
def _invoke_parser_llm(chain, raw_data: dict) -> ProductSchema:
    """Invoke parser LLM with retry logic."""
    return chain.invoke({"raw_data": json.dumps(raw_data)})

def parser_node(state: AgentState):
    logger.info("Parsing raw product data...")
    raw_data = state['raw_data']
    
    # Initialize Gemini
    # Ensure GOOGLE_API_KEY is set in environment
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ProductSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Data Engineer specializing in E-commerce product data normalization.
        
        Your task is to:
        1. Analyze the raw input JSON carefully
        2. Extract key product details (Name, Price, Category, Features, Specs)
        3. Identify any competitor data if present
        4. Normalize the data into a strict, validated schema
        
        CRITICAL Requirements:
        - The 'features' list MUST contain at least 3 distinct selling points
        - Description must be at least 50 characters and provide real value
        - Price must be a positive number
        - Currency must be a valid 3-letter code (e.g., USD, EUR, GBP)
        - NO external search or web lookups - use only the provided data
        
        If fields are missing:
        - Infer reasonable defaults based on product context
        - For critical fields, use "N/A" or appropriate placeholder
        - Ensure all required fields are populated
        
        Quality over speed - ensure the normalized data is accurate and complete.
        """),
        ("user", "Raw Data: {raw_data}")
    ])

    chain = prompt | structured_llm
    
    try:
        clean_data = _invoke_parser_llm(chain, raw_data)
        logger.info(f"✓ Successfully parsed product: {clean_data.name}")
        return {"clean_data": clean_data}
        
    except Exception as e:
        logger.error(f"Parser failed after retries: {e}")
        # Return None and let graph handle the error
        return {
            "clean_data": None,
            "error": f"Parsing failed: {str(e)}"
        }

