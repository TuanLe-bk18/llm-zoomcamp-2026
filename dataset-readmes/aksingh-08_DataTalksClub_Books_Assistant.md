# DataTalksClub_Books_Assistant


<p align='center'>

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![RAG](https://img.shields.io/badge/RAG-Application-success?style=for-the-badge)
![Groq](https://img.shields.io/badge/LLM-Groq-orange?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?style=for-the-badge&logo=streamlit)
![Sentence Transformers](https://img.shields.io/badge/Embeddings-SentenceTransformers-green?style=for-the-badge)
![DuckDB](https://img.shields.io/badge/Database-DuckDB-yellow?style=for-the-badge)
![DLT](https://img.shields.io/badge/Ingestion-dlt-purple?style=for-the-badge)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
<!--![Render](https://img.shields.io/badge/Deployment-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)-->

</p>

---

[streamlit-main-2026-07-31-15-05-13.webm](https://github.com/user-attachments/assets/847c4dc3-632a-45eb-82bc-f123ef3ed3a1)

---

<!--## Live Demo

Try the application without any installation:

https://datatalksclub-books-assistant.onrender.com

Exmample Questions:
- What is Data Engineering?
- Recommend books for learning MLOps.
- Compare Machine Learning books.
- Which books explain Feature Engineering?

----->

# Project Overview

**DataTalksClub Books Assistant** is an end-to-end Retrieval-Augmented Generation (RAG) application that enables users to explore and ask natural language questions about books featured in the **DataTalksClub Book of the Week Archive**.

Instead of relying solely on an LLM's internal knowledge, the assistant retrieves relevant information from a curated knowledge base containing book metadata, descriptions, discussion threads, and community replies before generating an answer. This approach significantly improves factual accuracy while reducing hallucinations.

The project was developed as the capstone project for **LLM Zoomcamp 2026** and combines concepts learned throughout the course into a single production-style application.

The application demonstrates the complete lifecycle of a modern RAG system, including:

- Data ingestion
- Document preprocessing
- Multiple retrieval techniques
- Prompt engineering
- LLM integration
- Response evaluation
- Monitoring
- Analytics dashboard
- User feedback collection

Unlike many RAG demonstrations that focus only on retrieval and generation, this project also includes evaluation, monitoring, logging, and analytics to simulate how real-world LLM applications are built and maintained.

---

# Motivation

Large Language Models are excellent at generating fluent responses, but they often struggle when answering questions about information they were never trained on or about domain-specific content.

The DataTalksClub Book Archive contains valuable information including:

- Book descriptions
- Learning resources
- Community discussions
- Questions from readers
- Expert replies

Unfortunately, browsing this information manually becomes increasingly difficult as the archive grows.

Traditional keyword search has several limitations:

- It requires users to know the exact terminology.
- Similar concepts expressed differently are often missed.
- Answers are spread across multiple discussion threads.
- It cannot summarize information from several documents.

This project addresses these limitations by combining semantic retrieval with Large Language Models, allowing users to ask questions naturally, such as:

> *"Which books should I read to become a Machine Learning Engineer?"*

or

> *"Compare books related to MLOps and Data Engineering."*

The assistant retrieves the most relevant documents and uses them as context to generate grounded, context-aware answers.

---

# Features

## Retrieval-Augmented Generation (RAG)

- Context-aware question answering
- Hallucination reduction using retrieved documents
- Source attribution
- Multi-document context generation

---

## Multiple Retrieval Strategies

The application implements three different retrieval techniques:

### Text Search

Traditional keyword-based retrieval using **MinSearch**.

Useful for:

- Exact phrase matching
- Specific terminology
- Book titles
- Named entities

---

### TF-IDF Retrieval

Statistical retrieval using **TF-IDF Vectorization**.

Useful for:

- Sparse textual matching
- Term importance
- Fast document ranking

---

### Semantic Search

Embedding-based retrieval using **Sentence Transformers**.

Useful for:

- Semantic similarity
- Synonyms
- Concept matching
- Natural language search

Semantic Search is used as the default retrieval strategy because it consistently produces the highest-quality results during evaluation.

---

## LLM-powered Answer Generation

The retrieved documents are injected into a carefully designed prompt before being sent to the LLM.

The assistant is instructed to:

- answer only from retrieved context
- avoid hallucinations
- remain concise
- cite the books used
- admit when information is unavailable

---

## Evaluation

The project includes an evaluation framework for measuring retrieval quality.

It supports:

- Retrieval metrics
- Ground-truth dataset evaluation
- LLM-as-a-Judge evaluation
- Automated evaluation reports

---

## Monitoring

The application logs every conversation, including:

- User question
- Generated answer
- Response time
- Retrieval strategy
- Model used
- Token usage

These logs are stored for further analysis and dashboard visualization.

---

## Analytics Dashboard

The project contains dashboards for visualizing:

- Total conversations
- Model usage
- Token consumption
- Response latency
- User feedback
- Evaluation metrics

---

## Feedback Collection

Users can rate responses directly from the interface.

Collected feedback helps identify:

- Poor retrieval cases
- Hallucinated responses
- Low-quality answers
- Opportunities for improving prompts and retrieval strategies.

---

# Technology Stack

| Component | Technology |
|------------|------------|
| Programming Language | Python |
| LLM | Groq (Llama 3.3 70B) |
| Retrieval | Semantic Search, TF-IDF, Text Search |
| Embeddings | Sentence Transformers |
| Data Ingestion | dlt |
| Database | DuckDB |
| Frontend | Streamlit |
| Monitoring | SQLite |
| Evaluation | Custom Metrics + LLM Judge |
| Dashboard | Streamlit |
| Package Management | uv |
<!--| Deployment | Render |-->

---

# Highlights

✔ End-to-End RAG Application

✔ Modular Architecture

✔ Three Retrieval Strategies

✔ Semantic Search

✔ Prompt Engineering

✔ Evaluation Pipeline

✔ Monitoring Dashboard

✔ Analytics Dashboard

✔ User Feedback Collection

✔ Easily Extensible Architecture

---

# Project Journey

This project is the culmination of everything I learned during **LLM Zoomcamp 2026**.

Throughout the course, I built several small applications while learning different concepts, including:

- Prompt Engineering
- Vector Search
- Retrieval-Augmented Generation (RAG)
- Evaluation
- Monitoring
- LLM APIs
- OpenTelemetry
- Dashboards
- Agentic Workflows

Each module introduced an individual concept, but none of them demonstrated how all of these components fit together in a production-style application.

The goal of this project was therefore much larger than simply building another chatbot.

Instead, I wanted to build a complete end-to-end RAG system that combines all major concepts from the course into a single application.

Rather than treating retrieval, evaluation, monitoring, and deployment as separate topics, I wanted them to work together as parts of one cohesive system.

The final result is **DataTalksClub Books Assistant**, a Retrieval-Augmented Generation application that allows users to search, explore, and ask natural language questions about books from the DataTalksClub Book of the Week Archive.

---

# Problem Statement

The DataTalksClub Book of the Week Archive contains dozens of carefully selected books covering topics such as:

- Machine Learning
- Data Engineering
- MLOps
- Python
- SQL
- Statistics
- Software Engineering
- Large Language Models

Every book includes valuable information such as:

- Metadata
- Description
- Discussion threads
- Community questions
- Replies
- Recommendations

As the archive grows, manually finding relevant information becomes increasingly difficult.

Suppose a learner wants to know:

> Which books should I read to become a Machine Learning Engineer?

The answer may require combining information from several books.

Another user may ask:

> Which books discuss feature engineering?

while another asks:

> Recommend books that explain ML deployment.

Traditional keyword search struggles with these kinds of questions because:

- Users may not know the exact wording used in documents.
- Similar concepts may be expressed using different terminology.
- Information may be distributed across multiple discussion threads.
- Search engines cannot generate summaries across documents.

Large Language Models can summarize information effectively, but they also introduce another challenge:

**Hallucination.**

Without access to the underlying archive, an LLM may generate inaccurate or unsupported answers.

This project combines document retrieval with LLM generation to ensure that responses are grounded in actual documents from the archive.

---

# Project Objective

The primary objective was not simply to build a chatbot.

Instead, the project aimed to answer the following engineering questions:

- How can a complete RAG application be built from scratch?
- How should data be ingested and prepared?
- Which retrieval strategy performs best?
- How can retrieval quality be evaluated?
- How should conversations be monitored?
- How can user feedback be collected?
- How should such a system be organized for maintainability?

By answering these questions, the project demonstrates the complete lifecycle of a Retrieval-Augmented Generation application.

---

# Why This Dataset?

Choosing the right dataset was one of the most important design decisions.

Several datasets were considered before selecting the DataTalksClub Book Archive.

The dataset ultimately stood out for several reasons.

## 1. Educational Domain

Unlike generic datasets, every document focuses on technical learning.

Topics include:

- Machine Learning
- Data Engineering
- LLMs
- Python
- Statistics
- MLOps
- System Design

This makes the archive ideal for building an educational assistant.

---

## 2. Rich Document Structure

Each book contains significantly more than a title and description.

The archive also includes:

- descriptions
- discussion threads
- community questions
- replies from readers
- recommendations

This richer structure allows retrieval to capture both official information and community knowledge.

---

## 3. Real Retrieval Challenges

Unlike benchmark datasets, this archive contains:

- overlapping concepts
- repeated terminology
- related books
- similar questions
- multiple discussions

These characteristics make retrieval more realistic and provide a better opportunity to compare different retrieval methods.

---

## 4. Suitable Size

Another practical reason for selecting this dataset was its size.

During development, multiple retrieval experiments, prompt iterations, and evaluation runs had to be performed.

A moderately sized dataset allowed experimentation without excessive computation while still being large enough to meaningfully compare retrieval strategies.

---

# Design Philosophy

Several principles guided the implementation of this project.

## Build modular components

Instead of writing one large script, every major responsibility was isolated into its own module.

Examples include:

- ingestion
- preprocessing
- retrieval
- prompting
- evaluation
- monitoring
- dashboards

This makes the project easier to maintain and extend.

---

## Make every component replaceable

Most components can be swapped without affecting the rest of the application.

For example:

- changing the retrieval strategy requires only a configuration change.
- replacing the LLM requires modifying a single module.
- adding another embedding model requires minimal code changes.

This flexibility was an intentional design goal.

---

## Prefer reproducibility

Generated artifacts such as embeddings and databases are not treated as source code.

Instead, the repository contains scripts that regenerate these resources from the original data.

This keeps the repository lightweight and ensures that anyone can reproduce the complete pipeline from scratch.

---

## Keep production practices in mind

Although this is an educational project, several production-inspired practices were adopted.

These include:

- modular architecture
- logging
- monitoring
- evaluation
- analytics
- configuration management
- reusable components
- separation of concerns

The objective was not only to answer questions about books but also to demonstrate how modern LLM applications are engineered.

# Dataset

A Retrieval-Augmented Generation (RAG) system is only as good as the knowledge it retrieves. Instead of relying on a synthetic benchmark dataset, this project uses the **DataTalksClub Book of the Week Archive** as its primary knowledge source.

The archive contains a curated collection of books covering modern topics in Artificial Intelligence, Data Engineering, Machine Learning, MLOps, Python, Statistics, SQL, and Software Engineering. Each book entry includes not only metadata but also valuable community discussions where readers ask questions, share insights, and recommend learning resources.

Unlike a traditional search engine that indexes plain documents, this project transforms multiple types of information into retrieval-ready documents that can be searched efficiently by different retrieval algorithms.

The dataset therefore represents both structured and unstructured information, making it well suited for building an educational RAG assistant.

---

# Dataset Structure

Each book is represented using multiple pieces of information.

## Book Metadata

Every book contains metadata such as:

- Book ID
- Title
- Description
- Original Markdown file
- Book Content

Example:

```
Book:
Machine Learning Bookcamp

Description:
A practical introduction to Machine Learning using Python.

Content:
...
```

---

## Community Discussions

One of the most valuable parts of the archive is the discussion section.

Readers ask questions related to:

- prerequisites
- learning paths
- implementation details
- recommendations
- career advice

Example:

```
Question:

How should I start learning Machine Learning?

Replies:

Read Chapter 2 first.

Focus on supervised learning before neural networks.

Practice with small projects.
```

These discussions significantly increase the amount of searchable knowledge available to the RAG pipeline.

---

# Why Discussions Were Included

Initially, only book descriptions were considered for indexing.

However, after experimenting with retrieval quality, it became clear that many user questions were actually answered inside discussion threads rather than the book descriptions themselves.

For example:

User Question

> Can I read this book as a beginner?

The answer usually exists inside community replies instead of the official description.

Including discussions therefore improved retrieval quality while also making generated responses much more useful.

---

# Data Ingestion Pipeline

Instead of writing a custom parser for every Markdown file, this project uses **DLT (Data Load Tool)** to build a reproducible ingestion pipeline.

The ingestion process follows the ELT (Extract → Load → Transform) approach.

```
Markdown Files
        │
        ▼
Frontmatter Parsing
        │
        ▼
DLT Resources
        │
        ▼
DuckDB
```

Using DLT provides several advantages:

- repeatable ingestion
- schema management
- automatic table creation
- simplified loading
- reproducible pipelines

This also makes it easier to replace DuckDB with another destination database in the future if required.

---

# Why DuckDB?

Several storage options were considered during development.

## SQLite

Advantages

- lightweight
- simple

Limitations

- less suitable for analytical workloads
- weaker support for columnar processing

---

## PostgreSQL

Advantages

- production ready
- scalable

Limitations

- requires additional setup
- unnecessary complexity for this project

---

## Vector Databases

Examples:

- Qdrant
- Chroma
- Pinecone

Advantages

- optimized vector retrieval

Limitations

- an additional service to manage
- unnecessary for a relatively small dataset
- retrieval experiments could be implemented locally

---

## DuckDB (Chosen)

DuckDB was selected because it provides an excellent balance between simplicity and analytical performance.

Advantages include:

- zero server configuration
- extremely fast analytical queries
- SQL support
- local database
- lightweight
- easy integration with DLT

Since this project focuses on demonstrating the complete RAG lifecycle rather than distributed infrastructure, DuckDB was an ideal choice.

---

# Document Processing

The ingested data cannot be indexed directly.

Instead, a preprocessing step converts relational data into retrieval documents.

The processing pipeline combines multiple sources of information into a single searchable representation.

For every book, the following fields are combined:

- title
- description
- content

For every discussion, the following fields are combined:

- question
- replies
- associated book

The final document contains a single field called **search_text**, which becomes the searchable representation used by every retrieval strategy.

Example:

```
Book:
Designing Machine Learning Systems

Question:
How should I deploy ML models?

Replies:
...
```

This approach keeps retrieval independent of the original database schema.

---

# Why Create Retrieval Documents?

One design decision was to separate the storage schema from the retrieval schema.

The database is optimized for storing normalized data.

Retrieval, however, works better when every searchable unit already contains all relevant information.

Instead of performing multiple joins during every search request, preprocessing creates retrieval-ready documents once.

Benefits include:

- simpler retrieval
- faster searches
- cleaner code
- interchangeable retrievers
- reusable document collection

This preprocessing step also makes it possible to switch between Text Search, TF-IDF, and Semantic Search without changing the document format.

---

# Engineering Decisions

Several implementation decisions were made during this stage.

## Decision 1 — Separate ingestion from retrieval

The ingestion pipeline is responsible only for loading data.

Retrieval-specific logic is handled later during preprocessing.

This separation keeps responsibilities clear.

---

## Decision 2 — Generate documents offline

Retrieval documents are generated before the application starts.

Advantages:

- lower latency
- faster retrieval
- simpler runtime pipeline

---

## Decision 3 — Do not commit generated data

Generated artifacts such as:

- DuckDB databases
- processed retrieval documents
- embeddings

are intentionally excluded from version control.

Instead, scripts are provided to regenerate them.

This keeps the repository lightweight while ensuring that every result can be reproduced.

---

# Challenges Encountered

Building the ingestion pipeline involved several practical challenges.

### Parsing Markdown

Books contain frontmatter along with Markdown content.

The parser had to correctly separate metadata from the document body before ingestion.

---

### Nested Discussions

Discussion threads include nested replies.

These replies needed to be grouped correctly so that each retrieval document preserved the original conversation context.

---

### Multiple Document Types

Books and discussions have different structures.

Instead of forcing them into a single relational schema, preprocessing converts both into a unified retrieval document format.

This allows every retrieval strategy to operate on a consistent document structure.

---

# Output of the Processing Stage

After preprocessing, the application produces a collection of retrieval documents.

Each document contains information such as:

- document type
- document ID
- book ID
- title
- search text
- metadata

These retrieval documents become the input for every retrieval strategy implemented in the next stage of the pipeline.

# System Architecture

The DataTalksClub Books Assistant follows a modular architecture where each component is responsible for a single task. Instead of tightly coupling retrieval, prompting, and generation into one script, the project separates these responsibilities into independent modules.

This modular design makes the application easier to understand, maintain, test, and extend.

At a high level, the application follows the architecture shown below.

```
                           ┌────────────────────────────┐
                           │      Markdown Books        │
                           └──────────────┬─────────────┘
                                          │
                                          ▼
                           ┌────────────────────────────┐
                           │      DLT Ingestion         │
                           └──────────────┬─────────────┘
                                          │
                                          ▼
                           ┌────────────────────────────┐
                           │         DuckDB             │
                           └──────────────┬─────────────┘
                                          │
                                          ▼
                           ┌────────────────────────────┐
                           │ Document Preprocessing      │
                           └──────────────┬─────────────┘
                                          │
                                          ▼
                           ┌────────────────────────────┐
                           │ Retrieval Documents (JSON) │
                           └──────────────┬─────────────┘
                                          │
                    ┌─────────────────────┼──────────────────────┐
                    ▼                     ▼                      ▼
            Text Search             TF-IDF Search        Semantic Search
                    └─────────────────────┬──────────────────────┘
                                          ▼
                              Retriever Factory
                                          │
                                          ▼
                                Prompt Builder
                                          │
                                          ▼
                                 Groq LLM API
                                          │
                                          ▼
                                 Generated Answer
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 ▼                        ▼                        ▼
            Monitoring              Analytics              User Feedback
```

This pipeline allows each stage to evolve independently without affecting the rest of the application.

---

# Project Architecture

One of the primary goals of this project was to organize the codebase in a way that mirrors how production systems are typically structured.

Instead of writing all logic inside a notebook or a single Python file, every major responsibility was isolated into its own package.

```
app/
│
├── dashboard/
│
├── evaluation/
│
├── ingestion/
│
├── monitoring/
│
├── processing/
│
├── rag/
│
├── retrieval/
│
└── tests/
```

Each package has a clearly defined responsibility.

| Folder | Responsibility |
|---------|----------------|
| app | Streamlit user interface |
| dashboard | Analytics dashboards |
| ingestion | Data loading using DLT |
| processing | Document preparation |
| retrieval | Search algorithms |
| rag | Prompting and LLM pipeline |
| evaluation | Evaluation framework |
| monitoring | Logging and feedback |
| tests | Component validation |

This separation greatly simplifies maintenance while also making the project easier for new contributors to understand.

---

# Retrieval Layer

The retrieval layer is the most important component of any Retrieval-Augmented Generation application.

Its responsibility is simple:

> Given a user's question, return the most relevant documents.

Instead of implementing only one retrieval algorithm, this project compares **three independent retrieval strategies**.

This design makes experimentation much easier and allows retrieval quality to be evaluated objectively.

---

# 1. Keyword Search

The first implementation uses traditional keyword search based on MinSearch.

This approach indexes fields such as:

- question
- book title
- searchable text

During retrieval, field-specific boosting is applied.

For example:

- Question field → highest importance
- Book title → medium importance
- Search text → standard importance

### Advantages

- Extremely fast
- Lightweight
- Exact phrase matching
- Excellent for book titles

### Limitations

- Cannot understand semantic similarity
- Sensitive to wording
- Misses synonyms

Example

User asks

> "Books about ML deployment"

If the document only contains

> "Machine Learning Systems"

keyword search may fail to retrieve it.

---

# 2. TF-IDF Retrieval

The second implementation uses TF-IDF vectorization.

Unlike keyword search, TF-IDF considers how important a term is across the entire document collection.

Frequently occurring words receive lower importance, while distinctive words receive higher weights.

Advantages

- Better ranking than keyword search
- Lightweight
- Fast
- Easy to interpret

Limitations

- Still relies on lexical similarity
- Cannot understand meaning
- Vocabulary mismatch remains a challenge

Although TF-IDF generally performs better than simple keyword matching, it still struggles when users express concepts using different wording.

---

# 3. Semantic Search

The final implementation uses Sentence Transformers to generate dense vector embeddings.

Every retrieval document is converted into a numerical vector representing its semantic meaning.

When a user submits a query:

1. The query is converted into an embedding.
2. Cosine similarity is computed.
3. Documents are ranked by similarity.

Unlike keyword-based retrieval, semantic search understands meaning rather than exact words.

For example,

Query:

> "How do I become an AI Engineer?"

can successfully retrieve documents containing

> Machine Learning

> Deep Learning

> Neural Networks

even if the exact words "AI Engineer" never appear.

This significantly improves retrieval quality.

---

# Why Semantic Search Became the Default

During experimentation, all three retrieval strategies were evaluated.

The observations were consistent.

Keyword Search

- Excellent for exact matches

- Poor for paraphrased questions

---

TF-IDF

- Better ranking

- Improved relevance

- Limited semantic understanding

---

Semantic Search

- Handles synonyms

- Better concept matching

- More natural interaction

- Highest quality responses

Because of these advantages, Semantic Search became the default retriever for the application.

The other retrieval methods remain available for experimentation and evaluation.

---

# Factory Pattern

One design decision that greatly improved maintainability was introducing a Retriever Factory.

Instead of writing conditional statements throughout the codebase,

```
if retriever == "semantic":
    ...

elif retriever == "tfidf":
    ...

elif retriever == "text":
    ...
```

the application centralizes retriever creation.

```
Retriever Factory
        │
        ├── Semantic Retriever
        ├── TF-IDF Retriever
        └── Text Retriever
```

Benefits include:

- cleaner code
- easier extensibility
- reduced coupling
- single responsibility

Adding another retriever now requires only:

1. Implement the retriever.
2. Register it in the factory.

No changes are required elsewhere.

---

# Prompt Engineering

Retrieval alone is insufficient.

The retrieved documents must be transformed into a prompt that guides the LLM.

The prompt follows a structured format.

```
System Instructions

↓

Retrieved Context

↓

User Question

↓

Expected Answer
```

The system prompt explicitly instructs the model to:

- answer only from retrieved documents
- avoid hallucination
- remain concise
- admit uncertainty
- cite relevant books

These instructions significantly improve response reliability.

---

# LLM Integration

The final prompt is sent to the Large Language Model.

Initially, this project used **GitHub Models** because they provide free access to several modern LLMs for experimentation.

This worked well during the early stages of development.

However, as the project evolved, new challenges emerged.

Large-scale evaluation required hundreds of API requests.

Monitoring generated additional requests.

Repeated retrieval experiments also increased API usage.

Eventually, GitHub Models' request limits became a bottleneck during development.

Rather than reducing experimentation, the project migrated to **Groq**.

Groq provided several advantages:

- significantly faster inference
- generous free tier
- stable API
- low latency
- easy OpenAI-compatible integration

Migrating required only a small change because the LLM interaction was isolated into its own module.

This illustrates one advantage of modular architecture.

Changing providers did not require modifying the retrieval pipeline, prompt builder, monitoring system, or evaluation framework.

Only the LLM wrapper changed.

---

# Complete Request Lifecycle

Every user question follows the same sequence.

```
User Question
      │
      ▼
Retrieve Relevant Documents
      │
      ▼
Construct Prompt
      │
      ▼
Send Prompt to Groq
      │
      ▼
Receive Generated Response
      │
      ▼
Log Metadata
      │
      ▼
Store Conversation
      │
      ▼
Collect Feedback
      │
      ▼
Display Answer
```

This lifecycle ensures that every response is:

- grounded in retrieved knowledge
- monitored
- measurable
- reproducible
- ready for future evaluation

# Evaluation Framework

Building a RAG application is only the first step. A more important question is:

> **How do we know if the system is actually performing well?**

Without evaluation, it is impossible to determine whether changes to the retrieval strategy, prompt, or embedding model improve or degrade the quality of responses.

To address this, the project includes a dedicated evaluation framework that measures retrieval effectiveness and provides a repeatable way to compare different configurations.

The evaluation pipeline is implemented independently from the main application so that experiments can be run without modifying production code.

---

# Evaluation Pipeline

The evaluation workflow consists of the following stages.

```
Knowledge Base
        │
        ▼
Ground Truth Dataset
        │
        ▼
Retriever
        │
        ▼
Generated Answer
        │
        ▼
Evaluation Metrics
        │
        ▼
Evaluation Report
```

This separation makes it possible to evaluate retrieval quality independently of the user interface.

---

# Ground Truth Dataset

A high-quality evaluation requires a reliable set of reference questions.

The project includes a manually curated ground truth dataset containing representative user questions about the book archive.

Examples include:

- beginner recommendations
- career-oriented questions
- book comparisons
- topic-specific searches
- implementation questions

These questions cover a wide range of realistic user interactions and provide a consistent benchmark for evaluating retrieval performance.

---

# Retrieval Evaluation

Each retrieval strategy is evaluated independently.

The project compares:

- Keyword Search
- TF-IDF Retrieval
- Semantic Search

Each strategy retrieves the top-k most relevant documents for every evaluation query.

The retrieved documents are then compared against the expected relevant documents to measure retrieval quality.

This makes it possible to objectively compare different retrieval approaches rather than relying solely on subjective impressions.

---

# LLM-as-a-Judge

Traditional metrics measure retrieval quality but do not always capture answer quality.

To evaluate generated responses, the project also incorporates an LLM-based evaluation approach.

For each generated answer, the judge model evaluates characteristics such as:

- factual correctness
- relevance
- completeness
- consistency with retrieved context

This provides an additional perspective beyond retrieval metrics alone.

Rather than replacing traditional evaluation, the LLM judge complements it by assessing the overall usefulness of generated responses.

---

# Why Evaluation Matters

Evaluation was integrated into the project from the beginning rather than being treated as an afterthought.

This allows the application to answer important engineering questions, such as:

- Did a new embedding model improve retrieval?
- Does prompt modification improve answer quality?
- Which retrieval strategy performs best?
- Are generated answers becoming more accurate?

Having a repeatable evaluation process makes future improvements measurable instead of relying on intuition.

---

# Monitoring

Generating answers is only one aspect of operating an LLM application.

Understanding how the system behaves in real-world usage is equally important.

For this reason, the project includes a monitoring subsystem that records metadata for every interaction.

Each conversation generates structured logs containing information such as:

- user question
- generated response
- selected retrieval strategy
- model used
- response time
- token usage
- timestamp

These records make it possible to analyze application behavior over time.

---

# Monitoring Workflow

```
User Question
        │
        ▼
Retrieve Documents
        │
        ▼
Generate Response
        │
        ▼
Record Metadata
        │
        ▼
Store Conversation
        │
        ▼
Analytics Dashboard
```

This workflow ensures that every interaction contributes to future analysis and system improvement.

---

# Conversation Logging

Every conversation is stored with relevant metadata rather than only the generated response.

Examples of captured information include:

- Question
- Generated answer
- Retrieval method
- Response latency
- Token consumption
- Timestamp

Storing this information enables historical analysis, debugging, and performance monitoring.

---

# Response Time Tracking

User experience depends heavily on latency.

The application records the total time required to generate each response.

Monitoring response time makes it easier to identify performance bottlenecks and evaluate the impact of future optimizations.

---

# Token Usage

LLM inference incurs computational cost.

To better understand resource consumption, the application tracks token usage for each interaction.

The recorded information includes:

- prompt tokens
- completion tokens
- total tokens

Tracking token usage provides visibility into model utilization and helps estimate operating costs when scaling the application.

---

# User Feedback

Automatic evaluation cannot capture every aspect of response quality.

To incorporate human judgment, the application allows users to provide direct feedback on generated answers.

This feedback helps identify situations where:

- retrieval failed
- context was insufficient
- answers were incomplete
- prompts could be improved

Combining automated evaluation with human feedback creates a stronger foundation for future iterations of the system.

---

# Analytics Dashboard

The project includes a dedicated analytics dashboard that presents key operational metrics through an interactive interface.

The dashboard provides insights such as:

- total conversations
- retrieval method usage
- response latency
- token consumption
- user feedback statistics
- evaluation summaries

Instead of inspecting raw logs, developers can quickly understand how the application is performing.

---

# Why Build Dashboards?

Dashboards transform raw monitoring data into actionable insights.

Examples include:

- identifying frequently asked questions
- detecting slow responses
- monitoring retrieval quality
- observing usage trends
- understanding user satisfaction

These insights support data-driven improvements rather than relying on assumptions.

---

# Testing

The project includes a dedicated testing package to verify the behavior of core components.

The tested modules include:

- configuration
- retrieval
- prompt generation
- LLM integration
- RAG pipeline

These tests ensure that individual components behave as expected and reduce the likelihood of regressions during future development.

Although the current test suite focuses on functional validation, the modular project structure makes it straightforward to expand toward comprehensive automated testing.

---

# Reproducibility

A key objective of this project is reproducibility.

Generated artifacts such as:

- embeddings
- processed documents
- local databases

are intentionally excluded from version control.

Instead, the repository provides scripts that regenerate these artifacts from the original dataset.

This approach offers several advantages:

- smaller repository size
- reproducible experiments
- deterministic processing pipeline
- easier collaboration
- cleaner version history

Anyone cloning the repository can recreate the complete application by running the ingestion, preprocessing, and embedding generation steps.

---

# Engineering Takeaways

This project extends beyond implementing a basic RAG pipeline.

It demonstrates several software engineering principles commonly found in production systems, including:

- modular architecture
- configuration-driven design
- reproducible data pipelines
- interchangeable retrieval strategies
- evaluation-driven development
- structured monitoring
- user feedback collection
- operational analytics

Together, these components create a complete Retrieval-Augmented Generation application that can be continuously evaluated, monitored, and improved over time.

# Project Structure

The repository is organized into modular packages, each responsible for a specific stage of the RAG pipeline.

```
DataTalksClub-Books-Assistant/
│
├── app/                    # Streamlit user interface
├── dashboard/              # Analytics and evaluation dashboards
├── data/
│   ├── raw/                # Original dataset
│   └── processed/          # Generated retrieval documents
│
├── embeddings/             # Generated semantic embeddings
├── evaluation/             # Evaluation framework
├── ingestion/              # DLT ingestion pipeline
├── monitoring/             # Logging and feedback system
├── notebooks/              # Exploratory notebooks
├── processing/             # Data preprocessing
├── rag/                    # Prompting and LLM pipeline
├── retrieval/              # Retrieval implementations
├── tests/                  # Component tests
│
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── main.py
├── run_evaluation.py
└── README.md
```

This structure separates concerns, making the project easier to understand, maintain, and extend.

---

# Installation

<!--## Prerequisites [ Try Online ]

https://datatalksclub-books-assistant.onrender.com-->

## Prerequisites [ Locally ]

Before running the project, ensure you have:

- Python 3.13 or later
- Git
- uv (recommended package manager)
- Groq API Key

---

## Clone the Repository

```bash
git clone https://github.com/<your-username>/DataTalksClub-Books-Assistant.git

cd DataTalksClub-Books-Assistant
```

---

## Install Dependencies

Using **uv** (recommended):

```bash
uv sync
```

or using pip:

```bash
pip install -e .
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_api_key_here
```

Additional configuration options can be adjusted in the project's configuration module if needed.

---

# Running the Project

The application is designed so that each stage of the pipeline can be executed independently.

---

## Step 1 — Ingest Data

Run the DLT ingestion pipeline.

```bash
python ingestion/dlt_pipeline.py
```

This loads the dataset into DuckDB.

---

## Step 2 — Process Documents

Generate retrieval-ready documents.

```bash
python processing/prepare_documents.py
```

---

## Step 3 — Generate Embeddings

Create semantic embeddings for retrieval.

```bash
python retrieval/generate_embeddings.py
```

> **Note:** Generated embeddings are not committed to the repository. They are created locally after cloning.

---

## Step 4 — Start the Application

Launch the Streamlit interface.

```bash
streamlit run app/main.py
```

The application will be available in your browser.

---

# Running the Evaluation

To compare retrieval strategies and generate evaluation reports:

```bash
python run_evaluation.py
```

The evaluation pipeline produces metrics and summary reports that can be used to compare different retrieval methods.

---

# Running Tests

Individual components can be validated using the provided test scripts.

```bash
python tests/test_pipeline.py
```

or

```bash
pytest
```

if additional automated tests are added in the future.

## Prerequisites [ Run using Docker ]

Build

```bash
docker build -t datatalksclub-books-assistant .
```

Run

```bash
docker run \
-p 8501:8501 \
--env-file .env \
datatalksclub-books-assistant
```

---

# Example Questions

The assistant is designed to answer natural language questions about the book archive.

Example queries include:

### Learning Paths

- Which books should I read to become a Data Engineer?
- Where should a beginner start with Machine Learning?
- Recommend books for learning MLOps.

---

### Book Comparison

- Compare the Machine Learning books in the archive.
- Which book is better for beginners?
- Which books focus on Deep Learning?

---

### Topic Search

- Which books explain feature engineering?
- Recommend books covering SQL optimization.
- Which books discuss vector databases?

---

### Community Knowledge

- What questions do readers commonly ask about Python?
- Which books are frequently recommended together?
- What advice is given to beginners?

---

# Lessons Learned

Developing this project provided valuable experience beyond implementing a Retrieval-Augmented Generation pipeline.

Some of the most important lessons include:

- Building a RAG application involves much more than calling an LLM API.
- Data quality has a direct impact on retrieval quality.
- Prompt engineering is important, but strong retrieval is even more critical.
- Evaluation should be integrated into the development process rather than performed only at the end.
- Monitoring and analytics are essential for understanding real-world application behavior.
- A modular architecture makes experimentation significantly easier.
- Separating ingestion, preprocessing, retrieval, and generation simplifies maintenance and future enhancements.
- Designing for reproducibility improves collaboration and long-term maintainability.

Perhaps the biggest lesson was that an effective RAG system is the result of many interconnected engineering decisions rather than a single model or library.

