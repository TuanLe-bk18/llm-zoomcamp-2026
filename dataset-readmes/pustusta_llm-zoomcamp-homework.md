# LLM Zoomcamp Homework

Homework exercises for the [DataTalksClub LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp). The repository follows the 2026 course modules and explores retrieval-augmented generation (RAG), agentic workflows, vector search, orchestration, and evaluation.

## Contents

| File | Topic |
| --- | --- |
| `llm-zoomcamp-hw1.ipynb` | Text search, RAG with the OpenAI Responses API, chunking, and an agentic search loop |
| `llm-zoomcamp-hw2.ipynb` | Local ONNX embeddings, vector search, text search, and reciprocal rank fusion |
| `llm-zoomcamp-hw3/` | Kestra workflows comparing chat with and without RAG, plus a simple AI agent |
| `llm-zoomcamp-hw4.ipynb` | Ground-truth generation and retrieval evaluation |
| `rag_helper.py` | Reusable RAG pipeline built around a search index and OpenAI client |
| `evaluation_utils.py` | Structured LLM calls, retries, token-cost tracking, and concurrent evaluation helpers |
| `embedder.py` | Local sentence embeddings using ONNX Runtime |
| `download.py` | Downloads the ONNX model and tokenizer from Hugging Face |
| `ground-truth.csv` | Evaluation questions and their source-document identifiers |

`llm-zoomcamp-hw3.ipynb` is currently an empty placeholder; the homework implementation for that module is in the adjacent YAML directory.

## Setup

Python 3.10 or newer is recommended. From the repository root, create a virtual environment and install the notebook dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install \
  jupyter openai pydantic python-dotenv pandas \
  numpy tqdm minsearch gitsource \
  onnxruntime tokenizers huggingface-hub
```

Configure the OpenAI API key before running notebooks that call an LLM:

```bash
export OPENAI_API_KEY="your-api-key"
```

Do not commit API keys. The `.env` file is ignored by Git and can be used by notebooks that load variables with `python-dotenv`:

```text
OPENAI_API_KEY=your-api-key
```

The embedding model is already present under `models/Xenova/all-MiniLM-L6-v2`. If it needs to be downloaded again, run:

```bash
python download.py
```

## Running the notebooks

Start Jupyter from this directory so relative paths to the model, helper modules, and CSV file resolve correctly:

```bash
jupyter lab
```

Open the notebooks in numerical order. Some cells retrieve course material from GitHub or call external APIs, so an internet connection is required for those exercises. LLM calls may incur API usage costs.

## Kestra workflows

The `llm-zoomcamp-hw3/` directory contains workflows intended to be imported into a Kestra instance:

- `1_chat_without_rag.yaml` queries Gemini without retrieved context.
- `2_chat_with_rag.yaml` ingests Kestra release notes and queries them with RAG.
- `4_simple_agent.yaml` runs a configurable summarization agent and reports token usage.

Set `GEMINI_API_KEY` in the Kestra environment or secret store before executing these flows. The RAG workflow also needs network access to retrieve the referenced Kestra documentation.

## Notes

- The notebooks read course documents from a pinned commit of the upstream `DataTalksClub/llm-zoomcamp` repository.
- `evaluation_utils.py` contains model-specific token prices used for homework calculations; update them before relying on the estimates for other models or current billing.
- Generated caches such as `.ipynb_checkpoints`, `__pycache__`, and local secrets should remain untracked.
