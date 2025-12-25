# Project Documentation: Agentic Content Generation System

## 1. Executive Summary
This project implements a state-of-the-art, **Agentic AI Pipeline** for automating e-commerce content creation. Unlike traditional script-based automation, this system utilizes a **Directed Acyclic Graph (DAG)** architecture powered by **Google Gemini** to reason, plan, and generate high-quality, structured content (FAQs, Product Pages, Comparisons).

## 2. System Architecture

### 2.1. Core Frameworks
- **LangGraph**: Manages the orchestration, state, and control flow (DAG).
- **LangChain**: Provides the interface for LLM interaction and prompt management.
- **Pydantic**: Enforces strict data validation and schema compliance for all outputs.
- **Google Gemini (`gemini-1.5-flash`)**: The underlying intelligence engine.

### 2.2. Architecture Diagrams
![System Architecture](System Architecture.png)
![System Design](SystemDesign.png)

*Note: The system now implements a **Cyclic Graph**. If the Reviewer Agent rejects the content, the flow loops back to the Question Generator or Page Agents for regeneration.*

### 2.3. Data Flow
1.  **Ingestion**: Raw JSON data is loaded into the `AgentState`.
2.  **Parsing Node**: The **Parser Agent** normalizes the data.
3.  **Reasoning Node**: The **Question Generator Agent** creates strategic questions.
4.  **Generation Nodes (Parallel)**: FAQ, Product Page, and Comparison Agents generate content.
5.  **Review Node**: The **Reviewer Agent** critiques the output against quality criteria.
    *   **Pass**: Pipeline finishes.
    *   **Fail**: Feedback is added to state, and flow **loops back** to Step 3 (max 3 retries).
6.  **Output**: Final JSON artifacts are validated and saved.

## 3. Agent Specifications

### 3.1. Parser Agent
- **Goal**: Data Normalization.
- **Input**: Raw Dictionary.
- **Output**: `ProductSchema` (Pydantic).
- **Logic**: Uses LLM to extract structured fields from unstructured text.

### 3.2. Question Generator Agent
- **Goal**: User Intent Prediction.
- **Input**: `ProductSchema`.
- **Output**: `List[QuestionSchema]`.
- **Logic**: Generates questions across 4 categories (Usage, Safety, Purchase, Informational).

### 3.3. Page Agents
- **Goal**: Content Synthesis.
- **Input**: `ProductSchema` + `List[QuestionSchema]`.
- **Output**: Page-specific Schemas (`FAQPageSchema`, etc.).
- **Logic**: Uses role-playing prompts (e.g., "You are a Copywriting Expert") to generate persuasive text.

## 4. Robustness & Reliability
- **State Management**: A centralized `AgentState` ensures all agents have access to the latest data context.
- **Error Handling**: Each node implements `try/except` blocks to handle API failures gracefully.
- **Conditional Logic**: The graph includes checks (e.g., "Did parsing succeed?") to prevent cascading failures.
- **Schema Validation**: All LLM outputs are forced into Pydantic models, guaranteeing valid JSON.

## 5. Setup & Configuration
1.  **Environment**: Create a `.env` file with `GOOGLE_API_KEY`.
2.  **Dependencies**: `pip install -r requirements.txt` (or manually install `langchain`, `langgraph`, `pydantic`, `python-dotenv`, `langchain-google-genai`).
3.  **Execution**: Run `python src/main_graph.py`.
