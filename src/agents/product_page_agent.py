"""
Product Page Agent
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.logic_blocks import LogicBlocks
from core.agent_base import Agent
from core.templates import ProductPageTemplate

class ProductPageAgent(Agent):
    def __init__(self):
        super().__init__("ProductPageAgent")

    def process(self, product_data):
        self.log("Generating Product page...")
        template = ProductPageTemplate()

        data = {
            "meta": {
                "title": LogicBlocks.generate_seo_title(product_data["name"], product_data["category"]),
                "description": product_data["description"][:150] + "..."
            },
            "hero": {
                "headline": product_data["name"],
                "subheadline": f"Experience the future of {product_data['category']}",
                "price": LogicBlocks.format_currency(product_data["price"]["amount"], product_data["price"]["currency"])
            },
            "features": {
                "title": "Key Features",
                "list": product_data["features"]
            },
            "benefits": LogicBlocks.generate_benefits_block(product_data["features"]),
            "specs": {
                "title": "Technical Specifications",
                "data": product_data["specs"]
            },
            "usage": LogicBlocks.extract_usage_block(product_data),
            "cta": "Buy Now"
        }
        return template.render(data)
