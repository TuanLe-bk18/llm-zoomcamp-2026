# 🖥️ IT Infrastructure Assistant

An AI-powered Retrieval-Augmented Generation (RAG) assistant designed for IT Infrastructure documentation.

The assistant allows administrators and engineers to ask natural language questions about technical documentation such as:

- Active Directory
- VMware
- Windows Server
- Linux
- PowerVM
- Exchange Server
- Networking
- PDF Documentation

The system retrieves the most relevant document chunks from a local Chroma vector database and generates accurate answers using Google's Gemini API.

---

# 🚀 Features

- 📄 PDF document indexing
- 🔍 Semantic Search using BGE Embeddings
- 🧠 Retrieval-Augmented Generation (RAG)
- 🤖 Google Gemini Integration
- 💾 ChromaDB Vector Database
- 💬 Streamlit Chat Interface
- 📚 Source Citation
- ⚡ Fast local search

---

# 🏗 Architecture

```

User Question

↓

Embedding Model
(BAAI/bge-small-en-v1.5)

↓

ChromaDB Vector Search

↓

Top-K Relevant Chunks

↓

Gemini 3.1 Flash Lite

↓

Final Answer + Sources

```

---

# 📂 Project Structure

```

IT-Infrastructure-Assistant/

│

├── app.py                 # Streamlit UI

├── rag.py                 # RAG Pipeline

├── embeddings.py          # Embedding Model

├── vector_store.py        # ChromaDB Search

├── build_index.py         # Index Builder

├── document_loader.py     # PDF Loader

├── chunker.py             # Text Chunking

├── config.py

├── chroma_db/

├── data/

│     ├── ActiveDirectory.pdf

│     ├── VMware.pdf

│     └── Windows.pdf

└── requirements.txt

```

---

# ⚙ Technologies

| Component | Technology |
|------------|------------|
| LLM | Google Gemini 3.1 Flash Lite |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| Vector Database | ChromaDB |
| UI | Streamlit |
| Language | Python 3.12 |

---

# 📦 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/IT-Infrastructure-Assistant.git

cd IT-Infrastructure-Assistant
```

Create virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

Install requirements

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure API Key

Create a `.env` file

```text
GOOGLE_API_KEY=YOUR_API_KEY
```

---

# 📚 Index Your Documents

Place PDF files inside

```

data/

```

Build the index

```bash
python build_index.py
```

---

# ▶ Run the Application

```bash
streamlit run app.py
```

---

# 💬 Example Questions

```

How to install Active Directory?

What is an authoritative restore of SYSVOL?

How to configure VMware HA?

What are FSMO Roles?

Explain DNS Forwarders.

```

---
## Evaluation

The project includes a custom evaluation module to measure RAG response quality.

Metrics:

- Keyword Coverage
- Response Length Quality
- Overall Score

Run evaluation:

```bash
python -m evaluation.run_evaluation
#========================
# 📷 Screenshots

## Home Page

```

screenshots/home.png

```

## Search Result

```

screenshots/search.png

```

## Source References

```

screenshots/sources.png

```

---

# 📈 Example Output

Question

```

What is an authoritative restore of SYSVOL?

```

Answer

```

An authoritative restore of SYSVOL specifies that the copy
restored from backup becomes authoritative for the domain.
Active Directory replicates this version to all domain
controllers after the required configuration steps.

```

Sources

```

active_directory_operation_guide_part_1.pdf (Page 32)

active_directory_operation_guide_part_1.pdf (Page 27)

active_directory_operation_guide_part_1.pdf (Page 26)

```

---

# 📊 Current Capabilities

- Answer questions from indexed PDFs
- Semantic similarity search
- Source attribution
- Multi-document retrieval
- Streamlit chat interface

---

# 🔮 Future Improvements

- Conversation Memory
- Hybrid Search (BM25 + Vector Search)
- Cross Encoder Reranking
- Multi-turn Conversations
- Upload PDFs from UI
- Streaming Responses
- User Authentication

---

# 👤 Author

**Ibrahim Hashem**

Server & Storage Team

Badr El Din Petroleum Company (BAPETCO)

Egypt

---

# 📄 License

MIT License
