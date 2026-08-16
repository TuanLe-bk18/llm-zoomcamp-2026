import os
import json
import sys
import time
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agent'))
from advisor import MCPAdvisor

EVAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "llm_report.json")

class JudgeEvaluation(BaseModel):
    relevance: float = Field(description="Relevance score (1-5)")
    groundedness: float = Field(description="Groundedness score (1-5)")
    constraint_satisfaction: float = Field(description="Constraint satisfaction score (1-5)")
    usefulness: float = Field(description="Usefulness score (1-5)")
    feedback: str = Field(description="Brief comment explaining the scores")

def evaluate_with_llm(client, query, output, evidence, rationale, max_retries=3):
    # Pass all evidence instead of truncating
    evidence_text = "\\n\\n".join([f"[{ev['server_id']}]: {ev['text']}" for ev in evidence])

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
"""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JudgeEvaluation,
                    temperature=0.0
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"  [Retry {attempt+1}/{max_retries}] Eval Error: {e}")
            time.sleep(2 ** attempt * 5) # Exponential backoff: 5s, 10s, 20s
            
    return {"judge_failed": True, "error": "Max retries exceeded"}

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        return

    client = genai.Client(api_key=api_key)
    advisor = MCPAdvisor()
    
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        queries = json.load(f)
        
    sample_queries = queries[:20]
    
    results = []
    totals = {"relevance": 0, "groundedness": 0, "constraint_satisfaction": 0, "usefulness": 0}
    successful_judges = 0
    failed_judges = 0
    
    print(f"Evaluating {len(sample_queries)} queries with LLM-as-a-Judge (gemini-3.5-flash)...")
    
    for i, q in enumerate(sample_queries):
        print(f"\\n[{i+1}/{len(sample_queries)}] Evaluating query: {q['query']}")
        
        rec_result = advisor.recommend(q['query'])
        output = rec_result["answer"]
        evidence = rec_result["evidence"]
        
        eval_result = evaluate_with_llm(client, q['query'], output, evidence, q['rationale'])
        
        if eval_result.get("judge_failed"):
            failed_judges += 1
            print("  Judge failed.")
        else:
            successful_judges += 1
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
        
    failure_rate = failed_judges / len(sample_queries)
    is_valid = failure_rate <= 0.10
    
    summary = {k: v / successful_judges if successful_judges > 0 else 0 for k, v in totals.items()}
    
    print("\\n=== LLM Evaluation Summary ===")
    print(f"Judged Successfully: {successful_judges}/{len(sample_queries)}")
    print(f"Judge Failed: {failed_judges} ({failure_rate:.1%})")
    print(f"Run Valid: {'YES' if is_valid else 'NO (Failure rate > 10%)'}")
    
    if is_valid:
        for k, v in summary.items():
            print(f"{k.capitalize()}: {v:.2f}/5.0")
        
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "judge_model": "gemini-3.5-flash",
            "evaluation_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "number_of_cases": len(sample_queries),
            "successful_judges": successful_judges,
            "failed_judges": failed_judges,
            "failure_rate": failure_rate,
            "is_valid": is_valid,
            "summary": summary, 
            "details": results
        }, f, indent=2)
        
    print(f"\\nFull report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
