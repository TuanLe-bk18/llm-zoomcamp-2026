# ⛽ PEKA — Petroleum Enterprise Knowledge Assistant
## Sample Data Mode — Complete Setup Guide

A RAG-powered bilingual (Arabic + English) knowledge assistant that runs entirely
on **local sample documents** — no SharePoint, no Active Directory needed.

---

## What's Included

### 10 Sample Documents (in `sample_data/`)

| Library | File | Language |
|---------|------|----------|
| Procedures & SOPs | Well Control Procedure - ESD-001 | English |
| Procedures & SOPs | Gas Compressor Maintenance - MAINT-045 | English |
| Procedures & SOPs | H2S Safety Procedure - HSE-012 | English |
| Procedures & SOPs | إجراء صيانة مضخات الحقن (Pump Maintenance) | **Arabic** |
| Meeting Minutes | HSE Committee Meeting - March 2024 | English |
| Meeting Minutes | Q1 2024 Production Review | English |
| Meeting Minutes | محضر اجتماع مجلس الإدارة (Board Meeting) | **Arabic** |
| Technical Reports | Reservoir Performance Report 2024 | English |
| Technical Reports | Drilling Completion Report - Well A-16 | English |
| HSE Documents | HSE Annual Performance Report 2023 | English |

### Architecture

```
sample_data/ (10 .txt files)
      ↓
Local File Loader (no SharePoint needed)
      ↓
Text Extraction + Bilingual Chunking (500 chars, 100 overlap)
      ↓
multilingual-e5-large Embeddings (Arabic + English, 1024 dims)
      ↓
Qdrant Vector Database (local Docker container)
      ↓
FastAPI + Claude claude-sonnet-4-6 (RAG pipeline)
      ↓
React Chat Interface (dark theme, RTL Arabic support)
```

---

## Prerequisites

| Tool | Required | Install |
|------|----------|---------|
| Python 3.11+ | ✅ Yes | https://python.org |
| Docker Desktop | ✅ Yes | https://docker.com/products/docker-desktop |
| Node.js 20+ | Optional (frontend only) | https://nodejs.org |
| Anthropic API Key | ✅ Yes | https://console.anthropic.com |

---

## Step-by-Step Setup

### Option A — Automated Setup (Recommended)

**Windows:**
```cmd
scripts\setup_windows.bat
```

**Linux / Mac:**
```bash
chmod +x scripts/setup.sh
bash scripts/setup.sh
```

---

### Option B — Manual Setup (Step by Step)

Follow these steps if you prefer to understand each part.

#### Step 1 — Create your .env file

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:
```dotenv
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
```

Get your key from: https://console.anthropic.com

---

#### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs: `anthropic`, `sentence-transformers`, `qdrant-client`, `fastapi`, `uvicorn`

> ⚠️ First time takes 2-3 minutes. The embedding model (560 MB) downloads separately in Step 4.

---

#### Step 3 — Start Qdrant (Vector Database)

```bash
docker run -d \
  --name peka-qdrant \
  -p 6333:6333 \
  -v peka-qdrant-data:/qdrant/storage \
  qdrant/qdrant:v1.10.1
```

**Windows:**
```cmd
docker run -d --name peka-qdrant -p 6333:6333 -v peka-qdrant-data:/qdrant/storage qdrant/qdrant:v1.10.1
```

Verify it's running:
```bash
curl http://localhost:6333/health
# → {"title":"qdrant - vector search engine","version":"..."}
```

Or open: http://localhost:6333/dashboard

---

#### Step 4 — Run Document Ingestion

```bash
python -m backend.ingestion.runner --reset
```

This will:
1. Download `intfloat/multilingual-e5-large` model (~560 MB, first run only)
2. Load all 10 sample documents from `sample_data/`
3. Split into chunks (bilingual Arabic/English aware)
4. Generate embeddings
5. Index into Qdrant

**Expected output:**
```
INFO: Loading local sample data from: sample_data/
INFO: Loading library 'HSE Documents' from folder: hse/
INFO:   [1] Hse Annual Report 2023 (HSE Documents) → 18 chunks
INFO: Loading library 'Meeting Minutes' from folder: meetings/
INFO:   [2] Board Meeting Arabic 2024 (Meeting Minutes) → 12 chunks (lang=ar)
INFO:   [3] Hse Committee March 2024 (Meeting Minutes) → 15 chunks
INFO:   [4] Production Review Q1 2024 (Meeting Minutes) → 14 chunks
INFO: Loading library 'Procedures & SOPs' from folder: procedures/
INFO:   [5] Compressor Maintenance (Procedures & SOPs) → 16 chunks
INFO:   [6] H2S Safety Procedure (Procedures & SOPs) → 14 chunks
INFO:   [7] Pump Maintenance Arabic (Procedures & SOPs) → 11 chunks (lang=ar)
INFO:   [8] Well Control Procedure (Procedures & SOPs) → 13 chunks
INFO: Loading library 'Technical Reports' from folder: technical/
INFO:   [9] Drilling Report Well A16 (Technical Reports) → 17 chunks
INFO:  [10] Reservoir Report 2024 (Technical Reports) → 19 chunks
==================================================
INGESTION COMPLETE
  Documents loaded:  10
  Chunks created:    149
  Vectors indexed:   149
  Qdrant dashboard:  http://localhost:6333/dashboard
==================================================
```

> ⏱ Takes 3-8 minutes on first run (model download). Subsequent runs take ~30 seconds.

---

#### Step 5 — Start the API

```bash
# Load environment variables first
# Windows:
set ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# Linux/Mac:
export $(cat .env | xargs)

# Start API
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:
```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"PEKA API","mode":"sample-data"}
```

Interactive API docs: http://localhost:8000/docs

---

#### Step 6 — Start the Frontend

In a **new terminal**:

```bash
cd frontend
npm install          # first time only (~2 minutes)
npm start            # starts on http://localhost:3000
```

---

#### Step 7 — Open PEKA

Open your browser: **http://localhost:3000**

**Login:** Any username and password (sample mode accepts all)

---

## Testing

Run the automated test to verify everything works:

```bash
python scripts/test_pipeline.py
```

Expected output:
```
==================================================
  PEKA Pipeline Test
==================================================

1. Testing Qdrant connection...
   ✓ Qdrant connected — 149 vectors indexed

2. Testing embedding model...
   ✓ Embedding model OK — dim=1024

3. Testing retrieval...
   ✓ Retrieval OK — top result:
     Title:   Well Control Procedure
     Library: Procedures & SOPs
     Score:   0.912

4. Testing full RAG pipeline (calls Claude API)...
   ✓ Question (en): What is the ESD procedure for a well?…
     Answer preview: According to the Well Control Procedure (ESD-001)…
   ✓ Question (ar): ما هي حدود التعرض لـ H2S؟…
     Answer preview: وفقاً لإجراء السلامة HSE-012…

5. Testing API endpoint...
   ✓ API healthy: {'status': 'ok', 'service': 'PEKA API'}

==================================================
  RESULTS
==================================================
  ✓ Qdrant
  ✓ Embeddings
  ✓ Retrieval
  ✓ RAG
  ✓ API
==================================================
```

---

## Sample Questions to Try

**English:**
```
What is the emergency shutdown procedure for a well?
What decisions were made in the HSE committee meeting March 2024?
What is the API gravity of the crude oil?
What are the H2S exposure limits and required PPE?
How often should compressor oil be changed?
How was Well A-16 drilling performance vs budget?
What was the Q1 2024 production vs target?
```

**Arabic:**
```
ما هو إجراء الإغلاق الطارئ للبئر؟
ما هي قرارات اجتماع لجنة السلامة مارس 2024؟
ما هي متطلبات صيانة مضخات الحقن؟
ما هي حدود التعرض لغاز H2S؟
ما هو إجمالي إنتاج النفط في الربع الأول 2024؟
ما هي قرارات مجلس الإدارة للميزانية 2024؟
```

---

## Adding Your Own Documents

1. Create a `.txt` file in the appropriate `sample_data/` subfolder:
   - `sample_data/procedures/` → shows as "Procedures & SOPs"
   - `sample_data/meetings/`   → shows as "Meeting Minutes"
   - `sample_data/technical/`  → shows as "Technical Reports"
   - `sample_data/hse/`        → shows as "HSE Documents"

2. Add a header block at the top (optional but recommended):
   ```
   DOCUMENT: My Document Title
   LIBRARY: Procedures & SOPs
   AUTHOR: Your Name
   DATE: 2024-01-01
   ```

3. Re-run ingestion:
   ```bash
   python -m backend.ingestion.runner --reset
   ```

---

## Switching to SharePoint (Production Mode)

When you're ready to connect to real SharePoint:

1. Install additional dependencies:
   ```bash
   pip install requests-ntlm ldap3 PyJWT redis
   ```

2. Copy and fill in `config/config.yaml` with your SharePoint URLs and AD settings

3. Run ingestion in SharePoint mode:
   ```bash
   python -m backend.ingestion.runner --sharepoint
   ```

See `docs/IMPLEMENTATION_GUIDE.md` for the complete SharePoint + AD setup guide.

---

## Project Structure

```
peka-sample/
│
├── sample_data/                ← 10 petroleum documents (txt)
│   ├── procedures/             ← SOPs and safety procedures (EN + AR)
│   ├── meetings/               ← Meeting minutes (EN + AR)
│   ├── technical/              ← Engineering reports
│   └── hse/                   ← Health, Safety, Environment reports
│
├── backend/
│   ├── ingestion/
│   │   ├── local_loader.py     ← Reads from sample_data/ (replaces SharePoint)
│   │   ├── processor.py        ← Text extraction + bilingual chunking
│   │   └── runner.py           ← Orchestrates ingestion pipeline
│   ├── rag/
│   │   └── pipeline.py         ← Embed → Retrieve → Generate (Claude)
│   └── api/
│       └── main.py             ← FastAPI REST endpoints
│
├── frontend/
│   └── src/
│       ├── App.jsx             ← React chat UI with RTL support
│       └── App.css             ← Dark petroleum theme
│
├── scripts/
│   ├── setup.sh                ← Linux/Mac one-command setup
│   ├── setup_windows.bat       ← Windows one-command setup
│   └── test_pipeline.py        ← End-to-end pipeline test
│
├── docker/
│   ├── Dockerfile.api          ← API container
│   └── Dockerfile.frontend     ← Frontend container
│
├── docker-compose.yml          ← Full Docker stack
├── requirements.txt            ← Python dependencies
├── .env.example                ← Environment template
└── README.md                   ← This file
```

---

## Troubleshooting

### "Cannot connect to Qdrant"
```bash
# Check if Qdrant container is running
docker ps | grep qdrant

# If not running, start it:
docker start peka-qdrant

# If never created:
docker run -d --name peka-qdrant -p 6333:6333 qdrant/qdrant:v1.10.1
```

### "No vectors indexed" / "No relevant documents found"
```bash
# Re-run ingestion with --reset flag
python -m backend.ingestion.runner --reset
```

### "ANTHROPIC_API_KEY not set"
```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-...

# Or add it to .env and run: source .env (Linux/Mac)
```

### "Module not found" errors
```bash
# Run from the project ROOT directory, not from inside backend/
cd /path/to/peka-sample
python -m backend.ingestion.runner  # correct ✓
# NOT: cd backend && python ingestion/runner.py  ✗
```

### Embedding model download is very slow
The `intfloat/multilingual-e5-large` model is 560 MB. It downloads once and is cached.
Default cache location:
- Linux/Mac: `~/.cache/huggingface/`
- Windows: `C:\Users\<you>\.cache\huggingface\`

### Frontend shows blank page / CORS error
Make sure both API and frontend are running:
- API: `uvicorn backend.api.main:app --port 8000`
- Frontend: `cd frontend && npm start`
- Check browser console for the exact error

---

## Key Files to Understand First

| File | What it does | Lines |
|------|-------------|-------|
| `backend/ingestion/local_loader.py` | Reads .txt files, builds document objects | ~120 |
| `backend/ingestion/processor.py` | Chunks text (bilingual Arabic/English) | ~170 |
| `backend/ingestion/runner.py` | Full ingestion pipeline orchestration | ~130 |
| `backend/rag/pipeline.py` | Embed → Qdrant search → Claude generate | ~180 |
| `backend/api/main.py` | FastAPI endpoints (/chat, /search, /auth) | ~120 |
| `frontend/src/App.jsx` | React chat UI with RTL + citations | ~200 |
