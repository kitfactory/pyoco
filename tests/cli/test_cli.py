import json
import pytest
import sys
from unittest.mock import patch, MagicMock
from pyoco.cli.main import main
from pyoco.schemas.config import PyocoConfig, FlowConfig
from pyoco.core.models import Task

# Mock config
@pytest.fixture
def mock_config():
    return PyocoConfig(
        version=1,
        flows={
            "main": FlowConfig(graph="A >> B", defaults={"x": "1"})
        },
        tasks={
            "A": MagicMock(callable="mod:A", inputs={}),
            "B": MagicMock(callable="mod:B", inputs={})
        },
        runtime=None
    )

def test_cli_check_valid(mock_config):
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=mock_config), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("sys.argv", ["pyoco", "check", "--config", "dummy.yaml"]):
        
        loader = MockLoader.return_value
        loader.tasks = {
            "A": Task(func=lambda: None, name="A"),
            "B": Task(func=lambda: None, name="B")
        }
        
        # Should exit 0 (or just return if we didn't mock sys.exit, but main calls sys.exit on error)
        # Since we print report and don't exit on success, it should finish.
        main()

def test_cli_check_cycle(mock_config):
    mock_config.flows["main"].graph = "A >> B >> A" # Cycle
    
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=mock_config), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("sys.argv", ["pyoco", "check", "--config", "dummy.yaml"]), \
         pytest.raises(SystemExit) as excinfo:
        
        loader = MockLoader.return_value
        t_a = Task(func=lambda: None, name="A")
        t_b = Task(func=lambda: None, name="B")
        loader.tasks = {"A": t_a, "B": t_b}
        
        main()
    
    assert excinfo.value.code == 1

def test_cli_check_dry_run_json(mock_config, capsys):
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=mock_config), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("sys.argv", ["pyoco", "check", "--config", "dummy.yaml", "--dry-run", "--json"]):
        
        loader = MockLoader.return_value
        loader.tasks = {
            "A": Task(func=lambda: None, name="A"),
            "B": Task(func=lambda: None, name="B")
        }
        
        main()
        out = capsys.readouterr().out
        json_payload = out[out.find("{"):]
        data = json.loads(json_payload)
        assert data["status"] == "ok"

def test_cli_check_dry_run_error(mock_config):
    mock_config.flows["main"].graph = "flow >> switch('$ctx.params.flag')[('*' >> A, '*' >> B)]"
    
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=mock_config), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("sys.argv", ["pyoco", "check", "--config", "dummy.yaml", "--dry-run"]), \
         pytest.raises(SystemExit) as excinfo:
        
        loader = MockLoader.return_value
        loader.tasks = {
            "A": Task(func=lambda: None, name="A"),
            "B": Task(func=lambda: None, name="B")
        }
        
        main()
    
    assert excinfo.value.code == 2

def test_cli_runs_inspect_json(capsys):
    fake_run = {
        "run_id": "abc",
        "flow_name": "main",
        "status": "COMPLETED",
        "tasks": {"t1": "SUCCEEDED"},
        "task_records": {"t1": {"state": "SUCCEEDED"}}
    }
    with patch("pyoco.cli.main.Client") as MockClient, \
         patch("sys.argv", ["pyoco", "runs", "inspect", "abc", "--json"]):
        MockClient.return_value.get_run.return_value = fake_run
        main()
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["run_id"] == "abc"

def test_cli_runs_logs_tail(capsys):
    fake_logs = {
        "run_status": "COMPLETED",
        "logs": [
            {"seq": 0, "task": "t1", "stream": "stdout", "text": "hello\n"},
            {"seq": 1, "task": "t1", "stream": "stderr", "text": "oops\n"}
        ]
    }
    with patch("pyoco.cli.main.Client") as MockClient, \
         patch("sys.argv", ["pyoco", "runs", "logs", "abc", "--tail", "1"]):
        MockClient.return_value.get_run_logs.return_value = fake_logs
        main()
        output = capsys.readouterr().out
        assert "oops" in output

def test_cli_run_params(mock_config):
    with patch("pyoco.cli.main.PyocoConfig.from_yaml", return_value=mock_config), \
         patch("pyoco.cli.main.TaskLoader") as MockLoader, \
         patch("pyoco.cli.main.Engine") as MockEngine, \
         patch("sys.argv", ["pyoco", "run", "--config", "dummy.yaml", "--param", "x=2", "--param", "y=3"]):
        
        loader = MockLoader.return_value
        loader.tasks = {
            "A": Task(func=lambda: None, name="A"),
            "B": Task(func=lambda: None, name="B")
        }
        
        main()
        
        engine = MockEngine.return_value
        # Check if run called with updated params
        args, kwargs = engine.run.call_args
        flow, params = args
        assert params["x"] == "2"
        assert params["y"] == "3"

def test_cli_plugins_list(capsys):
    plugin_reports = [
        {
            "name": "demo",
            "module": "pkg.module",
            "value": "pkg.module:hook",
            "tasks": [
                {"name": "foo", "origin": "task_class", "warnings": [], "class": "VisionTask"}
            ],
            "warnings": [],
        }
    ]
    with patch("pyoco.cli.main._collect_plugin_reports", return_value=plugin_reports), \
         patch("sys.argv", ["pyoco", "plugins", "list"]):
        main()
        output = capsys.readouterr().out
        assert "demo" in output
        assert "foo" in output
