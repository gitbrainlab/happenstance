import os

from happenstance.env import load_project_env


def test_load_project_env_sets_alias_without_overriding(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GOOGLE_API_KEY=local-google-key",
                "RESTAURANT_SOURCE=google_places",
                "EXISTING_VALUE=from-file",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("RESTAURANT_SOURCE", raising=False)
    monkeypatch.setenv("EXISTING_VALUE", "from-env")

    load_project_env(env_file)

    assert os.environ["GOOGLE_API_KEY"] == "local-google-key"
    assert os.environ["GOOGLE_PLACES_API_KEY"] == "local-google-key"
    assert os.environ["RESTAURANT_SOURCE"] == "google_places"
    assert os.environ["EXISTING_VALUE"] == "from-env"


def test_load_project_env_sets_alias_without_env_file(monkeypatch, tmp_path):
    missing_env_file = tmp_path / ".env"
    monkeypatch.setenv("GOOGLE_API_KEY", "ci-google-key")
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)

    load_project_env(missing_env_file)

    assert os.environ["GOOGLE_PLACES_API_KEY"] == "ci-google-key"
