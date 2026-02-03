import pytest

from pyoco.schemas.config import PyocoConfig


def test_from_yaml_allows_minimal_config(tmp_path):
    path = tmp_path / "flow.yaml"
    path.write_text("version: 1\ntasks: {}\n")
    config = PyocoConfig.from_yaml(str(path))
    assert config.version == 1


def test_from_yaml_rejects_discovery_key(tmp_path):
    path = tmp_path / "flow.yaml"
    path.write_text("version: 1\ntasks: {}\ndiscovery: {}\n")
    with pytest.raises(ValueError, match=r"(?i)discovery"):
        PyocoConfig.from_yaml(str(path))


def test_from_yaml_rejects_flows_key(tmp_path):
    path = tmp_path / "flow.yaml"
    path.write_text("version: 1\nflows: {}\ntasks: {}\n")
    with pytest.raises(ValueError, match=r"(?i)flows"):
        PyocoConfig.from_yaml(str(path))
