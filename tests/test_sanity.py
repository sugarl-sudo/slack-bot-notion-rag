from slack_bot_notion_rag.config import Settings
from slack_bot_notion_rag.slack_app import clean_user_question


def test_settings_split_ids_and_defaults(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SLACK_SIGNING_SECRET=secret\n"
        "SLACK_BOT_TOKEN=token\n"
        "NOTION_API_TOKEN=n-token\n"
        "OPENAI_API_KEY=oai\n"
        "NOTION_ROOT_PAGE_IDS=[\"page1\", \"page2\"]\n"
    )

    settings = Settings(_env_file=env_file)

    assert settings.notion_root_page_ids == ["page1", "page2"]
    assert settings.chunk_size == 800
    assert settings.chunk_overlap == 200
    assert settings.retriever_top_k == 4


def test_clean_user_question_removes_mentions():
    raw_text = "<@U12345> こんにちは、環境構築の手順を教えてください"

    assert clean_user_question(raw_text) == "こんにちは、環境構築の手順を教えてください"
