*Read this in [Español](README.es.md).*

# SecureContent AI Governance Loop

**Multimodal data protection gateway for enterprise RAG**

SecureContent reviews documents, images, dashboards, audio, and video before they are shared with an AI assistant or added to its index. It detects sensitive information and malicious instructions, preserves provenance and permissions, routes ambiguous cases to human review, and turns corrections into evaluation cases.

> Status: working educational MVP. It does not replace Microsoft Purview, a DLP product, legal review, or an organization's security controls.

## Where to find each evaluation criterion

Every row is verifiable from a fresh clone with the command in the last column.

| Criterion | Where | Command |
|---|---|---|
| Problem description | [Business problem](#business-problem) | — |
| Knowledge base + LLM | `src/securecontent/processor.py`, `search.py`, `rag.py` | `securecontent search "..."` |
| Retrieval evaluation (3 approaches) | `src/securecontent/evaluation.py` | `securecontent evaluate` |
| LLM evaluation (2 prompts) | `SYSTEM_PROMPTS` in `rag.py` | `securecontent evaluate-answers --provider offline` |
| Interface | `app.py` (Streamlit) | `streamlit run app.py` |
| Automated ingestion | `src/securecontent/cli.py` | `securecontent process --input examples/content --output build/chunks.jsonl` |
| Monitoring (6 charts) | `src/securecontent/monitoring.py`, Streamlit tab | `streamlit run app.py` |
| User feedback | thumbs up/down stored in SQLite | `streamlit run app.py` |
| Containerization | `Dockerfile`, `compose.yaml` | `docker compose up --build` |
| Reproducibility | [Quick start](#quick-start), `pyproject.toml` | `python -m unittest discover -s tests -v` |
| Hybrid search | `hybrid_search`, reciprocal-rank fusion in `search.py` | `securecontent evaluate` |
| Document re-ranking | query-token coverage reranker in `search.py` | `securecontent evaluate` |
| Query rewriting | `rewrite_query` in `search.py` | `securecontent evaluate` |

Detailed mapping: [docs/project-rubric.md](docs/project-rubric.md).

## Business problem

Organizations want to reuse SharePoint documents, support notes, Power BI captures, and recordings in RAG applications. Those sources can expose personal data, customer identifiers, credentials, confidential metrics, or instructions designed to manipulate the model. Governing content after indexing it is too late.

```text
Enterprise content
    -> extract text, OCR, frames, and transcript
    -> detect sensitive data and malicious instructions
    -> inherit owner, sensitivity, and access
    -> approve / review / block
    -> redact or minimize
    -> index only the authorized representation
    -> monitor retrieval and feedback
    -> correct and rerun regression tests
```

## Implemented features

- ingestion of Markdown and `.media.json` descriptors;
- stable identifiers and section-based chunking;
- detection of emails, phone numbers, customer identifiers, and credentials;
- blocking of prompt injection and exfiltration attempts in Spanish and English;
- internal states `approved`, `review`, and `blocked`;
- lexical, reproducible-vector, and hybrid search with rewriting and reranking;
- RAG answers with citations plus a local fallback that needs no API;
- OCR and redaction of sensitive image regions;
- local Whisper transcription with text redaction;
- real MP4 sampling, face detection, and blurring with OpenCV;
- import and normalization of Microsoft Purview JSON exports;
- human review, feedback, SQLite, and six monitoring charts;
- Streamlit interface, Docker, and automated tests.

The names `approved`, `review`, and `blocked` are kept as internal values for compatibility; the interface presents them as approved, needs review, and blocked.

## Governance decisions

| Visible state | Internal value | Permitted action |
|---|---|---|
| Approved | `approved` | May enter an authorized index |
| Needs review | `review` | Requires a decision from the data steward |
| Blocked | `blocked` | Quarantined and never indexed automatically |

Credentials, prompt injection, and exfiltration attempts are blocked. Other sensitive data requires human review.

## Quick start

Requires Python 3.11 or 3.12. All commands run **from the repository root**; the CLI resolves `evaluation/` and `examples/` relative to the current directory.

Linux / macOS:

```bash
git clone https://github.com/GabrielaOjcius/securecontent-ai-governance-loop.git
cd securecontent-ai-governance-loop
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[app,multimedia]"
```

Windows PowerShell:

```powershell
git clone https://github.com/GabrielaOjcius/securecontent-ai-governance-loop.git
cd securecontent-ai-governance-loop
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[app,multimedia]"
```

Then, on either platform:

```bash
securecontent process --input examples/content --output build/chunks.jsonl
securecontent search "Who reviews ambiguous findings?"
securecontent evaluate
securecontent evaluate-multimedia
securecontent evaluate-answers --provider offline
python -m unittest discover -s tests -v
```

**No API key is required for the default path**: the RAG flow falls back to an extractive provider and the prompt comparison runs offline.

Verified output on a clean run with Python 3.11.9:

```text
Processed 5 documents into 19 chunks: build/chunks.jsonl
Governance gate: approved=12, review=6, blocked=1
```

`securecontent evaluate` compares three retrieval approaches (lexical chunk MRR 1.0, vector 0.875, hybrid 1.0) and selects lexical. `securecontent evaluate-answers` compares the `strict` and `concise` prompts and selects `strict`. `securecontent evaluate-multimedia` reports precision 1.0 and recall 0.5. The suite runs 23 tests and passes.

To use OpenAI instead of the offline fallback:

```bash
cp .env.example .env      # PowerShell: Copy-Item .env.example .env
# add OPENAI_API_KEY to .env
python -m pip install -e ".[rag]"
securecontent evaluate-answers --provider openai
```

## Interface

```bash
streamlit run app.py
```

Open `http://localhost:8501`. The interface includes the authorized assistant, review queue, multimedia evidence, history, feedback, and monitoring.

### Run with Docker

```bash
docker compose up --build
```

## Power BI demo: MegaCompras BR

The first tab presents a case derived from functional and technical dashboard documentation. The demo separates two sources:

- approved documentation with KPIs, star schema, DAX measures, and insights;
- a synthetic capture containing an email, a customer identifier, and a confidential metric, which stays in review.

Suggested questions:

```text
Which cities concentrate most of the sales?
Which products underperform?
How is the data model organized?
Which indicators appear in the executive summary?
```

The sidebar also accepts `.md`, `.docx`, or `.media.json` uploads. Documents without explicit approval enter as pending and are not automatically used in answers.

Full walkthrough: [demo script](docs/demo-powerbi.md) (Spanish), also available as a Word document: [presentation guide](docs/Guia-presentacion-demo-SecureContent.docx).

## Multimedia processing

OCR and redaction of an image:

```bash
securecontent ocr-redact examples/public-assets/presidio-ocr-test.png \
  --output build/redacted/image.png \
  --report build/reports/image.json
```

Transcription and redaction of audio:

```bash
securecontent transcribe-redact examples/public-assets/whisper-jfk.flac \
  --transcript build/transcripts/audio.txt \
  --output build/redacted/audio.txt \
  --report build/reports/audio.json \
  --model tiny.en
```

MP4 sampling and face blurring:

```bash
securecontent inspect-video path/to/video.mp4 \
  --frames build/video/frames \
  --report build/reports/video.json \
  --every-seconds 2
```

The Haar detector is a local baseline: it can produce false positives and negatives. The resulting frames require human review, and the original binary is never indexed automatically.

## Microsoft Purview

The project includes a testable adapter for Purview JSON exports:

```bash
securecontent import-purview purview-export.json \
  --output build/purview/normalized-assets.json
```

The adapter normalizes identifier, title, owner, and classifications into the SecureContent contract. A live tenant connection still requires credentials, permissions, and an authorized environment; the project does not simulate that access.

## RAG security

The gate inspects both ingested content and incoming queries. It recognizes reproducible patterns of:

- instructions to ignore previous rules;
- requests for the system prompt;
- activation of supposed special modes;
- extraction of secrets, passwords, tokens, or keys;
- encoding intended to evade controls.

These defenses are tested automatically but do not guarantee full protection. A production deployment also needs per-user authorization, tool boundaries, isolation, secure logging, and continuous adversarial evaluation.

## Evaluation and honest limitations

- The retrieval set is small; a perfect score does not demonstrate production quality.
- The public OCR evaluation still shows a false negative, which is why human review is required.
- Face detection is implemented but needs a labeled video set to measure coverage.
- The Purview adapter processes exports; the live API depends on an authorized tenant.
- Anti-attack rules cover known cases and must grow with new adversarial tests.

## Structure

```text
app.py                       Streamlit interface
docs/                        architecture, processing, and governance
evaluation/                  labeled cases
examples/                    synthetic content and public assets
src/securecontent/           implementation
tests/                       automated tests
Dockerfile and compose.yaml  containerized execution
```

## Documentation

- [Architecture](docs/architecture.md)
- [Content processing](docs/content-processing.md)
- [Evaluation and human feedback](docs/evaluation-loop.md)
- [Governance and Microsoft Purview](docs/governance-and-purview.md)
- [Course criteria mapping](docs/project-rubric.md)
