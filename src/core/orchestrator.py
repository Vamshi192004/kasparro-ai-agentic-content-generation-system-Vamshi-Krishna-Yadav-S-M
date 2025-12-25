"""
Orchestrator - Central Controller
"""
import json
import os
import sys

# Add src to path to allow imports if running from different location
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.parser_agent import ParserAgent
from agents.question_generator_agent import QuestionGeneratorAgent
from agents.faq_page_agent import FAQPageAgent
from agents.product_page_agent import ProductPageAgent
from agents.comparison_page_agent import ComparisonPageAgent

class Orchestrator:
    def __init__(self, input_path):
        self.input_path = input_path
        self.data = None

    def run(self):
        print("Starting Content Generation Pipeline...")

        # 1. Load Data
        print(f"Loading input data from {self.input_path}...")
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found at {self.input_path}")
            return

        # 2. Parse Data
        print("Running Parser Agent...")
        parser = ParserAgent()
        self.data = parser.process(raw_data)
        print("Data parsed successfully.")

        # 3. Generate Questions
        print("Running Question Generator Agent...")
        q_gen = QuestionGeneratorAgent()
        questions = q_gen.process(self.data)
        print(f"Generated {len(questions)} questions.")

        # 4. Generate Pages
        print("Running Page Generation Agents...")
        
        faq_agent = FAQPageAgent()
        faq_page = faq_agent.process(self.data, questions)
        self.save_output('faq.json', faq_page)

        product_agent = ProductPageAgent()
        product_page = product_agent.process(self.data)
        self.save_output('product_page.json', product_page)

        comparison_agent = ComparisonPageAgent()
        comparison_page = comparison_agent.process(self.data)
        self.save_output('comparison_page.json', comparison_page)

        print("Pipeline completed successfully.")

    def save_output(self, filename, content):
        output_path = os.path.join(os.getcwd(), filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        print(f"Saved output to {filename}")

if __name__ == "__main__":
    # For testing directly
    input_file = os.path.join(os.getcwd(), 'dataset.json')
    orchestrator = Orchestrator(input_file)
    orchestrator.run()
