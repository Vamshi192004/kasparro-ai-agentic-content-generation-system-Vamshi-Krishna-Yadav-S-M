"""
Question Generator Agent
"""
from core.agent_base import Agent
from core.logic_blocks import LogicBlocks

class QuestionGeneratorAgent(Agent):
    def __init__(self):
        super().__init__("QuestionGeneratorAgent")

    def process(self, product_data):
        self.log("Generating questions...")
        questions = []
        name = product_data['name']

        # 0. Usage Block Question
        usage_text = LogicBlocks.extract_usage_block(product_data)
        questions.append({
            "category": "Usage",
            "question": f"How do I use {name}?",
            "answer": usage_text
        })

        # 1. Feature-based Usage Questions (Generate for every feature)
        for feature in product_data['features']:
            questions.append({
                "category": "Usage",
                "question": f"How does the {feature} benefit my skin?",
                "answer": f"The {feature} in {name} helps to improve skin health and appearance by targeting specific concerns."
            })
            questions.append({
                "category": "Informational",
                "question": f"Is the {feature} suitable for sensitive skin?",
                "answer": f"Yes, the {feature} used in {name} is formulated to be gentle and effective for all skin types."
            })

        # 2. Spec-based Informational Questions
        for key, value in product_data['specs'].items():
            questions.append({
                "category": "Informational",
                "question": f"What is the {key} of {name}?",
                "answer": f"The {key} of {name} is {value}."
            })

        # 3. Safety Questions
        questions.append({
            "category": "Safety",
            "question": f"Is {name} safe for daily use?",
            "answer": f"Yes, {name} is dermatologically tested and safe for daily application."
        })
        questions.append({
            "category": "Safety",
            "question": "Are there any side effects?",
            "answer": "No common side effects have been reported. Patch test recommended."
        })
        questions.append({
            "category": "Safety",
            "question": "Is it safe for pregnant women?",
            "answer": "Please consult your healthcare provider before using new skincare products during pregnancy."
        })

        # 4. Purchase Questions
        questions.append({
            "category": "Purchase",
            "question": f"Where can I buy {name}?",
            "answer": f"{name} is available exclusively on our official website and select retail partners."
        })
        questions.append({
            "category": "Purchase",
            "question": "What is the return policy?",
            "answer": "We offer a 30-day money-back guarantee if you are not satisfied."
        })
        questions.append({
            "category": "Purchase",
            "question": "Do you offer international shipping?",
            "answer": "Yes, we ship to over 50 countries worldwide."
        })

        # 5. Comparison Questions
        questions.append({
            "category": "Comparison",
            "question": f"How is {name} better than competitors?",
            "answer": f"{name} offers a unique blend of premium ingredients like {product_data['features'][0]} at a competitive price."
        })

        return questions
