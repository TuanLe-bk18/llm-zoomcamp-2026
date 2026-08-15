# Cloud Services Comparison Assistant

<p align="center">
  <img src="images/cover.jpg" alt="Cloud Services Comparison Assistant cover">
</p>

A RAG-powered conversational assistant that helps multi-cloud engineers discover Google Cloud products and map them to equivalent AWS and Azure offerings.

Staying current across three major cloud vendors is hard—especially when you know one platform well and need the closest counterpart on another. This assistant uses a curated comparison dataset, hybrid retrieval, and an LLM to answer questions like *“What is the AWS equivalent of Cloud Composer?”* or *“Which GCP service should I use for serverless workflow orchestration?”*

Built as the capstone for [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) (DataTalks.Club).

---

## Table of contents

- [Problem statement](#problem-statement)
- [Project overview](#project-overview)
- [Solution architecture](#solution-architecture)
- [RAG pipeline](#rag-pipeline)
- [Dataset](#dataset)
- [Technologies](#technologies)
- [Repository structure](#repository-structure)
- [Running the application](#running-the-application)
- [Using the application](#using-the-application)
- [Experiments & evaluation](#experiments--evaluation)
- [Monitoring](#monitoring)
- [Acknowledgements](#acknowledgements)

---

## Problem statement

Cloud engineers often need to:

1. **Select the right Google Cloud product** for a workload (compute, data, security, serverless, etc.).
2. **Find vendor alternatives** on AWS and Azure when migrating or designing multi-cloud architectures.
3. **Land on official documentation** quickly instead of browsing marketing pages and comparison blogs.

Manual research is slow and inconsistent. This project turns a structured GCP-centric comparison table into a searchable knowledge base with a chat interface, relevance evaluation, and production-style deployment on AWS EKS.

---

## Project overview

The **Cloud Services Comparison Assistant** is an end-to-end Retrieval-Augmented Generation (RAG) system with:

| Capability | Description |
|---|---|
| **GCP service discovery** | Recommend Google Cloud products by category, type, or natural-language intent |
| **Cross-cloud mapping** | Return AWS and Azure equivalents alongside the GCP product |
| **Documentation links** | Surface official Google Cloud (and related) documentation URLs from the corpus |
| **Conversational UI** | Streamlit chat app with model and retrieval-engine selection |
| **Quality feedback loop** | LLM-as-a-Judge relevance scoring + user ±1 feedback stored in PostgreSQL |
| **GitOps on Kubernetes** | Argo CD deploys Elasticsearch, Streamlit, Grafana, and support manifests |
| **Observability** | Grafana dashboards for cost, tokens, latency, relevance, and feedback |

### Main use cases

1. **Google Cloud service selection** — Ask in plain language; get the matching product and description.
2. **Vendor alternatives** — Given a GCP service (or a need), get AWS and Azure counterparts.
3. **Documentation pointers** — Follow links from the retrieved records.
4. **Comparative Q&A** — Multi-turn style questions answered from retrieved context only (prompt constrains the LLM to the corpus).

---

## Solution architecture

Infrastructure is provisioned with **Terraform** on **AWS** (region `eu-central-1`) and workloads run on **Amazon EKS** with **Argo CD** GitOps.

### Cloud resources

<p align="center">
  <img src="images/cloud_architecture.png" alt="AWS cloud architecture diagram">
</p>

> Also available under [`docs/cloud_architecture.png`](docs/cloud_architecture.png).

**Networking**

| Resource | Details |
|---|---|
| VPC | `10.0.0.0/16` (`aws_vpc.eks`) |
| Private subnets | `10.0.0.0/20` (eu-central-1a), `10.0.16.0/20` (eu-central-1b) |
| Public subnets | `10.0.32.0/20` (eu-central-1a), `10.0.48.0/20` (eu-central-1b) |
| Internet Gateway | Public egress / ingress path |
| NAT Gateway + EIP | Private-subnet egress |
| Route tables & NACLs | Separate public / private associations |
| Security groups | Public and private SGs for cluster and RDS access |

**Compute & container platform**

| Resource | Details |
|---|---|
| EKS cluster | Kubernetes **1.31**, private subnet placement, public + private API endpoint |
| Node group | On-demand **t3.2xlarge**, desired 2 / min 1 / max 2 |
| Add-ons | `vpc-cni`, `coredns`, `kube-proxy`, `eks-pod-identity-agent`, `aws-ebs-csi-driver` |
| IAM | Cluster role + node role with EKS, CNI, ECR, EBS CSI, EFS policies |
| ECR | `streamlit` repository; Terraform builds and pushes the app image |

**Data & secrets**

| Resource | Details |
|---|---|
| RDS PostgreSQL 16 | Instance `llm-eks` (`db.t3.small`) — conversations, feedback, Grafana backend |
| AWS Secrets Manager | Credentials synced into the cluster via External Secrets Operator |
| Terraform backend | S3 remote state |

### Kubernetes resources & workflow

<p align="center">
  <img src="images/kubernetes_workflow.png" alt="Kubernetes workloads and RAG workflow diagram">
</p>

> Also available under [`docs/kubernetes_workflow.png`](docs/kubernetes_workflow.png).

**Namespaces**

- `argocd` — Argo CD and related GitOps controllers  
- `llm` — Application workloads (Streamlit, Elasticsearch/Kibana, Grafana, support)

**Argo CD applications** (project `llm-project`)

| Application | Path / role |
|---|---|
| `support.yaml` | Storage class, shared secrets, cluster helpers |
| `elastic_search.yaml` | Elasticsearch master / data / client Helm releases + Kibana |
| `streamlit.yaml` | Streamlit Deployment + Service (LoadBalancer) |
| `grafana.yaml` | Grafana Deployment, Service, PVC, ConfigMap |

**In-cluster stack**

```
Users ──HTTPS──► LoadBalancer Services
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Streamlit    Grafana     Kibana
          │           │
          │           └──► RDS PostgreSQL
          │
          ├──► Elasticsearch (hybrid kNN + BM25 + RRF)
          ├──► OpenAI API (answer + relevance judge)
          └──► RDS PostgreSQL (conversations / feedback)
```

Secrets (OpenAI key, DB, Elasticsearch credentials) are injected via **External Secrets** from AWS Secrets Manager rather than being committed to Git.



---

## RAG pipeline

End-to-end flow implemented in `infrastructure/streamlit/app/`:

1. **User question** enters the Streamlit UI (`app.py`).
2. **Retrieval** (user-selectable):
   - **Minsearch** — in-process full-text search with tuned field boosts.
   - **Elasticsearch** — hybrid retrieval:
     - dense kNN over `General_Vector` embeddings (`SentenceTransformer`)
     - keyword `multi_match` over product fields
     - **Reciprocal Rank Fusion (RRF)** to merge and re-rank top documents
3. **Prompt construction** — retrieved GCP / AWS / Azure fields are formatted into context (`template.py`).
4. **Generation** — OpenAI chat completion (`gpt-3.5-turbo`, `gpt-4o`, or `gpt-4o-mini`).
5. **Evaluation** — a second LLM call (LLM-as-a-Judge) classifies the answer as `RELEVANT`, `PARTLY_RELEVANT`, or `NON_RELEVANT`.
6. **Persistence** — answer metadata (tokens, cost, latency, relevance) and optional ±1 feedback are written to PostgreSQL for Grafana.

The system prompt instructs the model to answer **only from retrieved context**, reducing hallucination relative to open-ended chat.

---

## Dataset

Source file: [`data/raw_data.csv`](data/raw_data.csv) (~**222** records), curated from Google Cloud documentation-oriented comparison material.

| Column | Meaning |
|---|---|
| `Service_Category` | High-level domain (e.g. Compute, Data analytics, Security & identity) |
| `Service_Type` | Finer capability (e.g. Workload orchestration, Zero trust) |
| `Link_to_Documentation` | Official documentation URL |
| `Google_Cloud_Product` | GCP product name (reference product) |
| `Google_Cloud_Product_Description` | Short product description |
| `AWS_Offering` | Closest AWS counterpart (when available) |
| `Azure_Offering` | Closest Azure counterpart (when available) |

Supporting artifacts:

- `data/documents_id.json` — indexed document IDs  
- `data/ground-truth-data.csv` — retrieval evaluation ground truth  
- `data/rag-eval-gpt-4o-mini.csv` — RAG judge evaluation sample  
- Notebooks under `data_preparation/` clean, embed, and load vectors into Elasticsearch  

---

## Technologies

![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elastic_Search-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)
[![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?logo=amazon-web-services&logoColor=white)](#)
[![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?logo=postgresql&logoColor=white)](#)
[![Helm](https://img.shields.io/badge/Helm-0F1689?logo=helm&logoColor=fff)](#)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=fff)](#)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

| Layer | Tools |
|---|---|
| Language / runtime | Python 3.12 |
| Containerization | Docker |
| Orchestration | Kubernetes (Amazon EKS 1.31) |
| Cloud | AWS — VPC, EKS, ECR, RDS, Secrets Manager, IAM |
| IaC | Terraform |
| GitOps / deploy | Argo CD, Helm, External Secrets Operator |
| Retrieval | [Minsearch](https://github.com/alexeygrigorev/minsearch), Elasticsearch (hybrid + RRF) |
| Embeddings | Sentence Transformers |
| LLM | OpenAI (`gpt-3.5-turbo`, `gpt-4o`, `gpt-4o-mini`) |
| UI | Streamlit |
| App / metrics DB | Amazon RDS PostgreSQL 16 |
| Monitoring | Grafana (+ Kibana for Elasticsearch) |

---

## Repository structure

```
├── README.md
├── argocd/                          # Argo CD projects, apps, Helm values, External Secrets
├── data/                            # Raw corpus, ground truth, eval exports
├── data_preparation/                # Ingest + ground-truth notebooks
├── docs/                            # Architecture diagrams (PNG)
├── images/                          # Screenshots + architecture images
├── infrastructure/
│   ├── kubernetes/manifests/          # Streamlit, Grafana, Elasticsearch, helpers
│   ├── streamlit/                   # App code, Dockerfile, requirements
│   └── terraform/                   # VPC, EKS, ECR, RDS, IAM
├── rag_evaluation/                  # RAG LLM-as-Judge notebook
├── script/                          # Deploy, Helm, namespace, Secrets Manager helpers
├── text_retrieval_evaluation/       # Minsearch / ES keyword eval
├── vector_retrieval_evaluation/     # Embedding, hybrid, reranking eval
├── infra_up.sh / infra_down.sh
└── instruction.sh
```

---

## Running the application

### Prerequisites

- Python 3.12+, Docker, Terraform, `kubectl`, Helm, AWS CLI  
- An AWS account with permissions for VPC, EKS, ECR, RDS, and Secrets Manager  

### 1. Local Python environment

```bash
python3 -m venv llm_project_env
source llm_project_env/bin/activate
pip install -r infrastructure/streamlit/requirements.txt
```

### 2. Terraform backend (S3)

```bash
aws s3api create-bucket \
  --bucket llm-terraform-backend \
  --region eu-central-1 \
  --create-bucket-configuration LocationConstraint=eu-central-1
```

Configure `infrastructure/terraform/backend.config` and variables, then:

```bash
sh infra_up.sh
```

This provisions the VPC, EKS cluster, node group, add-ons, ECR image push, and RDS instance.

### 3. Cluster access & namespaces

```bash
bash script/secret_manager.sh

kubectl create namespace argocd
kubectl create namespace llm
```

### 4. External Secrets

```bash
helm repo add external-secrets https://charts.external-secrets.io

helm upgrade --install external-secrets external-secrets/external-secrets \
  -f argocd/deployment_manifests/helm_values/secret_values.yaml

kubectl apply -f argocd/deployment_manifests/secret/service_account.yaml
kubectl apply -f argocd/deployment_manifests/secret/secret-store.yml
kubectl apply -f argocd/deployment_manifests/secret/argocd-aws-secret.yaml
```

### 5. Argo CD

```bash
helm repo add argo https://argoproj.github.io/argo-helm

helm upgrade --install argocd argo/argo-cd --version 7.5.2 \
  -f argocd/deployment_manifests/helm_values/values.yaml --debug

kubectl apply -f argocd/project_manifests/llm-project.yaml
```

### 6. Applications

```bash
kubectl apply -f argocd/application_manifests/support.yaml
kubectl apply -f argocd/application_manifests/elastic_search.yaml
kubectl apply -f argocd/application_manifests/streamlit.yaml
kubectl apply -f argocd/application_manifests/grafana.yaml
```

<p align="center">
  <img src="images/argocd.png" alt="Argo CD applications">
</p>

### 7. Index preparation

Create `infrastructure/streamlit/app/.env` with:

```bash
POSTGRES_HOST=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_PORT=

ELASTIC_URL=
INDEX_NAME=
ELASTIC_USERNAME=
ELASTIC_PASSWORD=
MODEL_NAME=
OPENAI_KEY=
```

Then load / prepare the index:

```bash
python3 infrastructure/streamlit/app/prep.py
```

<p align="center">
  <img src="images/kibana.png" alt="Kibana / Elasticsearch">
</p>

---

## Using the application

1. Open the Streamlit LoadBalancer URL (port **8501**).
2. Choose an OpenAI model and a search engine (`minisearch` or `elastic_search`).
3. Ask a multi-cloud question, for example:
   - *“What AWS service is equivalent to Cloud Composer?”*
   - *“I need serverless workflow orchestration on Google Cloud.”*
4. Review the answer, relevance label, token usage, and estimated cost.
5. Submit **+1 / −1** feedback to improve monitoring insights.

<p align="center">
  <img src="images/streamlit.png" alt="Streamlit UI">
</p>

---

## Experiments & evaluation

Notebooks:

| Notebook | Purpose |
|---|---|
| [`data_preparation/load_vector_database.ipynb`](data_preparation/load_vector_database.ipynb) | Clean, embed, and load documents into Elasticsearch |
| [`data_preparation/groud_truth_preparation.ipynb`](data_preparation/groud_truth_preparation.ipynb) | Generate ground-truth pairs for retrieval / RAG eval |
| [`text_retrieval_evaluation/text_eval.ipynb`](text_retrieval_evaluation/text_eval.ipynb) | Keyword / text retrieval evaluation |
| [`vector_retrieval_evaluation/vector_eval.ipynb`](vector_retrieval_evaluation/vector_eval.ipynb) | Dense vector retrieval evaluation |
| [`vector_retrieval_evaluation/hybird_search_reranking.ipynb`](vector_retrieval_evaluation/hybird_search_reranking.ipynb) | Hybrid search + RRF reranking |
| [`rag_evaluation/rag_eval.ipynb`](rag_evaluation/rag_eval.ipynb) | End-to-end RAG quality (LLM-as-a-Judge) |

### Text retrieval

**Minsearch** (no boosting): Hit rate **89%**, MRR **75%**  
**Minsearch** (tuned boosting): Hit rate **92%**, MRR **81%**

Best boosts:

```python
best_boost = {
  'Service_Category': 0.10638495651755087,
  'Service_Type': 1.269946147222612,
  'Link_to_Documentation': 1.5531045466189122,
  'Google_Cloud_Product': 1.3250028735372683,
  'Google_Cloud_Product_Description': 1.9395345731534959,
  'AWS_Offering': 2.067143729150134,
  'Azure_Offering': 0.799844469488588,
}
```

**Elasticsearch** keyword (no boosting): Hit rate **86%**, MRR **75%**

### Vector retrieval

| Approach | Hit rate | MRR |
|---|---|---|
| Description-only embeddings | 54% | 40% |
| All fields concatenated + embedded | 90% | 78% |
| Hybrid search + RRF reranking | **95%** | **84%** |

### RAG flow (LLM-as-a-Judge)

For `gpt-4o-mini` on a **200**-record sample:

| Label | Count | Share |
|---|---|---|
| `RELEVANT` | 167 | ~84%* |
| `PARTLY_RELEVANT` | 30 | ~15% |
| `NON_RELEVANT` | 3 | ~1% |

\*Percentages recalculated from counts (167 + 30 + 3 = 200). Older README figures listed inconsistent percentages.

---

## Monitoring

Grafana is exposed at `http://<LOADBALANCER_URL>:3000`.

<p align="center">
  <img src="images/grafana.png" alt="Grafana monitoring dashboard">
</p>

Dashboard panels:

1. **+1 / −1 (pie)** — user feedback distribution  
2. **Relevancy (gauge)** — LLM-as-a-Judge relevance levels  
3. **OpenAI cost (time series)** — estimated spend over time  
4. **Tokens (time series)** — prompt / completion volume  
5. **Model used (bar)** — conversations per model  
6. **Response time (time series)** — end-to-end latency  

Conversation and feedback rows are stored in **RDS PostgreSQL**, which both the Streamlit app and Grafana use as a backend.

---

## Acknowledgements

Thanks to everyone who made LLM Zoomcamp such a strong foundation for RAG and LLM engineering—especially [Alexey Grigorev](https://www.linkedin.com/in/agrigorev/).
