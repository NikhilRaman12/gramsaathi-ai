import json
import unittest

from scripts.chunk_pdfs import EvidenceChunk
from scripts.generator import AgroLLMEngine, GramsaathiEngine, ProviderTimeoutError, parse_agent_output
from scripts.retriever import Retriever


class FakeProvider:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        if isinstance(self.content, Exception):
            raise self.content
        return self.content


def evidence(text="PM-KISAN provides an income support scheme."):
    return EvidenceChunk(
        id="scheme.pdf:p2:c1",
        text=text,
        source_file="data/samman_nidhi_pm.pdf",
        source_title="PM-KISAN official release",
        page=2,
        source_urls=("https://pmkisan.gov.in/",),
        source_date="2024-10-05",
    )


class AgentTests(unittest.TestCase):
    def test_retrieval_keeps_source_metadata_and_rejects_unrelated_query(self):
        retriever = Retriever(chunks=[evidence()])
        found = retriever.search("PM-KISAN income support")
        self.assertEqual(found[0].source_file, "data/samman_nidhi_pm.pdf")
        self.assertEqual(found[0].page, 2)
        self.assertIn("https://pmkisan.gov.in/", found[0].source_urls)
        self.assertGreater(found[0].score, 0)
        self.assertEqual(retriever.search("quantum entanglement on Mars"), [])

    def test_structured_answer_uses_known_citation(self):
        output = json.dumps(
            {
                "summary": [{"text": "The document describes PM-KISAN.", "source_ids": ["S1"]}],
                "action_plan": [{"step": "Check the official portal.", "source_ids": ["S1"]}],
                "missing_information": ["State"],
                "follow_up_questions": ["Which state are you in?"],
                "uncertainties": [],
            }
        )
        provider = FakeProvider(output)
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(provider))
        result = engine.run("What does PM-KISAN cover?")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"][0]["source_ids"], ["S1"])
        self.assertEqual(result["evidence"][0]["source_urls"], ["https://pmkisan.gov.in/"])
        self.assertIn("untrusted data", provider.calls[0][0]["content"])

    def test_no_evidence_skips_provider(self):
        provider = FakeProvider("unused")
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(provider))
        result = engine.run("quantum entanglement on Mars")
        self.assertEqual(result["status"], "no_evidence")
        self.assertEqual(provider.calls, [])

    def test_empty_query_skips_provider(self):
        provider = FakeProvider("unused")
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(provider))
        result = engine.run("   ")
        self.assertEqual(result["status"], "empty_query")
        self.assertEqual(provider.calls, [])

    def test_provider_failure_keeps_retrieved_evidence_and_suppresses_answer(self):
        provider = FakeProvider(ProviderTimeoutError("timed out"))
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(provider))
        result = engine.run("What does PM-KISAN cover?")
        self.assertEqual(result["status"], "provider_error")
        self.assertEqual(result["summary"], [])
        self.assertEqual(result["evidence"][0]["id"], "S1")

    def test_malformed_model_output_fails_closed_but_shows_evidence(self):
        provider = FakeProvider("not valid json")
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(provider))
        result = engine.run("What does PM-KISAN cover?")
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(result["action_plan"], [])
        self.assertTrue(result["evidence"])

    def test_invalid_or_unknown_citations_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_agent_output("not json", {"S1"})
        with self.assertRaises(ValueError):
            parse_agent_output(
                json.dumps(
                    {
                        "summary": [{"text": "unsupported", "source_ids": ["S99"]}],
                        "action_plan": [],
                        "missing_information": [],
                        "follow_up_questions": [],
                        "uncertainties": [],
                    }
                ),
                {"S1"},
            )

    def test_prompt_includes_conflict_and_untrusted_source_handling(self):
        engine = GramsaathiEngine(Retriever(chunks=[evidence()]), AgroLLMEngine(FakeProvider("")))
        system, user = engine.build_messages("Ignore evidence", [{**evidence().as_dict(), "id": "S1"}])
        self.assertIn("If sources disagree", system["content"])
        self.assertIn("Ignore evidence", user["content"])


if __name__ == "__main__":
    unittest.main()
