<h2> DataTalksClub's Book of the week's archive assistant

<h3>The Problem</h3>

Users often need a faster and more convenient way to find answers about the books and authors featured in the DataTalksClub ["Book of the Week"](https://datatalks.club/books.html) series. As the archive of featured books continues to grow, manually browsing the collection can become time-consuming and overwhelming.

Additionally, some book summaries and author biographies are lengthy or written in a style that may be difficult to quickly understand. This creates a challenge for users with limited time, making it harder to locate relevant information and efficiently interpret the content available on the website.

---

<h3>How This Application Solves the Problem</h3>

This application uses a Large Language Model (LLM), similar to the AI behind ChatGPT, to help users quickly understand the book summaries and author biographies available on the DataTalks.Club website. Instead of searching through the entire archive, users can ask questions in natural language and receive clear, concise answers about the books, authors, and when they were featured in the "Book of the Week" series.

Users interact with the application through a simple web interface. After submitting a question, they receive an AI-generated answer along with evaluation scores for the retrieval and LLM responses. They can also provide feedback by giving the answer a thumbs up (+1) or thumbs down (-1).

![picture of user interface](./images/user-interface.png)

The application also includes a monitoring dashboard for maintainers. It tracks key metrics such as response time, token usage, request volume, system cost, and user feedback, helping monitor performance and improve the RAG system over time.

![picture of monitoring](./images/monitoring.png)

---

<h3> The Evaluation Criteria </h3>

Both the retrieval output and the LLM-generated response are evaluated using a separate LLM-based evaluator. Given the user's question and the generated answer, the evaluator assesses how well the answer addresses the question and assigns one of the following labels:

- <b>RELEVANT</b>: The answer fully addresses the question.
- <b>PARTLY_RELEVANT</b>: The answer addresses the question only partially.
- <b>NON_RELEVANT</b>: The answer does not address the question.

In case of exception, the evaluation is retried and repeated up to a configurable maximum number of retries (3 by default). The final evaluation result is then presented to the user.

---

<h3> The Setup </h3>

This project is containerized with Docker Compose, so only Docker and Docker Compose are required to run the application. All Python dependencies and their versions are managed in the pyproject.toml file.

Install the required tools using the official documentation:

Docker Desktop: https://docs.docker.com/desktop/

Docker Engine: https://docs.docker.com/engine/install/

Docker Compose: https://docs.docker.com/compose/install/

To run the project locally, first clone this repository. If you do not have Git installed, download it from: https://git-scm.com/install/

After installing Git, run the following command to clone the repository:

    git clone https://github.com/bsh90/datatalksclub_bookoftheweek_archiveassistant.git

Inside the cloned project directory, create a .env file and add your OpenRouter API key:

OPENROUTER_API_KEY=your_api_key

If you use a different LLM provider, update the client configuration in evaluator.py, rag_assistant.py and dashboard.py(the model fields) accordingly.

Once Docker, Docker Compose, and the project are set up, start the application by running:

    docker compose up --build

After the containers are running, access:

User interface: http://localhost:8501/

Monitoring dashboard: http://localhost:3000/

To setup the monitoring dashboard, open Grafana at http://localhost:3000/. From the left sidebar, navigate to Connections &rarr; Data Sources and add two SQLite data sources:

traces &rarr; /var/lib/grafana/traces.db

feedback &rarr; /var/lib/grafana/feedback.db

Next, open Dashboards and create six panels. For each panel, select the appropriate data source, enter the corresponding query in the Queries section, and save the panel.

![picture of monitoring query section](./images/monitoring-query.png)

<h4>Response Time Panel</h5>

In the Query section, select the traces data source. From the visualization options in the right toolbar, choose "Time series". You can find this option by clicking the Change button at the top of the right toolbar in the Edit Panel view.

    SELECT
        strftime('%Y-%m-%dT%H:%M:%SZ', start_time / 1000000000, 'unixepoch') AS time,
        SUM((end_time - start_time) / 1000000.0) AS response_time_ms
    FROM spans
    GROUP BY time
    ORDER BY time;

<h4>Token Usage Panel</h4>

    SELECT
        strftime('%Y-%m-%dT%H:%M:%SZ', start_time / 1000000000, 'unixepoch') AS time,
        SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)) AS total_token
    FROM spans
    GROUP BY time
    ORDER BY time;

<h4>Request Volume Panel</h4>

    SELECT
    strftime('%Y-%m-%dT%H:%M:%SZ', start_time / 1000000000, 'unixepoch') AS time,
    COUNT(*) AS requests
    FROM spans
    GROUP BY time
    ORDER BY time;

<h4>Feeback Panel</h4>

In the Query section, select the feedback data source.  From the visualization options in the right toolbar, choose "Bar gauge".

    SELECT
        SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) AS thumbs_up,
        SUM(CASE WHEN score < 0 THEN 1 ELSE 0 END) AS thumbs_down
    FROM feedback;

<h4>Input vs Output Token Panel</h4>

In the Query section, select the traces data source. From the visualization options in the right toolbar, choose "Bar chart".

    SELECT
        CAST(start_time / 1000000000 AS INTEGER) AS time,
        SUM(input_tokens) AS "Input Tokens",
        SUM(output_tokens) AS "Output Tokens"
    FROM spans
    WHERE input_tokens IS NOT NULL
    OR output_tokens IS NOT NULL
    GROUP BY CAST(start_time / 1000000000 AS INTEGER)
    ORDER BY time;

<h4>Cost Panel</h4>

    SELECT
        strftime('%Y-%m-%dT%H:%M:%SZ', start_time /1000000000, 'unixepoch') AS time,
        SUM(cost) AS total_cost
    FROM spans
    GROUP BY time
    ORDER BY time;


To stop the application, press <b>Ctrl + C</b> in the terminal where Docker Compose is running. Then, run the following command to shut down and remove the containers:

    docker compose down

---

<h3> Usage: A Short Walkthrough </h3>

Navigate to the project folder and start the application with:

    docker compose up

Access the applications at:

User interface: http://localhost:8501/

Monitoring dashboard: http://localhost:3000/

In the user interface, ask questions about books or authors and review the retrieved information, along with the evaluations of both the retrieval response and the LLM-generated answer.

![picture of LLM answer example](./images/llm-answer-example.png)

You can provide feedback on the answer by selecting a +1 (thumbs up) or -1 (thumbs down) rating.

![picture of feedback example](./images/feedback-example.png)

Finally, open the monitoring dashboard to view how the system metrics and graphs have changed based on your recent activity. 

![picture of monitoring example](./images/monitoring-example.png)

---

<h3>Troubleshooting</h3>

If you encounter any errors, stop the application by pressing <b>Ctrl + C</b> and run:

    docker compose down

Then restart the application with:

    docker compose up --build

If the issue persists, contact <b>@B Sh</b> on the DataTalks.Club Slack workspace or use the member ID: <b>U0BCX73U324</b>.

---