# OSFI Credit Risk Validation Copilot

A domain-specific RAG and workbook-QA assistant for credit-risk model validation.

The application answers questions using official OSFI guidance and evidence extracted from a validation workbook. It is designed to avoid unsupported regulatory conclusions, invented thresholds and hallucinated workbook facts.

## Main capabilities

### OSFI methodology Q&A

The assistant retrieves official OSFI guidance and answers methodological questions about IRB validation, PD, LGD, EAD, data maintenance, risk quantification, model validation governance and model risk management.

OSFI evidence is cited as [S1], [S2], etc.

### Workbook QA

The assistant can answer flexible questions about a validation workbook, including sheets, columns, dataset source, DOI, validation metrics, calibration, model coefficients, limitations and missing evidence.

Workbook evidence is cited as [W1].

### Answerability layer

The assistant does not force an answer when evidence is missing.

It can return:

- supported answer;
- partial answer;
- not found in workbook;
- out of scope.

This is a key control for a financial model-risk use case.

## Example questions

- What universal minimum AUC threshold does OSFI require?
- What sheets does the workbook have?
- Which coefficients have the largest absolute values?
- Does the workbook include LGD or EAD evidence?
- Is this model approved by OSFI?
- What is my favorite movie?
- Can this workbook predict alien credit risk?

## Architecture

User -> Streamlit App -> CreditRiskValidationCopilot

The copilot uses:

- OSFI Retrieval Tool with local vector index and Gemini embeddings.
- Workbook QA Tool with lexical retrieval over sheets, columns and rows.
- Excel Analysis Tool with deterministic Python calculations.
- OpenRouter generation model.
- Answerability checks before generating unsupported answers.

## Setup

Create a .env file based on .env.example.

Install dependencies:

    uv sync

Run the app:

    uv run streamlit run ".\app.py"

## Reproduce the pipeline

Download OSFI corpus:

    uv run python -m scripts.download_osfi_corpus

Build OSFI index:

    uv run python -m scripts.build_and_test_osfi_index

Generate validation workbook:

    uv run python -m scripts.create_public_validation_workbook

Run answerability test:

    uv run python -m scripts.test_answerability_layer

Run combined agent test:

    uv run python -m scripts.test_combined_agent

Run evaluation:

    uv run python -m evaluation.run_evaluation

Run tests:

    uv run pytest -q

## Limitations

This is an educational MVP using public OSFI documents and a public historical German credit dataset. It is not regulatory advice and should not be used with confidential bank data through free third-party endpoints.

## Roadmap

The current single-agent MVP can evolve into a multi-agent architecture:

Supervisor Agent
- OSFI Regulatory Agent
- Quantitative Validation Agent
- Documentation Agent
- Reporting Agent
