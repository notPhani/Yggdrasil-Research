from pathlib import Path
from rich.console import Console
from ygg.tui import ForensicsTUI

def test_tui_renders_without_exception(tmp_path):
    # Test on real data directory
    real_data = Path("data")
    if (real_data / "cases" / "2025-01-27.json").exists():
        console = Console(record=True, width=120)
        tui = ForensicsTUI(real_data, day="2025-01-27", console=console)
        
        # Test individual component renders
        header = tui.render_header()
        assert header is not None
        
        tree = tui.render_tree()
        assert tree is not None
        
        rivals = tui.render_rivals()
        assert rivals is not None
        
        evidence = tui.render_evidence()
        assert evidence is not None
        
        verdicts = tui.render_verdicts()
        assert verdicts is not None
        
        # Test full dashboard render
        tui.render_full_dashboard()
        output = console.export_text()
        assert "YGGDRASIL MARKET EVENT FORENSICS" in output
        assert "2025-01-27" in output                  # renders the case; the result itself is not asserted
        assert "[ROOT] BOT" in output

def test_tui_handles_missing_case(tmp_path):
    console = Console(record=True, width=120)
    tui = ForensicsTUI(tmp_path, day="nonexistent", console=console)
    tui.render_full_dashboard()
    output = console.export_text()
    assert "YGGDRASIL" in output
