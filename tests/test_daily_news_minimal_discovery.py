import pathlib
import tomllib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DailyNewsMinimalDiscoveryTests(unittest.TestCase):
    def load_agent(self, name):
        path = ROOT / ".codex" / "agents" / name
        return tomllib.loads(path.read_text(encoding="utf-8"))

    def test_scanner_is_terra_high_and_uses_google_news_search_only(self):
        agent = self.load_agent("sci-research-daily-news-scanner.toml")
        self.assertEqual(agent["model"], "gpt-5.6-terra")
        self.assertEqual(agent["model_reasoning_effort"], "high")
        instructions = agent["developer_instructions"]
        self.assertIn("mcp__google_news__search_news", instructions)
        self.assertIn("Do not call `get_news_article`", instructions)
        self.assertIn("do not use Codex native WebSearch", instructions)
        self.assertIn("whether or not its article can be fetched", instructions)

    def test_verifier_is_deduplication_only(self):
        agent = self.load_agent("sci-research-news-verifier.toml")
        self.assertEqual(agent["model"], "gpt-5.6-terra")
        self.assertEqual(agent["model_reasoning_effort"], "high")
        instructions = agent["developer_instructions"]
        self.assertIn("same-event deduplication", instructions)
        self.assertIn("keep the first occurrence", instructions)
        self.assertIn("DROP_DUPLICATE", instructions)
        self.assertIn("Do not search, fetch pages, verify facts or dates", instructions)
        self.assertIn("drop a unique result", instructions)

    def test_verifier_schema_has_deduplication_arithmetic(self):
        schema = (
            ROOT / "skills" / "daily-news-intelligence" / "references" / "schemas.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Mode: deduplication-only", schema)
        self.assertIn("Input count = Kept count + Duplicate count", schema)
        self.assertIn("The only valid DROP verdict is `DROP_DUPLICATE`", schema)
        self.assertIn("duplicate chains are forbidden", schema)

    def test_fact_extractor_is_luna_medium_with_search_result_basis(self):
        agent = self.load_agent("sci-research-daily-fact-extractor.toml")
        self.assertEqual(agent["model"], "gpt-5.6-luna")
        self.assertEqual(agent["model_reasoning_effort"], "medium")
        self.assertIn("evidence_basis: search-results", agent["developer_instructions"])
        self.assertIn("all Corroborated by URLs", agent["developer_instructions"])

    def test_writer_and_editor_use_google_news_for_search_and_body(self):
        for filename in (
            "sci-research-daily-news-writer.toml",
            "sci-research-daily-editor.toml",
        ):
            instructions = self.load_agent(filename)["developer_instructions"]
            self.assertIn("mcp__google_news__search_news", instructions)
            self.assertIn("mcp__google_news__get_news_article", instructions)
            self.assertIn("same MCP session", instructions)
            self.assertIn("access_status: full_text", instructions)
            self.assertIn("Never use Codex native WebSearch", instructions)

    def test_skill_has_exact_scope_templates(self):
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Default: `Use google_news.search_news for news published on {date}", skill)
        self.assertIn("China: `Use google_news.search_news on foreign media only", skill)
        self.assertIn("Europe: `Use google_news.search_news", skill)
        self.assertIn("Do not append any other search", skill)

    def test_skill_requires_current_task_google_news_tools(self):
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("mcp__google_news__search_news", skill)
        self.assertIn("mcp__google_news__get_news_article", skill)
        self.assertIn("start a new Codex task", skill)


if __name__ == "__main__":
    unittest.main()
