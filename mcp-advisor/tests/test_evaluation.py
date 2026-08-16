import pytest
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


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
        def search_production(self, query, top_k):
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
        def search_production(self, query, top_k):
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
        def search_production(self, query, top_k):
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
        def search_production(self, query, top_k):
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
        def search_production(self, query, top_k):
            return [{"server_id": "owner/repo", "text": "evidence", "score": 1.0}]

    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    advisor = MCPAdvisor()
    advisor.llm_client = FakeEvidenceGenAIClient()
    advisor.search_engine = DummySearch()
    advisor.rewrite_query = lambda q: q
    
    result = advisor.recommend("test query")
    assert result["recommended_server"] is None
