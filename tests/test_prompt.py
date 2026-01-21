from pathlib import Path


def load_prompt_contents() -> str:
    prompt_path = Path("app/prompts/stock_analyzer_prompt.md")
    return prompt_path.read_text(encoding="utf-8")


def test_prompt_mentions_score_total():
    prompt = load_prompt_contents()
    assert "score_total" in prompt
