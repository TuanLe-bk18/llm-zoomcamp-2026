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

def evaluate_with_llm(client, query, output, evidence, rationale):
    evidence_text = ""
    for ev in evidence[:3]: # Limit to top 3 evidence chunks to save tokens
        evidence_text += f"[{ev['server_id']}]: {ev['text'][:500]}...\\n"

    prompt = f"""
You are an expert evaluator judging the output of an MCP Recommendation system.
Evaluate the following recommendation based on these criteria:
1. Relevance (1-5): Does the recommended server solve the user's problem?
2. Groundedness (1-5): Are the claims strictly based on the "Evidence" provided below?
3. Constraint Satisfaction (1-5): Does it respect the constraints (e.g. local vs remote, auth vs no-auth) implied in the query?
4. Usefulness (1-5): Is the format clear and strictly adhered to?

User Query: "{query}"
Target Rationale / Expected: "{rationale}"

Provided Evidence to the Generator (Use this to judge Groundedness):
{evidence_text}

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
            model='gemini-3.5-flash',
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
        
    # Evaluate 20 stratified queries to save time/cost and respect 5 RPM quota
    sample_queries = queries[:20]
    
    results = []
    totals = {"relevance": 0, "groundedness": 0, "constraint_satisfaction": 0, "usefulness": 0}
    
    print(f"Evaluating {len(sample_queries)} queries with LLM-as-a-Judge (gemini-3.5-flash)...")
    
    for i, q in enumerate(sample_queries):
        print(f"\\n[{i+1}/{len(sample_queries)}] Evaluating query: {q['query']}")
        
        rec_result = advisor.recommend(q['query'])
        output = rec_result["answer"]
        evidence = rec_result["evidence"]
        
        eval_result = evaluate_with_llm(client, q['query'], output, evidence, q['rationale'])
        
        for k in totals.keys():
            totals[k] += eval_result.get(k, 0)
            
        results.append({
            "query": q['query'],
            "output": output,
            "eval": eval_result
        })
        
        if i < len(sample_queries) - 1:
            print("Sleeping for 15 seconds to respect Gemini Free Tier RPM limits...")
            time.sleep(15)
        
    n = len(sample_queries)
    summary = {k: v/n for k, v in totals.items()}
    
    print("\\n=== LLM Evaluation Summary ===")
    for k, v in summary.items():
        print(f"{k.capitalize()}: {v:.2f}/5.0")
        
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "judge_model": "gemini-3.5-flash",
            "evaluation_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "number_of_cases": n,
            "summary": summary, 
            "details": results
        }, f, indent=2)
        
    print(f"\\nFull report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
