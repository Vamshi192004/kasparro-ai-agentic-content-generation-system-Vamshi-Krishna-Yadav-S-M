import os
import json
import argparse
from dotenv import load_dotenv
from core.graph import create_graph

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI Content Generation Pipeline")
    parser.add_argument("--input", default="dataset.json", help="Path to input JSON file")
    parser.add_argument("--tone", default="Professional", help="Tone of voice for content (e.g. Witty, Luxury)")
    args = parser.parse_args()

    # Load input data
    input_path = os.path.join(os.path.dirname(__file__), '..', args.input)
    if not os.path.exists(input_path):
        # Try absolute path
        input_path = args.input
        
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"Starting LangGraph Pipeline with Tone: {args.tone}...")
    app = create_graph()
    
    # Initialize State
    initial_state = {
        "raw_data": raw_data,
        "revision_count": 0,
        "tone": args.tone
    }
    
    # Stream output to see progress
    # Note: invoke() returns the final state, stream() yields updates.
    # For a CLI, streaming is nice, but we need the final state to save files.
    # We can use invoke() for simplicity in this CLI version.
    
    final_state = app.invoke(initial_state)
    
    # Save Outputs
    print("Saving outputs...")
    
    if final_state.get('faq_page'):
        with open('faq.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['faq_page'].dict(), f, indent=2)
        print("Saved faq.json")
    else:
        print("Skipped faq.json (Generation failed or stopped early)")
        
    if final_state.get('product_page'):
        with open('product_page.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['product_page'].dict(), f, indent=2)
        print("Saved product_page.json")
    else:
        print("Skipped product_page.json")
        
    if final_state.get('comparison_page'):
        with open('comparison_page.json', 'w', encoding='utf-8') as f:
            json.dump(final_state['comparison_page'].dict(), f, indent=2)
        print("Saved comparison_page.json")
    else:
        print("Skipped comparison_page.json")
        
    print("Pipeline execution finished.")

if __name__ == "__main__":
    # Ensure API Key is set
    if "GOOGLE_API_KEY" not in os.environ:
        print("WARNING: GOOGLE_API_KEY not found in environment variables.")
        print("Please set it to run the Gemini agents.")
        # For demo purposes, we might exit or let it fail
    
    main()
