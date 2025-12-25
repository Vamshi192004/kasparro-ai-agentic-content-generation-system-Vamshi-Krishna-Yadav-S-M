from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.state import AgentState
from core.schemas import ProductSchema
import json
import os

def parser_node(state: AgentState):
    raw_data = state['raw_data']
    
    # Initialize Gemini
    # Ensure GOOGLE_API_KEY is set in environment
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ProductSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Data Engineer specializing in E-commerce product data normalization.
        
        Your task is to:
        1. Analyze the raw input JSON.
        2. Extract key product details (Name, Price, Category, Features, Specs).
        3. Identify any competitor data if present.
        4. Normalize the data into a strict schema.
        
        If fields are missing, infer reasonable defaults based on the product context or mark as "N/A".
        Ensure the 'features' list contains at least 5 distinct selling points.
        """),
        ("user", "Raw Data: {raw_data}")
    ])

    chain = prompt | structured_llm
    
    try:
        # Invoke
        clean_data = chain.invoke({"raw_data": json.dumps(raw_data)})
        return {"clean_data": clean_data}
    except Exception as e:
        print(f"Error in Parser Node: {e}")
        # Return None or handle error appropriately in a real system
        return {"clean_data": None}
