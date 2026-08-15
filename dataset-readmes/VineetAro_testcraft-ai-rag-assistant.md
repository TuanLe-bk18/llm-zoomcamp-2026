# TestCraft AI RAG Assistant

A small RAG app for answering questions about QA, LLM testing, RAG testing, and prompt evaluation.

The app uses a custom JSON knowledge base, retrieves relevant records, sends the retrieved context to an LLM, and shows the answer in a Streamlit UI.

## Features

- JSON-based knowledge base
- Keyword search with `minsearch`
- Vector search with `sentence-transformers`
- Streamlit UI
- SQLite monitoring
- User feedback
- Basic retrieval evaluation

## Project structure

```text
testcraft-ai-rag-assistant/
├── data/
│   └── qa_knowledge.json
├── ingestion/
│   └── load_data.py
├── retrieval/
│   └── vector_search.py
├── llm/
│   └── llm_client.py
├── evaluation/
│   └── retrieval_eval.py
├── rag.py
├── app.py
├── monitoring.py
├── requirements.txt
├── sample_env_file.txt
└── README.md
```

## How it works

```text
question
  -> retrieve relevant documents
  -> build context
  -> build prompt
  -> call LLM
  -> show answer and sources
  -> save monitoring data
```

## Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the project root.

See `sample_env_file.txt` for the environment variables to set, including the GitHub API key.

Example:

```env
GITHUB_TOKEN=your_github_token_here
BASE_URL=https://models.github.ai/inference
MODEL_NAME=openai/gpt-4o-mini
```

Do not commit your real `.env` file.

## Run from terminal

```bash
python rag.py
```

## Run Streamlit app

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Monitoring

The app stores basic runtime data in SQLite:

```text
monitoring.db
```

Stored fields include:

- question
- answer
- sources
- latency
- feedback
- timestamp

`monitoring.db` is local runtime data and should not be committed.

## Evaluation

Retrieval evaluation is kept separate from the app.

Run:

```bash
python evaluation/retrieval_eval.py
```

This compares retrieval results against expected document titles and reports basic metrics such as Hit Rate and MRR.


#### _Evaluation Result_
```
Retrieval Evaluation
--------------------
Questions: 5
Hit Rate@5: 0.6
MRR@5: 0.2
```
## Dataset format

The knowledge base is stored in:

```text
data/qa_knowledge.json
```

Each record should have this structure:

```json
{
  "title": "Example title",
  "topic": "Example topic",
  "content": "Example content"
}
```

## Notes

This is a RAG application, not an agent application.

The focus is on a simple end-to-end flow: ingestion, retrieval, prompt building, LLM response, UI, monitoring, and feedback.