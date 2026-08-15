# Recipe Assistant

A conversational AI that helps users choose recipes to help
people eat healthier.

Built as a demo project for [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp).

## Problem

There are many places to find recipes on the web. You can use type in
what you want on Google which does provide with links but you have to
go directly to a website to get nutritional information.

The Recipe Assistant is a RAG application that helps with:

1. Recipe Selection: Recommending recipes based on your nutrional needs are.
2. Recipe Instructions: Providing guidance on how to prepare a
   specific dish.
3. Conversational Interaction: Making it easy to get information
   without sifting through manuals or websites.

## Quickstart

The easiest way to run the application is with Docker Compose:

```bash
cp .envrc_template .envrc    # add your OPENAI_API_KEY
direnv allow                 # load the key
docker-compose up            # starts the app, postgres, and grafana
```

The app runs at http://localhost:5000

### Prerequisites

- Python 3.12
- Docker and Docker Compose
- OpenAI API key
- [direnv](https://direnv.net/) for environment variables
- [uv](https://docs.astral.sh/uv/) for dependency management

### Full setup

1. Install direnv and allow it:

   ```bash
   sudo apt install direnv
   direnv hook bash >> ~/.bashrc
   ```

2. Copy `.envrc_template` to `.envrc` and add your OpenAI API key:

   ```bash
   cp .envrc_template .envrc
   direnv allow
   ```

3. Install Python dependencies:

   ```bash
   uv sync
   ```

4. Initialize the database:

   ```bash
   docker-compose up postgres
   cd recipe_assistant
   export POSTGRES_HOST=localhost
   uv run python db.py
   ```

5. Run the app:

   ```bash
   docker-compose up
   ```



### Running locally

If you want to run the app directly on your machine instead of in Docker, start only the Postgres and Grafana containers as dependencies:

```bash
docker-compose up postgres 
```

Then run the app on your host machine:

```bash
cd recipe_assistant
export POSTGRES_HOST=localhost
uv run python app.py
```

### Time configuration

When inserting logs into the database, ensure the timestamps are correct.
Otherwise, they won't be displayed accurately in Grafana.

On some systems, specifically WSL, the clock in Docker may get out of sync.
You can check by running:

```bash
docker run ubuntu date
```

If the time doesn't match yours, sync the clock:

```bash
wsl
sudo apt install ntpdate
sudo ntpdate time.windows.com
```

## Testing

There is no automated test suite. The interactive CLI is the primary way to
test the application:

```bash
uv run python cli.py
```

Or pick a random question from the ground truth dataset:

```bash
uv run python cli.py --random
```

You can also test the API with curl:

```bash
URL=http://localhost:5000
QUESTION="Is the Lat Pulldown considered a strength training activity?"
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "'${QUESTION}'"}' \
    ${URL}/question
```

You can also send feedback:

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"conversation_id": "...", "feedback": 1}' \
    ${URL}/feedback
```

## Evaluation

### Retrieval evaluation

Ground truth dataset: 207 exercises with generated questions. The dataset
is in [`data/ground-truth-retrieval.csv`](data/ground-truth-retrieval.csv).


## Project structure

```text
fitness_assistant/
  app.py          # Flask API - main entrypoint
  rag.py          # RAG logic: retrieval + prompt building
  ingest.py       # Loads data into the in-memory search index
  db.py           # Logs requests and responses to PostgreSQL
  evaluating-retrieval-and-rag.ipynb     # RAG flow and retrieval evaluation
  evaluation-data-generation.ipynb
data/
  data.csv                       # 207 exercises (generated with ChatGPT)
  ground-truth-retrieval.csv     # Ground truth for retrieval evaluation
  rag-eval-gpt-5.4-mini.csv       # RAG evaluation results
  
docker-compose.yaml
Dockerfile
```

## Dataset

The dataset contains recipes from HuggingFace. Here is the original data: https://huggingface.co/datasets/datahiveai/recipes-with-nutrition.

You can find the data in [`data/recipes-with-nutrition-ids.csv`](data/recipes-with-nutrition-ids.csv).

## Limitations

- No automated test suite (only manual CLI and API testing).
- The dataset is small (207 exercises) and generated with ChatGPT, so
  instructions may not be as precise as professionally curated content.
- No web UI - only CLI and API.
- In-memory search means the index is rebuilt on every restart.
- No user authentication or multi-user support.
