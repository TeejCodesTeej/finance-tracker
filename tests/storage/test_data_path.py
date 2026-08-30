"""Unit tests for data path resolution precedence (ticket 3)."""

from pathlib import Path

from finance_tracker.storage.data_path import ENV_VAR, resolve_data_dir


def test_env_var_takes_precedence_over_everything(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('data_dir = "/from/config"\n')

    resolved = resolve_data_dir(env={ENV_VAR: "/from/env"}, home=tmp_path)

    assert resolved == Path("/from/env")


def test_env_var_expands_user(tmp_path: Path) -> None:
    resolved = resolve_data_dir(env={ENV_VAR: "~/somewhere"}, home=tmp_path)

    assert resolved == Path("~/somewhere").expanduser()


def test_config_file_used_when_env_var_unset(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('data_dir = "/from/config"\n')

    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == Path("/from/config")


def test_config_file_used_when_env_var_empty(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('data_dir = "/from/config"\n')

    resolved = resolve_data_dir(env={ENV_VAR: ""}, home=tmp_path)

    assert resolved == Path("/from/config")


def test_xdg_default_when_nothing_else_set(tmp_path: Path) -> None:
    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == tmp_path / ".local" / "share" / "finance-tracker"


def test_xdg_default_when_config_file_missing(tmp_path: Path) -> None:
    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == tmp_path / ".local" / "share" / "finance-tracker"


def test_xdg_default_when_config_file_malformed(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text("this is not valid toml [[[")

    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == tmp_path / ".local" / "share" / "finance-tracker"


def test_xdg_default_when_config_missing_data_dir_key(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('other_key = "irrelevant"\n')

    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == tmp_path / ".local" / "share" / "finance-tracker"


def test_xdg_default_when_config_data_dir_not_a_string(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text("data_dir = 5\n")

    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == tmp_path / ".local" / "share" / "finance-tracker"


def test_config_file_value_expands_user(tmp_path: Path) -> None:
    config_dir = tmp_path / ".config" / "finance-tracker"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('data_dir = "~/elsewhere"\n')

    resolved = resolve_data_dir(env={}, home=tmp_path)

    assert resolved == Path("~/elsewhere").expanduser()


def test_defaults_to_real_environment_and_home(monkeypatch) -> None:
    """No-arg call uses the real process environment and home dir."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/fake/home")))

    resolved = resolve_data_dir()

    assert resolved == Path("/fake/home/.local/share/finance-tracker")
