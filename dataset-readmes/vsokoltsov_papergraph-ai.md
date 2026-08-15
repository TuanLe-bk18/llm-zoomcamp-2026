# PaperGraph AI

[![CI](https://github.com/vsokoltsov/papergraph-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/vsokoltsov/papergraph-ai/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/vsokoltsov/papergraph-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/vsokoltsov/papergraph-ai)

![](./docs/cover.png)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Agent-1C3C3C)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Graph-1C3C3C)
![MCP](https://img.shields.io/badge/MCP-Agent_Tools-000000)
![OpenAI](https://img.shields.io/badge/OpenAI-LLM-412991?logo=openai&logoColor=white)
![OpenAlex](https://img.shields.io/badge/OpenAlex-Papers-2B6CB0)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C)
![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-4581C3?logo=neo4j&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Feedback-4169E1?logo=postgresql&logoColor=white)
![dlt](https://img.shields.io/badge/dlt-Ingestion-F5CD21)
![Grafana](https://img.shields.io/badge/Grafana-Monitoring-F46800?logo=grafana&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white)
![Logfire](https://img.shields.io/badge/Logfire-Observability-EF5B25)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## 🧩 Problem Description

![](./docs/infographic.png)

PaperGraph AI helps researchers explore scientific papers from OpenAlex with an agentic AI
workflow. The app ingests paper metadata and abstracts, stores semantic content in Qdrant, stores
paper relationships in Neo4j, and lets an LLM agent combine vector retrieval with graph context.

The main goal is to answer research questions such as:

- Which papers discuss a specific topic?
- How do papers relate by topic, source, author, institution, or citation?
- What are the main research directions across a retrieved set of papers?

The system is built around an automated ingestion pipeline, an agentic retrieval layer, evaluation
scripts, feedback collection, and Grafana monitoring dashboards.

## 🔎 Retrieval Features

PaperGraph AI implements the bonus retrieval features explicitly:

- **Hybrid search**: the evaluated `vector_plus_graph` approach retrieves semantic matches from
  Qdrant first, then enriches selected OpenAlex papers with Neo4j graph context.
- **User query rewriting**: the agent has a `rewrite_search_query` tool that converts a natural
  language question into a compact retrieval query before database search.
- **Document re-ranking**: the agent has a `rerank_documents` tool that reorders retrieved
  candidates using question-term overlap plus the backend retrieval score.

The LLM evaluation compares `vector_only`, `graph_only`, and `vector_plus_graph`, while the
retrieval evaluation compares Qdrant vector search, Neo4j graph search, and the combined
vector-plus-graph strategy.

The research agent itself is implemented as an explicit LangGraph workflow:

```text
rewrite query -> retrieve documents -> rerank documents -> fetch graph context -> generate answer
```

This keeps tool usage predictable, prevents unnecessary repeated retrieval calls, and makes each
agent step visible in the streamed research events.

## 💬 UI Interface

![](./docs/ui_demo.gif)

* [UI papergraph-ai-ui-833591358031.europe-west1.run.app](https://papergraph-ai-ui-833591358031.europe-west1.run.app/)
  * ⚠️ The hosted deployment may be disabled or temporarily unavailable because it runs on learning/free-tier GCP resources.

The user interface is a Streamlit chat app.

It provides:

- A chat input for research questions.
- Real-time agent progress in the research section.
- Final answers generated from retrieved paper context.
- Feedback buttons for marking answers as useful or not useful.
- Backend streaming from the FastAPI API to the UI.

Local URLs:

- 🖥️ Streamlit UI: `http://localhost:8501`
- 🚀 FastAPI backend: `http://localhost:8000`
- 📊 Grafana dashboards: `http://localhost:3000`
- 📈 Prometheus: `http://localhost:9090`
- 🧠 Neo4j Browser: `http://localhost:7474`
- 🔎 Qdrant API: `http://localhost:6333`

GCP Grafana URL is exposed by Terraform:

```bash
cd infra/terraform
terraform output papergraph_grafana_url
```

The public GCP deployment is intended for demos and may be unavailable when free-tier quotas,
credits, or cost controls require the services to be stopped.

The Helm deployment uses the reserved `GRAFANA_LOAD_BALANCER_IP` GitHub Actions variable and exposes
Grafana as a Kubernetes `LoadBalancer` service.

Grafana dashboards are generated in CI and uploaded to a Terraform-managed GCS bucket:

```bash
cd infra/terraform
terraform output grafana_dashboards_bucket
```

The Grafana pod runs a dashboard sync container that copies JSON dashboards from:

```text
gs://<grafana_dashboards_bucket>/dashboards
```

into Grafana's provisioned dashboard directory.

## 📈 Diagram

flowchart LR
      User[Researcher] --> UI[Streamlit UI<br/>app/ui.py]

      UI -->|POST /agent/runs/stream<br/>SSE response| API[FastAPI App<br/>app/api/app.py + routes.py]
      UI -->|POST /feedback| API

      CLI[CLI Ingestion<br/>app/cli.py] --> PapersService
      API -->|/ingestions/openalex| Ingestion[OpenAlex Ingestion<br/>app/ingestion/openalex.py]
      API -->|/agent/runs<br/>/agent/runs/stream| AgentRunner[Research Agent Runner<br/>app/api/
      lifespan.py]
      API -->|/feedback| FeedbackRepo[Feedback Repository<br/>app/repositories/feedback.py]

      AgentRunner --> ResearchAgent[ResearchAgent<br/>app/agents/research.py]
      ResearchAgent --> ResearchGraph[LangGraph Workflow<br/>app/agents/research_graph.py]

      ResearchGraph --> Rewrite[Rewrite Query]
      Rewrite --> Retrieve[Retrieve Documents]
      Retrieve --> Rerank[Rerank Documents]
      Rerank --> GraphContext[Fetch Graph Context]
      GraphContext --> Answer[Generate Answer]

      ResearchGraph --> Tools[Research Tools<br/>app/agents/research_tools.py]
      Tools --> PapersService[Papers Service<br/>app/services/papers.py]
      Tools --> VectorRepo[Vector Repository<br/>app/repositories/vector.py]
      Tools --> GraphRepo[Graph Repository<br/>app/repositories/graph.py]

      Ingestion --> OpenAlexFetch[Fetch OpenAlex Records]
      Ingestion --> DLTStage[dlt Staging]
      Ingestion --> PapersService

      PapersService --> OpenAlexClient[OpenAlex Client<br/>app/clients/openalex.py]
      PapersService --> VectorRepo
      PapersService --> GraphRepo

      OpenAlexClient --> OpenAlex[(OpenAlex API)]
      OpenAlexFetch --> OpenAlex

      VectorRepo --> Qdrant[(Qdrant<br/>Paper vectors + payloads)]
      GraphRepo --> Neo4j[(Neo4j<br/>Paper graph)]
      FeedbackRepo --> Postgres[(PostgreSQL<br/>Agent runs + feedback)]

      Answer --> OpenAI[(OpenAI Chat Model)]

## 🎯 Service diagram

![](./docs/diagram.png)

## 🧱 Project structure

```
.                                             <- Project root
  ├── .github                                   <- GitHub automation configuration
  │   └── workflows                             <- CI, validation, and deployment workflows
  ├── .rtk                                      <- RTK local command/filter configuration
  ├── app                                       <- Main PaperGraph application package
  │   ├── agents                                <- LangGraph research agent and tools
  │   ├── api                                   <- FastAPI app, routes, request/response models
  │   ├── clients                               <- External API clients
  │   ├── dashboards                            <- Grafana dashboard generation code
  │   ├── db                                    <- Database connection and schema helpers
  │   ├── eval                                  <- Evaluation framework
  │   │   ├── llm                               <- LLM answer evaluation
  │   │   │   └── ground_truth                  <- Ground-truth dataset generation/evaluation
  │   │   └── retrieval                         <- Retrieval evaluation
  │   ├── ingestion                             <- OpenAlex ingestion pipeline
  │   ├── repositories                          <- Data-access layer for storage backends
  │   └── services                              <- Application service layer
  ├── docs                                      <- Project diagrams, images, and demo assets
  ├── infra                                     <- Deployment and infrastructure definitions
  │   ├── helm                                  <- Kubernetes Helm charts
  │   │   └── papergraph                        <- PaperGraph Helm chart
  │   │       └── templates                     <- Kubernetes manifest templates
  │   ├── monitoring                            <- Observability configuration
  │   │   ├── grafana                           <- Grafana dashboards and provisioning
  │   │   │   ├── dashboards                    <- Generated dashboard JSON
  │   │   │   ├── dashboards_src                <- Dashboard source definitions
  │   │   │   └── provisioning                  <- Grafana provisioning config
  │   │   │       ├── alerting                  <- Grafana alerting config
  │   │   │       ├── dashboards                <- Dashboard provider config
  │   │   │       ├── datasources               <- Datasource config
  │   │   │       └── plugins                   <- Grafana plugin provisioning
  │   │   ├── prometheus                        <- Prometheus scrape config
  │   │   └── tempo                             <- Tempo tracing config
  │   ├── scripts                               <- Infrastructure helper scripts
  │   └── terraform                             <- GCP infrastructure as code
  │       └── modules                           <- Reusable Terraform modules
  │           ├── artifact_registry             <- Container registry resources
  │           ├── cloud_sql                     <- PostgreSQL Cloud SQL resources
  │           ├── gcs_bucket                    <- Cloud Storage bucket resources
  │           ├── github_actions                <- GitHub Actions variables
  │           ├── github_oidc                   <- GitHub OIDC federation
  │           ├── gke                           <- GKE cluster resources
  │           ├── network                       <- VPC and private services networking
  │           ├── project_services              <- Required GCP API enablement
  │           ├── secret_manager                <- Secret Manager resources
  │           ├── static_ip                     <- Reserved external IP addresses
  │           └── workload_identity             <- GKE to GCP service account binding
  ├── migrations                                <- Alembic migration environment
  │   └── versions                              <- Versioned database/schema migrations
  └── tests                                     <- Automated test suite
      ├── agents                                <- Agent behavior tests
      ├── clients                               <- External client tests
      ├── dashboards                            <- Dashboard generation tests
      ├── db                                    <- Database integration tests
      ├── eval                                  <- Evaluation tests
      ├── ingestion                             <- Ingestion pipeline tests
      ├── repositories                          <- Repository layer tests
      └── services                              <- Service layer tests
```

## 🚀 How To Run The Project

Install dependencies:

```bash
uv sync
```

Start the infrastructure:

```bash
docker compose up -d
```

Run migrations:

```bash
uv run alembic upgrade heads
```

Ingest papers from OpenAlex with dlt:

```bash
uv run python -m app.ingestion.run "mathematics" --limit 10
```

## 📥 Ingestion Via dltHub

![](./docs/ingestion_demo.gif)

PaperGraph can run ingestion locally, but the deployed ingestion flow is controlled from dltHub.
The dltHub job does not ingest papers directly inside dltHub; it calls the deployed PaperGraph API
endpoint:

```text
POST /ingestions/openalex
```

The API then fetches articles from OpenAlex, stages compact records with dlt, embeds papers, writes
semantic data to Qdrant, and writes graph relationships to Neo4j.

The dltHub deployment entrypoint is:

```text
__deployment__.py -> app.ingestion.dlthub:ingest_openalex_from_dlthub
```

The deployed job is registered as the `papergraph_openalex_ingestion` dltHub pipeline. It stores one
`openalex_ingestion_runs` row per configured keyword, so dltHub's Pipelines page shows the
ingestion pipeline and its load history. The actual application writes still happen through the
PaperGraph API, which persists papers into Qdrant and Neo4j.

### Deploy And Run

Login locally once, connect the workspace, deploy the job, then trigger it:

```bash
uv run dlthub login
uv run dlthub workspace connect
make dlthub-deploy
uv run dlthub run ingest_openalex_from_dlthub -f
```

Use `make dlthub-deploy` instead of calling `uv run dlthub deploy` directly. The project contains
large folders that should not be uploaded to dltHub, such as infrastructure, local dashboards, and
demo assets. The Make target temporarily applies `.dlthubignore` patterns during deployment and
restores `.gitignore` afterwards.

Because this is a dltHub pipeline job, it can also be triggered by pipeline name:

```bash
make dlthub-run
```

Use `make dlthub-run` locally for the same reason: `dlthub pipeline run` syncs workspace files
before triggering the remote pipeline, so the temporary ignore workaround is needed there too.

### Configuration

Configure the deployed job in `.dlt/config.toml` under the job-specific section. TOML arrays are
supported, so multiple OpenAlex topics can be ingested in one run:

```toml
[jobs.dlthub.ingest_openalex_from_dlthub]
api_url = "http://<papergraph-api-ip>:8000"
ingestion_keywords = [
  "mathematics",
  "graph theory",
  "topological data analysis",
  "retrieval augmented generation",
  "knowledge graphs"
]
ingestion_limit = 10
ingestion_from_year = 2020
ingestion_dlt_output_dir = ".dlt/openalex"
```

Use `.dlt/secrets.toml` only for sensitive dltHub runtime values:

```toml
[jobs.dlthub.ingest_openalex_from_dlthub]
ingestion_api_token = "optional-token-for-the-api-ingestion-endpoint"
```

After changing `.dlt/config.toml` or `.dlt/secrets.toml`, sync the remote workspace configuration:

```bash
uv run dlthub workspace configuration sync
```

For CI deployment, put the dltHub runtime token in `.env` as `DLTHUB_AUTH_TOKEN`, then sync it to
Google Secret Manager:

```bash
make sync-gcp-secrets
```

Terraform creates the `DLTHUB_AUTH_TOKEN` Secret Manager container and the
`DLTHUB_AUTH_SECRET_NAME` GitHub Actions variable. The CI deploy job reads the secret and exports it
as `RUNTIME__AUTH_TOKEN` for `uv run dlthub deploy`.

Then run the remote job:

```bash
uv run dlthub run ingest_openalex_from_dlthub -f
```

Or run it by pipeline name:

```bash
make dlthub-run
```

The job returns a summary with `keyword_count`, `staged_records`, `inserted_articles`, and one API
response per configured keyword.

Start the backend locally:

```bash
make api
```

Start the UI locally:

```bash
make ui
```

Alternatively, the API and UI are also included in `docker-compose.yml`, so a full Docker run is:

```bash
docker compose up -d --build
```

Run checks:

```bash
make check
```

## ☁️ GCP Deployment

Deployment assets are split by responsibility:

- `infra/terraform/`: GCP infrastructure modules for GKE Autopilot, Cloud SQL PostgreSQL, Artifact
  Registry, networking, and Workload Identity.
- `infra/helm/`: Helm chart for the API, migrations, monitoring stack, Cloud Run UI manifest, and
  optional dev Qdrant/Neo4j StatefulSets.

Production config uses managed Qdrant Cloud and Neo4j AuraDB endpoints. Use their learning/free
tiers where possible and pass the endpoint values to Helm. GKE stays smaller because Qdrant and
Neo4j are not deployed as StatefulSets in the production values.

Create infrastructure:

```bash
cd infra/terraform
terraform init
terraform apply -var-file=terraform.tfvars
```

Deploy the app and monitoring:

```bash
helm upgrade --install papergraph-ai infra/helm/papergraph \
  --namespace papergraph-ai \
  --create-namespace
```

For a production-style deployment with public API and Grafana load balancers, pass:

```bash
helm upgrade --install papergraph-ai infra/helm/papergraph \
  --namespace papergraph-ai \
  --create-namespace \
  --set api.serviceType=LoadBalancer \
  --set-string api.loadBalancerIP="$(terraform -chdir=infra/terraform output -raw api_load_balancer_ip)" \
  --set monitoring.grafana.serviceType=LoadBalancer \
  --set-string monitoring.grafana.loadBalancerIP="$(terraform -chdir=infra/terraform output -raw grafana_load_balancer_ip)"
```

Container images are built by GitHub Actions and pushed to Artifact Registry. Terraform creates the
GitHub Actions variables and GCP Workload Identity Federation needed for the workflow, so no long
lived GCP JSON key is required.

## 📊 Dashboards

* [Grafana dashboards url](http://34.140.120.185:3000/dashboards/f/dft2wa0bwt98gf/?orgId=1)
  * ⚠️ Might be disabled

![](./docs/monitoring_1.png)

![](./docs/monitoring_2.png)

![](./docs/monitoring_3.png)

![](./docs/monitoring_4.png)

![](./docs/monitoring_5.png)

## 🔌 API Contracts

Base URL for local development: `http://localhost:8000`.

### `GET /health`

Checks whether the API process is running.

Response:

```json
{
  "status": "ok"
}
```

### `POST /agent/runs`

Runs the research agent and returns the complete answer after the run finishes.

Request:

```json
{
  "question": "Which papers discuss graph retrieval augmented generation?"
}
```

Response:

```json
{
  "run_id": "29611bb8-d0cd-4546-90e4-5cc39b405b58",
  "answer": "Summary...\n\nKey papers...",
  "events": [
    {
      "type": "run_start",
      "input": {
        "question": "Which papers discuss graph retrieval augmented generation?"
      }
    },
    {
      "type": "tool_start",
      "tool": "search_vector_database",
      "input": {
        "query": "graph retrieval augmented generation",
        "limit": 5
      }
    },
    {
      "type": "tool_end",
      "tool": "search_vector_database",
      "output": {
        "count": 5
      }
    },
    {
      "type": "run_end",
      "output": {
        "answer": "Summary...\n\nKey papers..."
      }
    }
  ]
}
```

### `POST /agent/runs/stream`

Runs the research agent and streams progress as Server-Sent Events. The request body is the same
as `POST /agent/runs`.

Request:

```json
{
  "question": "Which papers discuss graph retrieval augmented generation?"
}
```

Each streamed item is emitted as an SSE `data:` event containing JSON:

```text
data: {"type":"status","message":"Running agent"}

data: {"type":"agent_event","event":{"type":"tool_start","tool":"search_vector_database","input":{"query":"graph retrieval augmented generation","limit":5}}}

data: {"type":"done","run_id":"29611bb8-d0cd-4546-90e4-5cc39b405b58","answer":"Summary...\n\nKey papers...","events":[...]}
```

On failure the stream emits:

```text
data: {"type":"error","message":"Error message"}
```

### `POST /feedback`

Stores user feedback for a completed agent run.

Request:

```json
{
  "run_id": "29611bb8-d0cd-4546-90e4-5cc39b405b58",
  "rating": "thumbs_up",
  "comment": "Useful answer with relevant papers."
}
```

`rating` must be either `thumbs_up` or `thumbs_down`. `comment` is optional.

Response:

```json
{
  "status": "ok"
}
```

## 🧰 MCP Server

PaperGraph AI exposes a local MCP server so MCP-compatible clients can use the same paper search,
graph context, ingestion, and agent workflow as the API and UI.

Run it with stdio transport:

```bash
make mcp
```

Available MCP tools:

- `search_papers`: semantic search over stored Qdrant paper titles and abstracts.
- `search_paper_graph`: keyword search over stored Neo4j paper metadata and relationships.
- `get_paper_graph_context`: graph context lookup for OpenAlex paper IDs.
- `ingest_openalex_papers`: search OpenAlex and store results in Qdrant and Neo4j.
- `ask_papergraph`: run the full PaperGraph research agent and return the answer plus events.

When Logfire is enabled, MCP tool calls emit structured `mcp.*` spans with bounded query/question
attributes and result counts.

Suggested commit split for this MCP feature:

- `Add MCP SDK dependency`: `pyproject.toml`, `uv.lock`
- `Add PaperGraph MCP server`: `app/mcp.py`, `tests/test_mcp.py`
- `Document MCP server command`: `Makefile`, `README.md`

## 📡 Observability

Local observability uses Prometheus, Grafana, and Tempo from `docker-compose.yml`.

External observability can also be sent to Pydantic Logfire. Set the Logfire write token in `.env`:

```bash
LOGFIRE_ENABLED=true
LOGFIRE_API_KEY=your-logfire-write-token
```

`LOGFIRE_API_KEY` is used by the local and deployment configuration. The app also accepts
`LOGFIRE_TOKEN`.

When enabled, the app configures Logfire once in `app/tracing.py`, instruments FastAPI requests,
HTTPX calls, OpenAI SDK calls, and failed Pydantic validations, and forwards existing OpenTelemetry
spans to Logfire. If `OTEL_TRACING_ENABLED=true`, the same spans are also exported to the local
OTLP endpoint used by Tempo.

## LLM Evaluation

The project uses the course-style LLM evaluation flow:

1. Ingest papers into Qdrant and Neo4j.
2. Use the committed frozen ground-truth examples in `app/eval/llm/llm_dataset.json`.
3. Run the real PaperGraph agent for each evaluation question.
4. Use an LLM-as-a-judge to compare the generated agent answer with the ground-truth answer.
5. Use the same judge to evaluate the agent trajectory, meaning the tool calls made before the final answer.

The generated ground-truth dataset has this shape:

```json
{
  "question": "What does this paper say about graph retrieval?",
  "answer_orig": "Ground-truth answer generated from the source paper data.",
  "document": "https://openalex.org/W..."
}
```

`answer_orig` is the expected answer. `answer_agent` is produced later by running the actual app agent. The evaluator sends both answers, the original question, the source document ID, and the recorded tool calls to the judge.

### Compared Approaches

LLM evaluation compares three retrieval/tool-use variants:

- `vector_only`: the agent can only use Qdrant vector search.
- `graph_only`: the agent can only use Neo4j graph search and graph context.
- `vector_plus_graph`: the agent uses Qdrant vector search first, then Neo4j graph context for the returned OpenAlex IDs.

The evaluation summary reports `answer_good_rate` and `trajectory_good_rate` per approach. The best approach should be selected from the current evaluation output. At this stage, `vector_only` is the default baseline to beat, while `vector_plus_graph` is useful when the graph context improves the answer without adding unnecessary tool calls.

The frozen dataset intentionally mixes direct paper questions, semantic paraphrases, and cross-paper graph-context questions. This avoids evaluating only exact title or abstract keyword lookup. The graph-context questions ask the agent to compare papers by topic, application domain, and relationship-style context, which is where `vector_plus_graph` should have an advantage over pure vector search.

### Run Locally

Start databases and run migrations:

```bash
docker compose up -d qdrant neo4j postgres
uv run alembic upgrade heads
```

Ingest papers:

```bash
uv run python -m app.cli "knowledge graph based retrieval augmented generation" --limit 10
```

Run the cheap LLM smoke evaluation from the committed frozen dataset:

```bash
uv run python -m app.eval.llm.evaluate \
  --dataset app/eval/llm/llm_dataset.json \
  --output-format markdown \
  --limit 2 \
  --approaches vector_only vector_plus_graph
```

Run the full LLM evaluation locally when you need benchmark numbers:

```bash
uv run python -m app.eval.llm.evaluate \
  --dataset app/eval/llm/llm_dataset.json \
  --output-format markdown
```

Write Markdown and JSON artifacts from the same evaluator run:

```bash
uv run python -m app.eval.llm.evaluate \
  --dataset app/eval/llm/llm_dataset.json \
  --output-format markdown \
  --output-dir eval-results
```

To regenerate candidate ground-truth data locally, ingest the focused query first and then run:

```bash
uv run python -m app.eval.llm.ground_truth.evaluate \
  --source qdrant \
  --limit 10 \
  --questions-per-document 1 \
  --output app/eval/llm/generated_dataset.json
```

Generated datasets and evaluation outputs are ignored by Git. The committed LLM dataset is intentionally frozen so CI runs can be compared across builds. If a regenerated dataset is better, review it manually before replacing `app/eval/llm/llm_dataset.json`.

### CI

GitHub Actions runs an `llm-eval` job after tests. The job starts Qdrant and Neo4j, runs migrations, ingests a focused batch of Graph RAG papers, runs the LLM judge against the frozen dataset, writes the markdown summary to the Actions summary, and uploads JSON/markdown artifacts generated from the same evaluator run.

Push and pull-request builds run only the smoke LLM evaluation: two questions and the `vector_only` / `vector_plus_graph` approaches. Use the manual `workflow_dispatch` run with `llm_eval_mode=full` for the complete LLM benchmark.

The job is marked `continue-on-error` because it depends on external services and API keys. This keeps normal CI useful while still producing evaluation artifacts when the environment is available.

### Cloud Metrics

The deployed Helm chart also creates a Kubernetes `CronJob` named `papergraph-ai-llm-eval`.
It runs the same evaluator inside GKE, where it can push metrics to the in-cluster Prometheus
Pushgateway:

```bash
kubectl create job papergraph-ai-llm-eval-manual \
  --namespace papergraph-ai \
  --from=cronjob/papergraph-ai-llm-eval
```

The deployment workflow triggers one evaluation Job after the Helm release is updated and waits for
it to finish. The scheduled job runs daily with the smoke settings from the Helm values file. Grafana
LLM evaluation panels are populated only after this Kubernetes job runs successfully and Prometheus
scrapes the Pushgateway.
