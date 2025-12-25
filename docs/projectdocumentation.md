# Project Documentation: AI-Powered Content Generation Pipeline

## 1. Problem Statement
The goal is to design and implement a modular, agentic automation system that can ingest raw product data and autonomously generate structured, machine-readable content pages (FAQ, Product Page, Comparison Page). The system must avoid monolithic scripts, ensuring clear separation of concerns, reusable logic, and a defined orchestration flow.

## 2. Solution Overview
The solution is a Python-based pipeline utilizing a centralized **Orchestrator** to coordinate a set of specialized **Agents**.
- **Architecture**: Orchestrator -> Parser -> Question Generator -> Page Agents.
- **Tech Stack**: Python 3.
- **Key Features**:
  - **Modular Agents**: Each agent has a single responsibility (Parsing, Question Generation, Page Creation).
  - **Custom Template Engine**: A structured definition of fields and rules for consistent output.
  - **Reusable Logic Blocks**: Shared modules for common transformations (e.g., ingredient comparison, benefit extraction).
  - **JSON Output**: All artifacts are strictly machine-readable.

## 3. Scopes & Assumptions
### Scope
- **Input**: Single product JSON file (`dataset.json`).
- **Output**: Three specific JSON files (`faq.json`, `product_page.json`, `comparison_page.json`).
- **Domain**: Product marketing content (specifically tested with Skincare products).

### Assumptions
- The input JSON structure is relatively stable (though the Parser handles normalization).
- "Competitor" data is provided within the input dataset for comparison logic.
- No external LLM APIs are used; "intelligence" is simulated via rule-based logic blocks and templates for this architectural demonstration.

## 4. System Design
### 4.1. Architecture Diagram
![System Architecture Diagram](SystemDesign.png)

`Input (JSON) -> [Orchestrator] -> [Parser Agent] -> [Question Generator Agent] -> [Page Agents] -> Output (JSON)`

### 4.2. Components
1.  **Orchestrator**: The controller that manages the DAG (Directed Acyclic Graph) of the pipeline.
2.  **Logic Blocks**: Reusable functions (`generate_benefits_block`, `compare_ingredients_block`, etc.) used by agents to transform data.
3.  **Template Engine**: Defines the schema and filling logic for each page type, ensuring structural consistency.
4.  **Agents**:
    - `ParserAgent`: Normalizes input.
    - `QuestionGeneratorAgent`: Uses `extract_usage_block` to create questions.
    - `FAQPageAgent`: Fills the FAQ Template.
    - `ProductPageAgent`: Fills the Product Page Template.
    - `ComparisonPageAgent`: Uses `compare_ingredients_block` to fill the Comparison Template.

### 4.3. Data Flow
1.  **Ingest**: Raw data loaded.
2.  **Normalize**: Parser creates internal model.
3.  **Enrich**: Question Generator adds 15+ questions.
4.  **Transform**: Page agents apply Logic Blocks to data.
5.  **Render**: Data is mapped to Templates.
6.  **Export**: JSON files saved.
