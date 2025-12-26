#!/usr/bin/env python3
"""
Monolithic Agentic Content Generation System

A self-contained script that generates marketing content (FAQs, Product Pages, Comparisons)
from raw product data using Google Gemini and LangGraph.

All components (schemas, validators, retry logic, agents, graph) are included in this single file.

Usage:
    python monolithic_content_generator.py --input dataset.json --tone Professional

Requirements:
    - Python 3.9+
    - GOOGLE_API_KEY environment variable set
    - pip install langchain langgraph langchain-google-genai pydantic python-dotenv
"""

import os
import json
import argparse
import time
import functools
import re
from typing import List, Dict, Any, Optional, Tuple, Type, TypedDict, Callable
from dotenv import load_dotenv

# Pydantic imports
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# LangGraph imports
from langgraph.graph import StateGraph, END


# ============================================================================
# LOGGING
# ============================================================================

import logging

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger(__name__)


# ============================================================================
# VALIDATORS
# ============================================================================

class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ContentQualityValidator:
    """Validates content quality beyond basic schema checks."""
    
    MIN_ANSWER_LENGTH = 20
    MIN_DESCRIPTION_LENGTH = 50
    MIN_HEADLINE_LENGTH = 10
    MAX_HEADLINE_LENGTH = 100
    
    EXTERNAL_SEARCH_PATTERNS = [
        r"according to.*search",
        r"based on.*results",
        r"found on.*website",
        r"source:.*http",
        r"retrieved from",
        r"as per.*online"
    ]
    
    @classmethod
    def validate_faq_quality(cls, faqs: List[Any]) -> bool:
        """Validate FAQ content quality."""
        if len(faqs) < 15:
            raise ValidationError(
                f"FAQ list must contain at least 15 questions, got {len(faqs)}"
            )
        
        for idx, faq in enumerate(faqs):
            if len(faq.answer) < cls.MIN_ANSWER_LENGTH:
                raise ValidationError(
                    f"FAQ #{idx + 1} answer is too short ({len(faq.answer)} chars). "
                    f"Minimum: {cls.MIN_ANSWER_LENGTH} chars"
                )
            
            if len(faq.question) < 5:
                raise ValidationError(f"FAQ #{idx + 1} question is too short")
            
            cls._check_external_search(faq.answer, f"FAQ #{idx + 1} answer")
        
        categories = [faq.category for faq in faqs]
        unique_categories = set(categories)
        
        if len(unique_categories) < 3:
            raise ValidationError(
                f"FAQs should cover at least 3 different categories, got {len(unique_categories)}"
            )
        
        return True
    
    @classmethod
    def validate_product_description(cls, description: str) -> bool:
        """Validate product description quality."""
        if len(description) < cls.MIN_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Product description is too short ({len(description)} chars). "
                f"Minimum: {cls.MIN_DESCRIPTION_LENGTH} chars"
            )
        
        cls._check_external_search(description, "Product description")
        
        placeholders = ["lorem ipsum", "placeholder", "todo", "tbd", "xxx"]
        desc_lower = description.lower()
        
        for placeholder in placeholders:
            if placeholder in desc_lower:
                raise ValidationError(
                    f"Product description contains placeholder text: '{placeholder}'"
                )
        
        return True
    
    @classmethod
    def validate_headline(cls, headline: str) -> bool:
        """Validate headline quality."""
        headline_len = len(headline)
        
        if headline_len < cls.MIN_HEADLINE_LENGTH:
            raise ValidationError(
                f"Headline is too short ({headline_len} chars). "
                f"Minimum: {cls.MIN_HEADLINE_LENGTH} chars"
            )
        
        if headline_len > cls.MAX_HEADLINE_LENGTH:
            raise ValidationError(
                f"Headline is too long ({headline_len} chars). "
                f"Maximum: {cls.MAX_HEADLINE_LENGTH} chars"
            )
        
        cls._check_external_search(headline, "Headline")
        return True
    
    @classmethod
    def validate_features_list(cls, features: List[str], min_count: int = 3) -> bool:
        """Validate features list quality."""
        if len(features) < min_count:
            raise ValidationError(
                f"Features list must contain at least {min_count} items, got {len(features)}"
            )
        
        for idx, feature in enumerate(features):
            if len(feature) < 3:
                raise ValidationError(f"Feature #{idx + 1} is too short: '{feature}'")
            cls._check_external_search(feature, f"Feature #{idx + 1}")
        
        if len(features) != len(set(features)):
            raise ValidationError("Features list contains duplicates")
        
        return True
    
    @classmethod
    def _check_external_search(cls, text: str, field_name: str) -> None:
        """Check if text contains indicators of external search usage."""
        text_lower = text.lower()
        
        for pattern in cls.EXTERNAL_SEARCH_PATTERNS:
            if re.search(pattern, text_lower):
                raise ValidationError(
                    f"{field_name} contains external search indicator: '{pattern}'. "
                    f"All content must be LLM-generated only."
                )


class BusinessRequirementValidator:
    """Validates business requirements beyond schema validation."""
    
    @classmethod
    def validate_price(cls, price: float, currency: str) -> bool:
        """Validate price is reasonable."""
        if price <= 0:
            raise ValidationError(f"Price must be positive, got {price}")
        
        if price > 100000:
            logger.warning(f"Price seems unusually high: {price} {currency}")
        
        if price < 0.01:
            raise ValidationError(f"Price is too low: {price} {currency}")
        
        return True
    
    @classmethod
    def validate_currency(cls, currency: str) -> bool:
        """Validate currency code."""
        valid_currencies = {
            "USD", "EUR", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", 
            "CHF", "SEK", "NZD", "KRW", "SGD", "HKD", "NOK", "MXN"
        }
        
        if currency not in valid_currencies:
            logger.warning(f"Unusual currency code: {currency}")
        
        if len(currency) != 3:
            raise ValidationError(
                f"Currency code must be 3 characters, got '{currency}'"
            )
        
        return True
    
    @classmethod
    def validate_comparison_table(cls, comparison_rows: List[Any]) -> bool:
        """Validate comparison table has meaningful data."""
        if len(comparison_rows) < 2:
            raise ValidationError(
                f"Comparison table must have at least 2 rows, got {len(comparison_rows)}"
            )
        
        features = [row.feature for row in comparison_rows]
        if len(set(features)) != len(features):
            raise ValidationError("Comparison table contains duplicate features")
        
        for idx, row in enumerate(comparison_rows):
            if not row.product_value or not row.competitor_value:
                raise ValidationError(f"Comparison row #{idx + 1} has empty values")
        
        return True


# ============================================================================
# SCHEMAS
# ============================================================================

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
        ContentQualityValidator.validate_product_description(v)
        return v
    
    @field_validator('features')
    @classmethod
    def validate_features_quality(cls, v: List[str]) -> List[str]:
        ContentQualityValidator.validate_features_list(v, min_count=3)
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        BusinessRequirementValidator.validate_currency(v)
        return v
    
    @model_validator(mode='after')
    def validate_price_business_rules(self):
        BusinessRequirementValidator.validate_price(self.price, self.currency)
        return self


class QuestionSchema(BaseModel):
    category: str = Field(description="Category (Usage, Safety, Purchase, Informational)")
    question: str = Field(min_length=5, description="The question text")
    answer: str = Field(min_length=5, description="The answer text")
    
    @field_validator('answer')
    @classmethod
    def validate_answer_length(cls, v: str) -> str:
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
        ContentQualityValidator.validate_faq_quality(v)
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title_quality(cls, v: str) -> str:
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
        ContentQualityValidator.validate_headline(v)
        return v
    
    @field_validator('features_list')
    @classmethod
    def validate_features_quality(cls, v: List[str]) -> List[str]:
        ContentQualityValidator.validate_features_list(v, min_count=3)
        return v
    
    @field_validator('benefits_list')
    @classmethod
    def validate_benefits_quality(cls, v: List[str]) -> List[str]:
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
        BusinessRequirementValidator.validate_comparison_table(v)
        return v


class ReviewOutput(BaseModel):
    is_approved: bool = Field(description="Whether the content is approved")
    feedback: str = Field(description="Constructive feedback if rejected")


# ============================================================================
# STATE
# ============================================================================

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
    tone: str
    
    # Error Tracking
    error: Optional[str]


# ============================================================================
# RETRY UTILITIES
# ============================================================================

class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator that retries a function with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import random
            
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Function {func.__name__} failed after {max_retries} retries"
                        ) from e
                    
                    delay = initial_delay * (exponential_base ** attempt)
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


# ============================================================================
# AGENTS
# ============================================================================

# Parser Agent
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, exponential_base=2.0)
def _invoke_parser_llm(chain, raw_data: dict) -> ProductSchema:
    """Invoke parser LLM with retry logic."""
    return chain.invoke({"raw_data": json.dumps(raw_data)})


def parser_node(state: AgentState):
    logger.info("Parsing raw product data...")
    raw_data = state['raw_data']
    
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
        return {"clean_data": None, "error": f"Parsing failed: {str(e)}"}


# Question Generator Agent
@retry_with_exponential_backoff(max_retries=5, initial_delay=1.0, exponential_base=2.0)
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
        
        Remember: Quality AND quantity matter. Generate 15+ excellent questions.
        """),
        ("user", "Product Name: {name}\nDescription: {desc}")
    ])

    chain = prompt | structured_llm
    
    try:
        result = _invoke_qgen_llm(chain, product)
        logger.info(f"✓ Generated {len(result.questions)} questions")
        
        if len(result.questions) < 15:
            logger.warning(f"Generated only {len(result.questions)} questions, retrying...")
            raise ValueError(f"Insufficient questions generated: {len(result.questions)}/15")
        
        return {"questions": result.questions}
    except Exception as e:
        logger.error(f"Question Generator failed after retries: {e}")
        return {"questions": [], "error": f"Question generation failed: {str(e)}"}


# FAQ Page Agent
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, exponential_base=2.0)
def _invoke_faq_llm(chain, product, questions, tone) -> FAQPageSchema:
    """Invoke FAQ generation LLM with retry logic."""
    return chain.invoke({
        "name": product.name,
        "questions": str([q.dict() for q in questions]),
        "tone": tone
    })


def faq_node(state: AgentState):
    logger.info("Generating FAQ page...")
    product = state['clean_data']
    questions = state['questions']
    
    if not product or not questions:
        logger.error("Missing product data or questions for FAQ generation")
        return {"faq_page": None, "error": "Cannot generate FAQ: missing product data or questions"}
    
    if len(questions) < 15:
        logger.warning(f"Only {len(questions)} questions available, need 15+")
        return {"faq_page": None, "error": f"Insufficient questions for FAQ page: {len(questions)}/15"}
    
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
        return {"faq_page": None, "error": f"FAQ generation failed: {str(e)}"}


# Product Page Agent
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, exponential_base=2.0)
def _invoke_product_page_llm(chain, product, tone) -> ProductPageSchema:
    """Invoke product page generation LLM with retry logic."""
    return chain.invoke({
        "name": product.name,
        "desc": product.description,
        "features": str(product.features),
        "specs": str(product.specs),
        "tone": tone
    })


def product_page_node(state: AgentState):
    logger.info("Generating product page...")
    product = state['clean_data']
    if not product:
        logger.error("Missing product data for product page generation")
        return {"product_page": None, "error": "Cannot generate product page: missing product data"}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    structured_llm = llm.with_structured_output(ProductPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Copywriting Expert specializing in high-converting product landing pages.
        
        Tone: {tone}
        
        CRITICAL Requirements:
        - Hero Headline must be compelling and benefit-focused (10-100 characters)
        - Features list must have at least 3 items
        - Benefits list must have at least 3 items
        - Usage instructions must be clear and actionable (10+ characters)
        - CTA must be action-oriented and compelling
        - NO external search or citations - use only provided context
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
        return {"product_page": None, "error": f"Product page generation failed: {str(e)}"}


# Comparison Page Agent
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, exponential_base=2.0)
def _invoke_comparison_llm(chain, product, tone) -> ComparisonPageSchema:
    """Invoke comparison page generation LLM with retry logic."""
    return chain.invoke({
        "product": product.dict(),
        "competitors": str(product.competitors),
        "tone": tone
    })


def comparison_node(state: AgentState):
    logger.info("Generating comparison page...")
    product = state['clean_data']
    if not product:
        logger.error("Missing product data for comparison page generation")
        return {"comparison_page": None, "error": "Cannot generate comparison page: missing product data"}
    
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
        return {"comparison_page": None, "error": f"Comparison page generation failed: {str(e)}"}


# Reviewer Agent
@retry_with_exponential_backoff(max_retries=2, initial_delay=0.5, exponential_base=2.0)
def _invoke_reviewer_llm(chain, state: AgentState) -> ReviewOutput:
    """Invoke reviewer LLM with retry logic."""
    return chain.invoke({
        "faq": str(state.get('faq_page')),
        "prod": str(state.get('product_page')),
        "comp": str(state.get('comparison_page'))
    })


def reviewer_node(state: AgentState):
    logger.info("Reviewing generated content...")
    
    faq = state.get('faq_page')
    
    # CRITICAL: FAQ must have at least 15 questions
    if faq and len(faq.faqs) < 15:
        logger.warning(f"FAQ page rejected: Too few questions ({len(faq.faqs)}). Required: 15+")
        return {
            "review_feedback": f"FAQ Page has only {len(faq.faqs)} questions. Must generate at least 15 high-quality FAQs.",
            "revision_count": state.get("revision_count", 0) + 1
        }
    
    # Check for external search indicators
    if faq:
        for idx, faq_item in enumerate(faq.faqs):
            answer_lower = faq_item.answer.lower()
            if any(phrase in answer_lower for phrase in ["according to search", "based on results", "found on website"]):
                logger.warning(f"FAQ #{idx+1} may contain external search content")
                return {
                    "review_feedback": f"FAQ #{idx+1} appears to contain external search content. All content must be LLM-generated only.",
                    "revision_count": state.get("revision_count", 0) + 1
                }

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
        return {
            "review_feedback": f"Reviewer encountered an error: {str(e)}. Please retry.",
            "revision_count": state.get("revision_count", 0) + 1,
            "error": str(e)
        }


# ============================================================================
# GRAPH
# ============================================================================

def create_graph():
    """Create the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("qgen", qgen_node)
    workflow.add_node("faq_page", faq_node)
    workflow.add_node("product_page", product_page_node)
    workflow.add_node("comparison_page", comparison_node)
    workflow.add_node("reviewer", reviewer_node)

    # Define Edges
    workflow.set_entry_point("parser")
    
    def check_parser(state):
        if not state.get("clean_data"):
            logger.error("Parser failed. Stopping pipeline.")
            return END
        return "qgen"

    workflow.add_conditional_edges("parser", check_parser, {"qgen": "qgen", END: END})
    
    # Parallel execution
    workflow.add_edge("qgen", "faq_page")
    workflow.add_edge("qgen", "product_page")
    workflow.add_edge("qgen", "comparison_page")
    
    # Fan-in to Reviewer
    workflow.add_edge("faq_page", "reviewer")
    workflow.add_edge("product_page", "reviewer")
    workflow.add_edge("comparison_page", "reviewer")
    
    # Review Loop
    def check_review(state):
        feedback = state.get("review_feedback")
        count = state.get("revision_count", 0)
        
        if feedback and count < 3:
            logger.info(f"Review failed. Retrying (Attempt {count+1}). Feedback: {feedback}")
            return "qgen"
        
        if count >= 3:
            logger.warning("Max retries reached. Proceeding with current content.")
            
        return END

    workflow.add_conditional_edges(
        "reviewer",
        check_review,
        {"qgen": "qgen", END: END}
    )

    return workflow.compile()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Content Generation Pipeline")
    parser.add_argument("--input", default="dataset.json", help="Path to input JSON file")
    parser.add_argument("--tone", default="Professional", help="Tone of voice for content")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Check API key
    if "GOOGLE_API_KEY" not in os.environ:
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        logger.error("Please set it in .env file or environment.")
        return

    # Load input data
    input_path = args.input
    if not os.path.exists(input_path):
        logger.error(f"Input file '{input_path}' not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    logger.info(f"Starting LangGraph Pipeline with Tone: {args.tone}...")
    app = create_graph()
    
    # Initialize State
    initial_state = {
        "raw_data": raw_data,
        "revision_count": 0,
        "tone": args.tone
    }
    
    # Execute pipeline
    final_state = app.invoke(initial_state)
    
    # Save Outputs
    logger.info("Saving outputs...")
    
    if final_state.get('faq_page'):
        with open('faq.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['faq_page'].dict(), f, indent=2)
        logger.info("✓ Saved faq.json")
    else:
        logger.warning("✗ Skipped faq.json (Generation failed or stopped early)")
        
    if final_state.get('product_page'):
        with open('product_page.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['product_page'].dict(), f, indent=2)
        logger.info("✓ Saved product_page.json")
    else:
        logger.warning("✗ Skipped product_page.json")
        
    if final_state.get('comparison_page'):
        with open('comparison_page.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['comparison_page'].dict(), f, indent=2)
        logger.info("✓ Saved comparison_page.json")
    else:
        logger.warning("✗ Skipped comparison_page.json")
        
    logger.info("Pipeline execution finished.")
    logger.info(f"Revision count: {final_state.get('revision_count', 0)}")


if __name__ == "__main__":
    main()
