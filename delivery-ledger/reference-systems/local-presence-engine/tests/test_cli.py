import os
import subprocess
import sys
from pathlib import Path


def test_cli_runs_deterministic_synthetic_scenario(tmp_path: Path) -> None:
    db = tmp_path / "demo.db"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "local_presence.cli", "--db", str(db)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "entry-001 -> VISIT_OPENED" in result.stdout
    assert "entry-001 duplicate -> VISIT_OPENED (idempotent)" in result.stdout
    assert "entry-002 -> ANOMALY_RECORDED: ENTRY_WHILE_OPEN" in result.stdout
    assert "exit-001 -> VISIT_CLOSED" in result.stdout
    assert "exit-002 -> ANOMALY_RECORDED: UNMATCHED_EXIT" in result.stdout
    assert "final visits: 1 closed" in result.stdout
    assert "anomalies: 2" in result.stdout
