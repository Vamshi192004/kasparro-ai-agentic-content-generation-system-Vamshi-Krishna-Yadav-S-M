from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import FAQPageSchema, ProductPageSchema, ComparisonPageSchema

def faq_node(state: AgentState):
    product = state['clean_data']
    questions = state['questions']
    
    if not product or not questions:
        return {"faq_page": None}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
    structured_llm = llm.with_structured_output(FAQPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Content Strategist. Create a structured FAQ page.
        
        Tone: {tone}
        
        Guidelines:
        - Title should be SEO-friendly.
        - Organize questions logically.
        - Ensure answers are concise and reassuring.
        - Add a standard disclaimer at the end.
        """),
        ("user", "Product: {name}\nQuestions: {questions}")
    ])

    chain = prompt | structured_llm
    try:
        result = chain.invoke({
            "name": product.name,
            "questions": str([q.dict() for q in questions]),
            "tone": state.get("tone", "Professional")
        })
        return {"faq_page": result}
    except Exception as e:
        print(f"Error in FAQ Node: {e}")
        return {"faq_page": None}

def product_page_node(state: AgentState):
    product = state['clean_data']
    if not product:
        return {"product_page": None}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    structured_llm = llm.with_structured_output(ProductPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Copywriting Expert. Create a high-converting Product Landing Page.
        
        Tone: {tone}
        
        Tasks:
        1. Write a catchy Hero Headline and Subheadline.
        2. Convert technical features into consumer benefits.
        3. Format specifications clearly.
        4. Write clear usage instructions.
        5. Create a compelling Call to Action (CTA).
        """),
        ("user", "Product: {name}\nDescription: {desc}\nFeatures: {features}\nSpecs: {specs}")
    ])

    chain = prompt | structured_llm
    try:
        result = chain.invoke({
            "name": product.name,
            "desc": product.description,
            "features": str(product.features),
            "specs": str(product.specs),
            "tone": state.get("tone", "Persuasive")
        })
        return {"product_page": result}
    except Exception as e:
        print(f"Error in Product Page Node: {e}")
        return {"product_page": None}

def comparison_node(state: AgentState):
    product = state['clean_data']
    if not product:
        return {"comparison_page": None}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
    structured_llm = llm.with_structured_output(ComparisonPageSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Market Analyst. Create a Comparison Page.
        
        Tone: {tone}
        
        Compare the Main Product against its Competitors on:
        - Price (Value for money)
        - Key Features
        - Ingredients/Materials
        - Primary Benefit
        
        Write a summary explaining why the Main Product is the superior choice.
        """),
        ("user", "Main Product: {product}\nCompetitors: {competitors}")
    ])

    chain = prompt | structured_llm
    try:
        result = chain.invoke({
            "product": product.dict(),
            "competitors": str(product.competitors),
            "tone": state.get("tone", "Analytical")
        })
        return {"comparison_page": result}
    except Exception as e:
        print(f"Error in Comparison Node: {e}")
        return {"comparison_page": None}
