import json
import pytest
from unittest.mock import patch
from pyoco.cli.main import main


def test_cli_plugins_lint_success(capsys):
    reports = [
        {
            "name": "demo",
            "module": "pkg.module",
            "value": "pkg.module:hook",
            "tasks": [{"name": "foo", "origin": "task_class", "warnings": [], "class": "VisionTask"}],
            "warnings": [],
        }
    ]
    with patch("pyoco.cli.main._collect_plugin_reports", return_value=reports), \
         patch("sys.argv", ["pyoco", "plugins", "lint"]):
        main()
        output = capsys.readouterr().out
        assert "look good" in output


def test_cli_plugins_lint_failure_json():
    reports = [
        {
            "name": "demo",
            "module": "pkg.module",
            "value": "pkg.module:hook",
            "tasks": [{"name": "bar", "origin": "callable", "warnings": ["callable warning"], "class": "CallablePluginTask"}],
            "warnings": ["no tasks registered"],
        }
    ]
    with patch("pyoco.cli.main._collect_plugin_reports", return_value=reports), \
         patch("sys.argv", ["pyoco", "plugins", "lint", "--json"]), \
         pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
