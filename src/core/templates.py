"""
Template Engine
Defines structured templates for content generation.
"""
from abc import ABC, abstractmethod

class Template(ABC):
    @abstractmethod
    def render(self, data):
        pass

class FAQTemplate(Template):
    def render(self, data):
        return {
            "title": data.get("title", "FAQ"),
            "description": data.get("description", ""),
            "faqs": data.get("faqs", []),
            "disclaimer": data.get("disclaimer", "")
        }

class ProductPageTemplate(Template):
    def render(self, data):
        return {
            "meta": data.get("meta", {}),
            "hero": data.get("hero", {}),
            "features": data.get("features", {}),
            "benefits": data.get("benefits", []), # Added field
            "specs": data.get("specs", {}),
            "usage": data.get("usage", ""), # Added field
            "cta": data.get("cta", "Buy Now")
        }

class ComparisonTemplate(Template):
    def render(self, data):
        return {
            "title": data.get("title", "Comparison"),
            "table": data.get("table", {}),
            "summary": data.get("summary", "")
        }
