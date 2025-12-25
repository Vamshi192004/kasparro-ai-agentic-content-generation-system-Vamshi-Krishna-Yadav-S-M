"""
FAQ Page Agent
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.logic_blocks import LogicBlocks
from core.agent_base import Agent
from core.templates import FAQTemplate

class FAQPageAgent(Agent):
    def __init__(self):
        super().__init__("FAQPageAgent")

    def process(self, product_data, questions):
        self.log("Generating FAQ page...")
        template = FAQTemplate()
        
        data = {
            "title": LogicBlocks.generate_seo_title(product_data["name"], "FAQ"),
            "description": f"Frequently asked questions about the {product_data['name']}.",
            "faqs": [
                {
                    "question": q["question"],
                    "answer": q["answer"],
                    "category": q["category"]
                } for q in questions
            ],
            "disclaimer": LogicBlocks.generate_disclaimer()
        }
        return template.render(data)
