from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.parser_agent import parser_node
from agents.question_generator_agent import qgen_node
from agents.page_agents import faq_node, product_page_node, comparison_node
from agents.reviewer_agent import reviewer_node
from core.logger import get_logger

logger = get_logger(__name__)

def create_graph():
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
        
        if feedback and count < 3: # Limit retries to 3
            logger.info(f"Review failed. Retrying (Attempt {count+1}). Feedback: {feedback}")
            return "qgen" # Loop back to QGen to regenerate everything
        
        if count >= 3:
            logger.warning("Max retries reached. Proceeding with current content.")
            
        return END

    workflow.add_conditional_edges(
        "reviewer",
        check_review,
        {"qgen": "qgen", END: END}
    )

    return workflow.compile()
