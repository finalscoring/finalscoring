from typer.testing import CliRunner

from finalscoring_worker.cli import app


def test_ping() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["ping"])

    assert result.exit_code == 0
    assert "pong" in result.stdout
