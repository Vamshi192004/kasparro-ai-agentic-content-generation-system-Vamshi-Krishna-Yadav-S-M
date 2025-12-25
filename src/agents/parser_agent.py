"""
Parser Agent - Normalizes Input Data
"""
from core.agent_base import Agent

class ParserAgent(Agent):
    def __init__(self):
        super().__init__("ParserAgent")

    def process(self, raw_data):
        self.log("Normalizing input data...")
        # In a real scenario, this would handle various input formats and validation.
        # For this demo, we ensure the structure matches our internal expectation.
        
        return {
            "id": raw_data.get("productId", "UNKNOWN"),
            "name": raw_data.get("productName", "Untitled Product"),
            "category": raw_data.get("category", "General"),
            "price": raw_data.get("price", {"amount": 0, "currency": "USD"}),
            "features": raw_data.get("features", []),
            "specs": raw_data.get("specs", {}),
            "description": raw_data.get("description", ""),
            "competitors": raw_data.get("competitors", [])
        }
