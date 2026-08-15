# 💰 Heartopia-Financial-Advisor
As an avid Heartopia player, I often found myself trying to find methods to earn enough coins to buy cute clothes, furniture, land, build houses, or even test my luck with Naughty's Treasures. Like most cozy games, Heartopia offers several hobbies such as Cooking, Fishing, Bird Watching, and Insect Catching where players can collect items and sell them to Albert Jr. for coins. Since every item has a different selling price, I had to manually calculate how many items I needed to sell to reach my weekly goal of 1 million coins.

That's what inspired this project. Heartopia Financial Assistant is an AI-powered chatbot designed to help players make smarter financial decisions in the game. Its knowledge base contains hobby items and their corresponding selling prices, allowing players to ask questions such as "How much can I sell my Blueberry Jam for?" or "What's the quickest way to earn 1 million coins?" Instead of manually doing the math, players can simply ask the chatbot and receive instant, context-aware answers.

# ▶️ App Preview
<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/6b11a14c-5b07-475e-ae83-a4a029de1d01" />
<p align="center"> Figure 1. Chat interface </p>
The application is deployed using Streamlit. Figure 1 shows the chat interface that users interact with after launching the application. The application, named Heartopia Financial Advisor, allows users to enter questions in the text input box at the bottom of the interface. In the example shown, the user asks, "How much profit does Blueberry make?", and the large language model (LLM) generates an appropriate response based on its knowledge base. Below the response is a feedback feature that enables users to evaluate the quality of the answer by clicking either the thumbs up or thumbs down button. This feedback can be used to assess the chatbot's performance and improve future responses. Users can also navigate to other pages through the side bar navigation panel on the left side where a short description of the project and a disclaimer is seen.

<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/063f675e-3621-4914-9578-82bf428cbe26" />
<p align="center"> Figure 2. Review Page </p>
The review page is where users can freely submit suggestions on ways the application can improve. The submitted form is appended to my csv.

<img width="975" height="485" alt="image" src="https://github.com/user-attachments/assets/1b69d401-ceae-480b-bf37-310438ee9dc7" />
<img width="975" height="486" alt="image" src="https://github.com/user-attachments/assets/38256552-6d50-4d9e-98ec-e1b92070e950" />
<p align="center"> Figure 3. Dashboard </p>
The dashboard page shows live update of feedbacks and recent queries of the user. This ensures that the developer can easily track and monitor anomalies while deployed.

<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/32d7e938-06e1-48d9-b119-664cbb34c848" />
<p align="center"> Figure 4. Credentials </p>
The credentials is a simple page showing the developer's details and where the data came from.

# 🧬 The RAG Pipeline
<h2> Data Preprocessing </h2>
The data is gathered first as an xlsx file where the items are separated through sheets by categories: food, bird, forage, fishing, and insect. To be able to build a financial assistant, I gathered only the relevant data for each sheet. The data needed to be checked and cleaned before turning it into csv and then cleaned the null values once again to prepare for data ingestion.

<h2> Ingestion and Containerization </h2>
Once the data is cleaned, it is structured into semantically dense text chunks. These chunks are processed through the all-MiniLM-L6-v2 embedding model to generate numerical vectors. The vectors and their associated metadata are then ingested into a ChromaDB instance, which runs persistently as a background service via docker-compose.

[ingest script](ingest2.ipynb)

<h2> Retrieval </h2>
When a user interacts with the Streamlit frontend, the system orchestrates a multi-step process to retrieve the correct information. First, the user's natural language query is vectorized using the all-MiniLM-L6-v2 model. The application then pings the local ChromaDB server to perform a semantic search, returning the top 5 (k=5) most relevant data chunks based on their mathematical proximity to the query. These retrieved chunks and the original query are then combined into a strict system prompt, which explicitly instructs the AI to act as a Heartopia game assistant and to rely only on the provided context to answer the question. This prompt is routed to Gemini 3.5 Flash, which serves as the primary generation engine due to its optimal balance of token efficiency. Furthermore, to guarantee high availability, the application features a fallback architecture. If the primary Gemini API hits rate limits (HTTP 429) or experiences server outages (HTTP 503), the system automatically catches the error and implements a backoff retry loop. If the primary model ultimately fails, the request is routed to a secondary OpenAI GPT-4o-mini client, ensuring the user always receives a response.

[retrieval script](retrieval2.ipynb)

# 📊 Evaluation Criteria
To ensure the reliability of the Retrieval-Augmented Generation (RAG) pipeline, the system's retrieval component was quantitatively evaluated.

<b> Retrieval Performance: Mean Reciprocal Rank (MRR) </b>
The vector search performance of the ChromaDB backend (powered by the `all-MiniLM-L6-v2` embedding model) was measured using MRR. 18 questions were manually curated for the evaluation. The results: Retrieval Hit Rate = 88.89%.
You can view the complete evaluation logic in the [evaluation.ipynb](Evaluation/evaluation.ipynb) notebook.

<h2> Ready to try the code? </h2>

[set-up.md](set-up.md)

