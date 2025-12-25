import os
import json
from core.graph import create_graph
from core.state import AgentState
from mock_llm import MockChatGoogleGenerativeAI

# Monkey patch the agents' LLM instantiation
import agents.parser_agent
import agents.question_generator_agent
import agents.page_agents
import agents.reviewer_agent

def mock_chat_google_factory(*args, **kwargs):
    return MockChatGoogleGenerativeAI()

# Override the class
agents.parser_agent.ChatGoogleGenerativeAI = mock_chat_google_factory
agents.question_generator_agent.ChatGoogleGenerativeAI = mock_chat_google_factory
agents.page_agents.ChatGoogleGenerativeAI = mock_chat_google_factory
agents.reviewer_agent.ChatGoogleGenerativeAI = mock_chat_google_factory

def run_test():
    print("Running System Verification with Mock Gemini LLM (Self-Correction Loop)...")
    
    # Create dummy dataset if needed
    raw_data = {"name": "Test Product"}
    
    app = create_graph()
    inputs = {"raw_data": raw_data}
    
    final_state = app.invoke(inputs)
    
    print("\nVerifying Outputs:")
    print(f"FAQ Page Generated: {final_state.get('faq_page') is not None}")
    print(f"Product Page Generated: {final_state.get('product_page') is not None}")
    print(f"Comparison Page Generated: {final_state.get('comparison_page') is not None}")
    print(f"Review Feedback: {final_state.get('review_feedback')}")
    print(f"Revision Count: {final_state.get('revision_count', 0)}")
    
    if final_state.get('faq_page'):
        print("FAQ Page Title:", final_state['faq_page'].title)

if __name__ == "__main__":
    run_test()
