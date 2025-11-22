import pytest
from unittest.mock import patch
from pyoco.trace.console import ConsoleTraceBackend

def test_console_trace_cute():
    backend = ConsoleTraceBackend(style="cute")
    
    with patch("builtins.print") as mock_print:
        backend.on_node_start("A")
        mock_print.assert_called_with("🏃 start node=A")
        
        backend.on_node_end("A", 100.0)
        mock_print.assert_called_with("✅ done node=A (100.00 ms)")
        
        backend.on_node_transition("A", "B")
        mock_print.assert_called_with("🐇 A -> B")

def test_console_trace_plain():
    backend = ConsoleTraceBackend(style="plain")
    
    with patch("builtins.print") as mock_print:
        backend.on_node_start("A")
        mock_print.assert_called_with("INFO pyoco start node=A")
