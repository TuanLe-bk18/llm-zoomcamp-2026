import os
import sys
from openai import OpenAI

# Add parent dir to path to import es_search
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'retrieval'))
from es_search import ElasticMCPSearch

class MCPAdvisor:
    def __init__(self):
        # We assume OPENAI_API_KEY is exported in the environment
        # For Zoomcamp MVP, standard OpenAI client is used
        self.llm_client = OpenAI()
        
        es_url = os.getenv("ES_URL", "http://localhost:9200")
        self.search_engine = ElasticMCPSearch(es_url=es_url)

    def rewrite_query(self, user_query):
        """Phase 4: Rewrite the user requirement into a better search query."""
        prompt = f"""
You are an expert AI agent specializing in the Model Context Protocol (MCP).
The user is looking for an MCP server.
User requirement: "{user_query}"

Rewrite this requirement into a concise, keyword-rich search query that will be used to search a database of MCP server READMEs.
Return ONLY the search query, nothing else.
"""
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def recommend(self, user_query):
        print(f"Original requirement: {user_query}")
        
        # 1. Query Rewrite
        try:
            search_query = self.rewrite_query(user_query)
            print(f"Rewritten query for retrieval: {search_query}")
        except Exception as e:
            print(f"LLM Error during query rewrite (check OPENAI_API_KEY). Using raw query. Error: {e}")
            search_query = user_query
            
        # 2. Retrieve & Rerank Candidates
        candidates = self.search_engine.search_hybrid_rerank(search_query, top_k=5)
        
        if not candidates:
            return "No suitable MCP servers found in the database."
            
        # 3. Construct Evidence Context
        context_blocks = []
        for i, c in enumerate(candidates):
            repo_id = f"{c['owner']}/{c['repo']}"
            context_blocks.append(f"--- SERVER: {repo_id} (Score: {c['score']:.2f}) ---\\n{c['text']}\\n")
            
        context_str = "\\n".join(context_blocks)
        
        # 4. LLM Generation
        system_prompt = """
You are the MCP Advisor, an expert in Model Context Protocol integrations.
Given the user's requirement and the retrieved evidence from the MCP Registry (README chunks), recommend the most suitable MCP server.

Rules:
1. ONLY recommend servers that appear in the Evidence below. Do not make up servers.
2. Do NOT infer capabilities, security properties, or authentication methods that are not explicitly stated in the evidence.
3. Structure your response EXACTLY as follows:

Recommended: [Main Server Repo]
Why: [Brief explanation of why it fits]
Alternatives: [Alternative repos if any]
Authentication: [Auth methods mentioned, or "Not documented"]
Security / Permissions: [Security constraints/permissions mentioned, or "Not documented"]
Sources: [List of repos used]
"""
        
        user_prompt = f"User Requirement: {user_query}\\n\\nEvidence:\\n{context_str}"
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM generation failed: {e}\\n\\nTop candidate was: {candidates[0]['owner']}/{candidates[0]['repo']}"

if __name__ == "__main__":
    advisor = MCPAdvisor()
    test_query = "I need an MCP to automate browser interactions without using a cloud service."
    print("Running MCP Advisor...")
    print("======================\\n")
    result = advisor.recommend(test_query)
    print("\\n======================\\nRESULT:\\n")
    print(result)
