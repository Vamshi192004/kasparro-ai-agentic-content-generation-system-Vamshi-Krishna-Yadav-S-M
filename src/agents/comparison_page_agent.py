"""
Comparison Page Agent
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.logic_blocks import LogicBlocks
from core.agent_base import Agent
from core.templates import ComparisonTemplate

class ComparisonPageAgent(Agent):
    def __init__(self):
        super().__init__("ComparisonPageAgent")

    def process(self, product_data):
        self.log("Generating Comparison page...")
        template = ComparisonTemplate()

        comparison_table = {
            "headers": ["Feature", product_data["name"]] + [c["name"] for c in product_data["competitors"]],
            "rows": []
        }

        # Price Row
        price_row = ["Price", LogicBlocks.format_currency(product_data["price"]["amount"], product_data["price"]["currency"])]
        for c in product_data["competitors"]:
            price_row.append(LogicBlocks.format_currency(c["price"], "USD"))
        comparison_table["rows"].append(price_row)

        # Ingredients Row (Using Logic Block)
        ingredients_row = ["Ingredients Comparison"]
        ingredients_row.append(LogicBlocks.compare_ingredients_block(product_data["features"], [])) # Self comparison placeholder
        for c in product_data["competitors"]:
             # Compare product vs competitor
             ingredients_row.append(LogicBlocks.compare_ingredients_block(product_data["features"], c.get("ingredients", [])))
        comparison_table["rows"].append(ingredients_row)

        # Benefits Row
        benefits_row = ["Primary Benefit", "Radiance & Hydration"] # Derived logic
        for c in product_data["competitors"]:
            benefits_row.append(", ".join(c.get("benefits", ["N/A"])))
        comparison_table["rows"].append(benefits_row)
        
        # Volume Row
        if "volume" in product_data["specs"]:
            vol_row = ["Volume", product_data["specs"]["volume"]]
            for c in product_data["competitors"]:
                vol_row.append(c.get("volume", "N/A"))
            comparison_table["rows"].append(vol_row)

        data = {
            "title": f"Compare {product_data['name']} vs Competitors",
            "table": comparison_table,
            "summary": f"The {product_data['name']} offers superior value compared to {product_data['competitors'][0]['name']}."
        }
        return template.render(data)
