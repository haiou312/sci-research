import pathlib
import tomllib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DailyNewsMinimalDiscoveryTests(unittest.TestCase):
    def load_agent(self, name):
        path = ROOT / ".codex" / "agents" / name
        return tomllib.loads(path.read_text(encoding="utf-8"))

    def test_scanner_is_terra_high_and_does_not_open_pages(self):
        agent = self.load_agent("sci-research-daily-news-scanner.toml")
        self.assertEqual(agent["model"], "gpt-5.6-terra")
        self.assertEqual(agent["model_reasoning_effort"], "high")
        instructions = agent["developer_instructions"]
        self.assertNotIn("open_page", instructions)
        self.assertIn("whether or not its page can be opened", instructions)

    def test_verifier_is_pass_through(self):
        agent = self.load_agent("sci-research-news-verifier.toml")
        instructions = agent["developer_instructions"]
        self.assertIn("do not search, open pages, verify, filter, score", instructions)
        self.assertIn("drop anything", instructions)

    def test_fact_extractor_is_luna_medium_with_search_result_basis(self):
        agent = self.load_agent("sci-research-daily-fact-extractor.toml")
        self.assertEqual(agent["model"], "gpt-5.6-luna")
        self.assertEqual(agent["model_reasoning_effort"], "medium")
        self.assertIn("evidence_basis: search-results", agent["developer_instructions"])

    def test_skill_has_exact_scope_templates(self):
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Default: `Search the web for news published on {date}", skill)
        self.assertIn("China: `Search foreign media only", skill)
        self.assertIn("Europe: `Search the web", skill)
        self.assertIn("Do not append any other search", skill)


if __name__ == "__main__":
    unittest.main()
