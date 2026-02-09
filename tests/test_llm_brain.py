from engine.llm_brain import LLMBrain


def test_llm_brain_init_no_key():
    """LLM Brain should gracefully handle no API key."""
    brain = LLMBrain()
    assert brain.provider == "none"
    assert brain.is_available is False


def test_llm_brain_generate_no_client():
    """Generate should return None when no client is available."""
    brain = LLMBrain()
    result = brain.generate("Say hello")
    assert result is None


def test_llm_brain_generate_health_no_client():
    """Health reminder generation should return None without client."""
    brain = LLMBrain()
    result = brain.generate_health_reminder("water", 14)
    assert result is None


def test_llm_brain_summarize_no_client():
    """Headline summarization should return None without client."""
    brain = LLMBrain()
    result = brain.summarize_headline("Breaking: Markets surge")
    assert result is None


def test_llm_brain_curate_no_client():
    """News curation should return None without client."""
    brain = LLMBrain()
    result = brain.curate_news(["Headline 1", "Headline 2"])
    assert result is None


def test_llm_brain_personalize_short_message():
    """Short love notes should pass through unchanged."""
    brain = LLMBrain()
    result = brain.personalize_love_note("I love you")
    assert result == "I love you"


def test_llm_brain_personalize_long_message():
    """Long love notes should be truncated."""
    brain = LLMBrain()
    long_msg = "A" * 100
    result = brain.personalize_love_note(long_msg)
    assert len(result) <= 80
    assert result.endswith("...")


def test_llm_brain_config_loading():
    """Config should be loaded properly."""

    class FakeConfig:
        def get(self, section, key=None):
            if section == "llm":
                return {
                    "provider": "openai",
                    "anthropic_api_key": "",
                    "openai_api_key": "",
                    "model": "gpt-4o-mini"
                }
            return {}

    brain = LLMBrain(config=FakeConfig())
    assert brain.provider in ("openai", "none")  # "none" because key is empty
    assert brain.model == "gpt-4o-mini"
