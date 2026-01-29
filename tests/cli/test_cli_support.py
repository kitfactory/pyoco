import pytest
from unittest.mock import patch

from pyoco.cli.main import main
from pyoco.schemas.config import PyocoConfig, DiscoveryConfig
from pyoco.core.exceptions import InvalidFormatError


def _dummy_config():
    return PyocoConfig(version=1, flows={}, tasks={}, discovery=DiscoveryConfig())


def test_cli_support_tasks_outputs(capsys):
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=_dummy_config()), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("pyoco.cli.main.SupportInfoService") as MockService, \
         patch("sys.argv", ["pyoco", "support", "tasks", "--config", "dummy.yaml"]):
        MockLoader.return_value.tasks = {}
        MockService.return_value.build.return_value = "support-output"
        main()
        output = capsys.readouterr().out
        assert "support-output" in output


def test_cli_support_invalid_format(capsys):
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=_dummy_config()), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("pyoco.cli.main.SupportInfoService") as MockService, \
         patch("sys.argv", ["pyoco", "support", "tasks", "--config", "dummy.yaml"]):
        MockLoader.return_value.tasks = {}
        MockService.return_value.build.side_effect = InvalidFormatError("xml")
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        output = capsys.readouterr().out
        assert "Invalid format" in output
