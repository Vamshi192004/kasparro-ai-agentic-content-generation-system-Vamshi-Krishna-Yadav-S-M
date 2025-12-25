from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import QuestionSchema, QuestionList
from typing import List

def qgen_node(state: AgentState):
    product = state['clean_data']
    if not product:
        return {"questions": []}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    structured_llm = llm.with_structured_output(QuestionList)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Customer Success AI Agent.
        
        Your goal is to anticipate customer needs and generate a comprehensive list of at least 15 Frequently Asked Questions (FAQs).
        
        Categories to cover:
        - **Usage**: Practical instructions, tips, and best practices.
        - **Safety**: Allergens, skin types, pregnancy safety, side effects.
        - **Purchase**: Shipping, returns, availability, bulk orders.
        - **Informational**: Ingredients, science behind the product, sustainability.
        
        Reasoning Steps:
        1. Analyze the product features: {features}
        2. Analyze the specs: {specs}
        3. Think about what a skeptical buyer would ask.
        4. Think about what a confused user would ask.
        5. Generate high-quality, helpful answers for each question.
        """),
        ("user", "Product Name: {name}\nDescription: {desc}")
    ])

    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({
            "name": product.name,
            "desc": product.description,
            "features": ", ".join(product.features),
            "specs": str(product.specs)
        })
        return {"questions": result.questions}
    except Exception as e:
        print(f"Error in Question Generator Node: {e}")
        return {"questions": []}
