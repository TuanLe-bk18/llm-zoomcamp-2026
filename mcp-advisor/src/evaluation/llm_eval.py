import os
import json
import sys
import time
from google import genai
from google.genai import types

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agent'))
from advisor import MCPAdvisor

EVAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "llm_report.json")

def evaluate_with_llm(client, query, output, rationale):
    prompt = f"""
You are an expert evaluator judging the output of an MCP Recommendation system.
Evaluate the following recommendation based on these criteria:
1. Relevance (1-5): Does the recommended server solve the user's problem?
2. Groundedness (1-5): Are the claims strictly based on the "Evidence" provided? (Assume 'Yes' unless it hallucinates widely known features not in the output)
3. Constraint Satisfaction (1-5): Does it respect the constraints (e.g. local vs remote)?
4. Usefulness (1-5): Is the format clear and strictly adhered to?

User Query: "{query}"
Target Rationale / Expected: "{rationale}"

System Output:
{output}

Return ONLY a JSON object with the scores:
{{
  "relevance": 5,
  "groundedness": 5,
  "constraint_satisfaction": 5,
  "usefulness": 5,
  "feedback": "Brief comment"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Eval Error: {e}")
        return {"relevance": 0, "groundedness": 0, "constraint_satisfaction": 0, "usefulness": 0, "feedback": str(e)}

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        return

    client = genai.Client(api_key=api_key)
    advisor = MCPAdvisor()
    
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        queries = json.load(f)
        
    # Evaluate 10 random queries to save time/cost
    sample_queries = queries[:10]
    
    results = []
    totals = {"relevance": 0, "groundedness": 0, "constraint_satisfaction": 0, "usefulness": 0}
    
    print(f"Evaluating {len(sample_queries)} queries with LLM-as-a-Judge...")
    
    for q in sample_queries:
        print(f"\\nEvaluating query: {q['query']}")
        output = advisor.recommend(q['query'])
        eval_result = evaluate_with_llm(client, q['query'], output, q['rationale'])
        
        for k in totals.keys():
            totals[k] += eval_result.get(k, 0)
            
        results.append({
            "query": q['query'],
            "output": output,
            "eval": eval_result
        })
        time.sleep(2)
        
    n = len(sample_queries)
    summary = {k: v/n for k, v in totals.items()}
    
    print("\\n=== LLM Evaluation Summary ===")
    for k, v in summary.items():
        print(f"{k.capitalize()}: {v:.2f}/5.0")
        
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"summary": summary, "details": results}, f, indent=2)
        
    print(f"\\nFull report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
