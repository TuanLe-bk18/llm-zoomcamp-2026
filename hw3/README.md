# LLM Zoomcamp Homework 3 (Cohort 2026)

This folder contains my solution for Homework 3: AI Orchestration with Kestra.

## Question Answers
1. **Question 1: Context Engineering:** AI Copilot has access to current Kestra plugin documentation
2. **Question 2: RAG vs No RAG:** Vague, generic, or fabricated — the model guesses from training data
3. **Question 3: Token usage — short summary:** 60-100 tokens
4. **Question 4: Token usage — long summary:** 2-5x more
5. **Question 5: Modifying a flow:** 2-4x more
6. **Question 6: Best Practices:** Use traditional task-based workflows for predictability and auditability

## Code for Question 5
As required by the homework instructions, below is the modified YAML code for `4_simple_agent.yaml` used to answer Question 5, where the `english_brevity` prompt is modified to ask for exactly 3 sentences:

```yaml
id: 4_simple_agent
namespace: zoomcamp

description: |
  This flow demonstrates a basic AI agent that summarizes text with controllable length and language. It shows:
  - How to structure agent prompts
  - How to chain multiple agent tasks
  - How to use pluginDefaults to avoid repetition
  - How to track token usage for cost monitoring

inputs:
  - id: summary_length
    displayName: Summary Length
    type: SELECT
    defaults: medium
    values:
      - short
      - medium
      - long

  - id: language
    displayName: Language
    type: SELECT
    defaults: en
    values:
      - en
      - fr
      - de
      - es
      - it
      - pt
      - ja

  - id: text
    type: STRING
    displayName: Text to summarize
    defaults: |
      Kestra is an open-source orchestration platform that allows you to define workflows declaratively in YAML. It enables both developers and non-developers to automate tasks through a no-code interface, while keeping everything versioned, governed, secure, and auditable. Kestra extends easily for custom use cases through plugins and custom scripts.
      
      Kestra follows a "start simple and grow as needed" philosophy. You can schedule a basic workflow in a few minutes, then later add Python scripts, Docker containers, or complex branching logic if the situation requires it. This makes Kestra ideal for data engineering, ETL pipelines, business process automation, and more.
      
      In LLM Zoomcamp, we learn how to build production-ready LLM applications using RAG, vector search, agents, and evaluation. In this bonus module, we're exploring how AI can accelerate workflow development through AI Copilot, RAG, and autonomous agents.

tasks:
  - id: multilingual_agent
    type: io.kestra.plugin.ai.agent.AIAgent
    description: Generate summary in requested language and length
    systemMessage: |
      You are a precise technical assistant.
      Produce a {{ inputs.summary_length }} summary in {{ inputs.language }}.
      Keep it factual, remove fluff, and avoid marketing language.
      If the input is empty or non-text, return a one-sentence explanation.
      
      Output format guidelines:
      - For 'short': 1-2 sentences
      - For 'medium': 2-5 sentences  
      - For 'long': 1-3 paragraphs
    prompt: |
      Summarize the following content: {{ inputs.text }}

  - id: english_brevity
    type: io.kestra.plugin.ai.agent.AIAgent
    prompt: |
      Generate exactly 3 sentences English summary of the following:
      "{{ outputs.multilingual_agent.textOutput }}"

  - id: log_token_usage
    type: io.kestra.plugin.core.log.Log
    message: |
      📊 Token Usage Summary:
      
      Multilingual Agent:
      - Input tokens: {{ outputs.multilingual_agent.tokenUsage.inputTokenCount }}
      - Output tokens: {{ outputs.multilingual_agent.tokenUsage.outputTokenCount }}
      - Total tokens: {{ outputs.multilingual_agent.tokenUsage.totalTokenCount }}
      
      English Brevity Agent:
      - Input tokens: {{ outputs.english_brevity.tokenUsage.inputTokenCount }}
      - Output tokens: {{ outputs.english_brevity.tokenUsage.outputTokenCount }}
      - Total tokens: {{ outputs.english_brevity.tokenUsage.totalTokenCount }}
      
      💡 Tip: Monitor token usage to understand costs and optimize prompts!

pluginDefaults:
  - type: io.kestra.plugin.ai.agent.AIAgent
    values:
      provider:
        type: io.kestra.plugin.ai.provider.GoogleGemini
        modelName: gemini-2.5-flash
        apiKey: "{{ secret('GEMINI_API_KEY') }}"
```

## Setup & Execution

To run these flows locally:
1. Start Kestra using Docker Compose:
   ```bash
   docker-compose up -d
   ```
2. Navigate to `http://localhost:8080` to access the Kestra UI.
3. Configure the `GEMINI_API_KEY` in the Kestra Secrets configuration.
4. Import the flow YAML files from the `flows/` directory into Kestra and execute them via the UI.
