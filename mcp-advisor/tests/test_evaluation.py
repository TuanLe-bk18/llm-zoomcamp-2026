import pytest
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from evaluation.generate_eval_dataset import redact_text
from evaluation.llm_eval import evaluate_with_llm

def test_eval_query_has_no_server_name_leakage():
    """Test that redacting text successfully removes repo and owner names."""
    raw_text = "This is the punkpeye/awesome-mcp-servers repo. You can install it using npx @punkpeye/awesome-mcp-servers. See https://github.com/punkpeye/awesome-mcp-servers"
    server_id = "punkpeye/awesome-mcp-servers"
    
    redacted = redact_text(raw_text, server_id)
    
    assert "punkpeye" not in redacted
    assert "awesome-mcp-servers" not in redacted
    assert "[REDACTED_SERVER]" in redacted
    assert "[REDACTED_URL]" in redacted
    assert "[REDACTED_PACKAGE]" in redacted

class DummyClient:
    class Models:
        def generate_content(self, model, contents, config):
            class Response:
                text = '{"relevance": 5, "groundedness": 5, "constraint_satisfaction": 5, "usefulness": 5, "feedback": "Good"}'
            return Response()
    models = Models()
    
class FailingClient:
    class Models:
        def generate_content(self, model, contents, config):
            raise Exception("503 UNAVAILABLE")
    models = Models()

def test_failed_judge_returns_judge_failed():
    """Test that if the judge fails, it returns judge_failed=True."""
    client = FailingClient()
    result = evaluate_with_llm(client, "query", "output", [], "rationale", max_retries=1) # 1 retry to speed up test
    
    assert result.get("judge_failed") is True
    assert "error" in result

# For the advisor tests, we need to mock the Gemini client and ES search.
from agent.advisor import MCPAdvisor

def test_advisor_parses_valid_json(monkeypatch):
    class ValidGenAIClient:
        class Models:
            def generate_content(self, model, contents, config):
                class Response:
                    text = '{"recommended_server": "owner/repo", "all_hard_constraints_satisfied": true, "constraint_checks": [{"constraint": "test", "is_hard_constraint": true, "satisfied": true, "evidence": "evidence"}], "answer": "Detailed answer"}'
                return Response()
        models = Models()

    class DummySearch:
        def search_rrf(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = ValidGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q # skip rewrite llm
    
    result = advisor.recommend("test query")
    assert result["recommended_server"] == "owner/repo"
    assert result["answer"] == "Detailed answer"

def test_advisor_rejects_unknown_server(monkeypatch):
    class HallucinatingGenAIClient:
        class Models:
            def generate_content(self, model, contents, config):
                class Response:
                    # Always hallucinates a server not in candidates
                    text = '{"recommended_server": "fake/repo", "all_hard_constraints_satisfied": true, "constraint_checks": [{"constraint": "test", "is_hard_constraint": true, "satisfied": true, "evidence": "evidence"}], "answer": "Hallucinated answer"}'
                return Response()
        models = Models()

    class DummySearch:
        def search_rrf(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = HallucinatingGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q
    
    result = advisor.recommend("test query")
    # Should fall back to None and report parse_failed
    assert result["recommended_server"] is None

def test_advisor_handles_invalid_json(monkeypatch):
    class InvalidJsonGenAIClient:
        class Models:
            def generate_content(self, model, contents, config):
                class Response:
                    text = 'This is not JSON'
                return Response()
        models = Models()

    class DummySearch:
        def search_rrf(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = InvalidJsonGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q
    
    result = advisor.recommend("test query")
    assert result["recommended_server"] is None
    assert "parse_failed" in result["error"]

def test_advisor_rejects_unsatisfied_constraint(monkeypatch):
    class UnsatisfiedGenAIClient:
        class Models:
            def generate_content(self, model, contents, config):
                class Response:
                    text = '{"recommended_server": "owner/repo", "all_hard_constraints_satisfied": false, "constraint_checks": [{"constraint": "test", "is_hard_constraint": true, "satisfied": false, "evidence": "evidence"}], "answer": "Answer"}'
                return Response()
        models = Models()

    class DummySearch:
        def search_rrf(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = UnsatisfiedGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q
    
    result = advisor.recommend("test query")
    assert result["recommended_server"] is None

def test_advisor_rejects_fake_evidence(monkeypatch):
    class FakeEvidenceGenAIClient:
        class Models:
            def generate_content(self, model, contents, config):
                class Response:
                    text = '{"recommended_server": "owner/repo", "all_hard_constraints_satisfied": true, "constraint_checks": [{"constraint": "test", "is_hard_constraint": true, "satisfied": true, "evidence": "hallucinated"}], "answer": "Answer"}'
                return Response()
        models = Models()

    class DummySearch:
        def search_rrf(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = FakeEvidenceGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q
    
    result = advisor.recommend("test query")
    assert result["recommended_server"] is None
