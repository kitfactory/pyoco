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
