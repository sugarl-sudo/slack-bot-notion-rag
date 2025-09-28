from slack_bot_notion_rag.config import Settings


def test_settings_split_ids(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SLACK_SIGNING_SECRET=secret\n"
        "SLACK_BOT_TOKEN=token\n"
        "NOTION_API_TOKEN=n-token\n"
        "OPENAI_API_KEY=oai\n"
        "NOTION_DATABASE_IDS=db1, db2\n"
    )

    settings = Settings(_env_file=env_file)

    assert settings.notion_database_ids == ["db1", "db2"]
