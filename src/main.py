"""
Entry Point
"""
import os
import sys
from core.orchestrator import Orchestrator

def main():
    # Define input path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'dataset.json')
    
    orchestrator = Orchestrator(input_path)
    orchestrator.run()

if __name__ == "__main__":
    main()
