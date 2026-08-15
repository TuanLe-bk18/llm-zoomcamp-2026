import os
import sys
from google import genai
from google.genai import types

# Add parent dir to path to import es_search
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'retrieval'))
from es_search import ElasticMCPSearch

class MCPAdvisor:
    def __init__(self):
        # We assume GEMINI_API_KEY is exported in the environment
        self.llm_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
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
        response = self.llm_client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )
        return response.text.strip()

    def recommend(self, user_query):
        print(f"Original requirement: {user_query}")
        
        # 1. Query Rewrite
        try:
            search_query = self.rewrite_query(user_query)
            print(f"Rewritten query for retrieval: {search_query}")
        except Exception as e:
            print(f"LLM Error during query rewrite (check GEMINI_API_KEY). Using raw query. Error: {e}")
            search_query = user_query
            
        # 2. Retrieve & Rerank Candidates
        candidates = self.search_engine.search_hybrid_rerank(search_query, top_k=5)
        
        if not candidates:
            return "No suitable MCP servers found in the database."
            
        # 3. Construct Evidence Context
        context_blocks = []
        for c in candidates:
            server_id = c.get('server_id', 'unknown')
            text = c.get('text', '')
            score = c.get('score', 0.0)
            url = c.get('source_url', '')
            context_blocks.append(f"--- SERVER: {server_id} (Score: {score:.2f}) ---\\nURL: {url}\\n{text}\\n")
            
        context_str = "\\n".join(context_blocks)
        
        # 4. LLM Generation
        system_prompt = """
You are the MCP Advisor, an expert in Model Context Protocol integrations.
Given the user's requirement and the retrieved evidence from the MCP Registry (README chunks), recommend the most suitable MCP server.

CRITICAL GROUNDING RULES:
1. ONLY recommend servers that appear in the Evidence below. Do not make up servers.
2. Every recommendation claim must be grounded in the retrieved README chunks.
3. You MUST NOT claim capabilities, authentication methods, permissions, installation steps, or security properties that are not supported by the retrieved evidence. If it is not in the evidence, say "Not documented".

Structure your response EXACTLY as follows:

Recommended: [Main Server Repo]
Why: [Brief explanation of why it fits based ON EVIDENCE]
Alternatives: [Alternative repos if any, based ON EVIDENCE]
Authentication: [Auth methods mentioned, or "Not documented"]
Local/Remote: [Is it local or remote, or "Not documented"]
Permissions / Security: [Security constraints/permissions mentioned, or "Not documented"]
Installation notes: [Installation notes mentioned, or "Not documented"]
Sources: [List of source URLs for the recommended server]
"""
        
        user_prompt = f"User Requirement: {user_query}\\n\\nEvidence:\\n{context_str}"
        
        try:
            response = self.llm_client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=[system_prompt, user_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            return response.text.strip()
        except Exception as e:
            return f"LLM generation failed: {e}\\n\\nTop candidate was: {candidates[0].get('server_id')}"

if __name__ == "__main__":
    advisor = MCPAdvisor()
    test_query = "I need an MCP to automate browser interactions without using a cloud service."
    print("Running MCP Advisor...")
    print("======================\\n")
    result = advisor.recommend(test_query)
    print("\\n======================\\nRESULT:\\n")
    print(result)
