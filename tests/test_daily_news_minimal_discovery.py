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
        self.assertIn("Codex native WebSearch", instructions)
        self.assertIn("Blocked or unavailable articles remain", instructions)
        self.assertIn("Raw or Markdown `news.google.com` URLs", instructions)
        self.assertIn("max_results=10", instructions)
        self.assertIn("one refined", instructions)
        self.assertIn("Return at most 10 results", instructions)
        self.assertIn("exact duplicate URLs", instructions)
        self.assertIn("best-effort", instructions)
        self.assertIn("near-duplicates", instructions)

    def test_scanner_url_presentation_is_not_a_gate(self):
        schema = (
            ROOT / "skills" / "daily-news-intelligence" / "references" / "schemas.md"
        ).read_text(encoding="utf-8")
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("raw `news.google.com` URL or a Markdown link is valid", schema)
        self.assertIn("Do not retry or stop for schema, URL, access, or quality problems", skill)
        self.assertIn("Preserve it verbatim", schema)

    def test_verifier_deduplicates_and_selects_three_to_six(self):
        agent = self.load_agent("sci-research-news-verifier.toml")
        self.assertEqual(agent["model"], "gpt-5.6-terra")
        self.assertEqual(agent["model_reasoning_effort"], "high")
        instructions = agent["developer_instructions"]
        self.assertIn("first report of each event", instructions)
        self.assertIn("DROP_DUPLICATE", instructions)
        self.assertIn("DROP_NOT_SELECTED", instructions)
        self.assertIn("more than 6 unique events", instructions)
        self.assertIn("below `min_per_category`", instructions)
        self.assertIn("Do not search, fetch, verify, score sources", instructions)

    def test_verifier_schema_has_bounded_selection_arithmetic(self):
        schema = (
            ROOT / "skills" / "daily-news-intelligence" / "references" / "schemas.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Mode: deduplicate-and-select", schema)
        self.assertIn(
            "Input count = Kept count + Duplicate count + Not-selected count", schema
        )
        self.assertIn("DROP_NOT_SELECTED", schema)
        self.assertIn("at most 6 events", schema)
        self.assertIn("duplicate chains are forbidden", schema)
        self.assertIn("Mode: mechanical-fallback", schema)
        self.assertIn("Continue downstream", schema)

    def test_skill_caps_scanner_and_final_category_counts(self):
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("max_per_category=6", skill)
        self.assertIn("cap at 10", skill)
        self.assertIn("Require `1 <= min_per_category <= 6`", skill)
        self.assertIn("an `unavailable` zero-candidate block", skill)
        self.assertIn("Never retry or stop for Verifier schema defects", skill)
        self.assertIn("`mechanical-fallback`", skill)
        self.assertIn("empty-facts fallback", skill)
        self.assertIn("FORMAT_WARNING", skill)
        self.assertIn("A missing language never blocks another", skill)

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
        self.assertIn("pass exactly one sentence", skill)

    def test_skill_requires_current_task_google_news_tools(self):
        skill = (ROOT / "skills" / "daily-news-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("mcp__google_news__search_news", skill)
        self.assertIn("mcp__google_news__get_news_article", skill)
        self.assertIn("start a new Codex task", skill)


if __name__ == "__main__":
    unittest.main()
