# AI-Powered Content Generation Pipeline

## Overview
This project implements a modular, agentic automation system that autonomously generates structured content pages (FAQ, Product, Comparison) from raw product data. It features a custom template engine, reusable logic blocks, and a centralized orchestration flow.

## Repository Structure
```text
/src
  /agents       # Specialized worker agents
  /core         # Orchestrator, Logic Blocks, Templates
  main.py       # Entry point
/docs
  projectdocumentation.md  # Detailed system documentation
  SystemDesign.png         # Architecture diagram
dataset.json    # Input data
```

## Getting Started

### Prerequisites
- Python 3.8+

### Installation
Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

### Usage
Run the pipeline:
```bash
python src/main.py
```

The system will generate `faq.json`, `product_page.json`, and `comparison_page.json` in the root directory.

## Documentation
For detailed system design and architecture, please refer to [docs/projectdocumentation.md](docs/projectdocumentation.md).
