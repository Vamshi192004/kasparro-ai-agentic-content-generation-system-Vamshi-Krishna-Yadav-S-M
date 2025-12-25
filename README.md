# Agentic Content Generation System

## Overview
A production-ready **Agentic AI System** that transforms raw product data into high-converting marketing content. Built on **LangGraph** and **Google Gemini**, it features a robust multi-agent architecture with strict data validation.

## Features
-  **True Agentic Reasoning**: Agents plan and reason before generating.
-  **Self-Correction Loop**: Reviewer Agent critiques and regenerates poor content.
-  **Powered by Gemini**: Uses `gemini-1.5-flash` for fast, high-quality inference.
-  **Robust Architecture**: Cyclic Graph with error handling and retries.
-  **Strict Validation**: 100% Pydantic-validated JSON outputs.

## Repository Structure
```text
/src
  /agents       # LLM-powered Worker Agents
  /core         # Graph definition, State, and Schemas
  main_graph.py # Entry point
/docs
  projectdocumentation.md  # Detailed system design
dataset.json    # Input data
```

## Quick Start

### 1. Prerequisites
- Python 3.9+
- Google Cloud API Key

### 2. Installation
```bash
pip install langchain langgraph langchain-google-genai pydantic python-dotenv
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### 4. Run the Pipeline
```bash
python src/main_graph.py
```

### 5. CLI Usage (Custom Tone)
You can customize the tone of voice (e.g., "Luxury", "Witty"):
```bash
python src/main_graph.py --tone "Luxury" --input "dataset.json"
```

## Documentation
See [docs/projectdocumentation.md](docs/projectdocumentation.md) for the full architectural breakdown.

## Architecture Decision Record (ADR)

### 1. Why LangGraph?
We chose **LangGraph** over simple chains because this system requires **cyclic capabilities** (loops) for self-correction. Traditional DAGs cannot easily handle "retry until good" logic without complex external controllers. LangGraph's state machine model is perfect for this agentic behavior.

### 2. Why Google Gemini?
**Gemini 1.5 Flash** was selected for its high speed and large context window, allowing us to pass the entire product schema and generated questions between agents without hitting token limits or incurring high latency.

### 3. Why Pydantic?
To ensure 100% machine-readable output, we strictly enforce schemas. LLMs can be unpredictable; Pydantic acts as a "Guardrail" that guarantees the downstream systems (e.g., a frontend) never receive malformed JSON.
