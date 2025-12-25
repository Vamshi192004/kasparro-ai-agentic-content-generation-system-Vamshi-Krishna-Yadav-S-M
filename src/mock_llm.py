from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List, Optional, Any, Dict
from core.schemas import ProductSchema, QuestionSchema, FAQPageSchema, ProductPageSchema, ComparisonPageSchema, ComparisonRow, QuestionList
from agents.reviewer_agent import ReviewOutput
import json

class MockChatGoogleGenerativeAI(BaseChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> "MockChatGoogleGenerativeAI":
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
        self.schema = schema
        return self

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        if self.schema == QuestionList:
            return QuestionList(questions=[
                QuestionSchema(category="Usage", question="How to use?", answer="Apply daily."),
                QuestionSchema(category="Safety", question="Is it safe?", answer="Yes."),
                QuestionSchema(category="Purchase", question="Where to buy?", answer="Online."),
                QuestionSchema(category="Info", question="Ingredients?", answer="Vitamin C."),
                QuestionSchema(category="Info", question="Vegan?", answer="Yes.")
            ])
        elif self.schema == FAQPageSchema:
            return FAQPageSchema(
                title="FAQ Page Title",
                description="FAQ Description Text",
                faqs=[
                    QuestionSchema(category="Usage", question="How to use?", answer="Apply daily."),
                    QuestionSchema(category="Safety", question="Is it safe?", answer="Yes."),
                    QuestionSchema(category="Purchase", question="Where to buy?", answer="Online.")
                ],
                disclaimer="Disclaimer"
            )
        elif self.schema == ProductPageSchema:
            return ProductPageSchema(
                hero_headline="Hero Headline",
                hero_subheadline="Subheadline",
                price_display="$49.99",
                features_list=["Feature 1", "Feature 2", "Feature 3"],
                benefits_list=["Benefit 1", "Benefit 2", "Benefit 3"],
                specs_display={"Volume": "50ml"},
                usage_instructions="Use daily for best results.",
                cta_text="Buy Now"
            )
        elif self.schema == ComparisonPageSchema:
            return ComparisonPageSchema(
                title="Comparison",
                comparison_table=[
                    ComparisonRow(feature="Price", product_value="$10", competitor_value="$12"),
                    ComparisonRow(feature="Quality", product_value="High", competitor_value="Low")
                ],
                summary="Better value overall."
            )
        elif self.schema == ProductSchema:
             return ProductSchema(
                id="123",
                name="GlowBoost",
                category="Skincare",
                price=49.99,
                currency="USD",
                features=["Vitamin C", "Hyaluronic Acid", "SPF 30"],
                specs={"volume": "50ml"},
                description="A great product description that is long enough.",
                competitors=[{"name": "Comp B", "price": 39.99}]
            )
        elif self.schema == ReviewOutput:
            # Simulate approval
            return ReviewOutput(is_approved=True, feedback="")
            
        return None

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Mock"))])

    @property
    def _llm_type(self) -> str:
        return "mock-chat-google-genai"
