"""The shipped fixture verifies offline: every network call is blocked, and every check must pass. A tampered
copy must fail, so the verifier is not vacuous."""
import json
import shutil
import socket
from pathlib import Path

import pytest

from ygg.verify import verify

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "replay"
pytestmark = pytest.mark.skipif(not FIXTURE.exists(), reason="fixtures/replay not present")


@pytest.fixture
def no_network(monkeypatch):
    def blocked(*a, **k):
        raise OSError("network disabled in this test")
    for name in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, name, blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def test_fixture_verifies_offline(no_network):
    checks = verify(FIXTURE)
    names = {(c.case, c.name) for c in checks}
    for day in ("2025-01-13", "2025-01-27"):
        for n in ("observer", "search", "verdicts", "placebo", "serpapi"):
            assert (day, n) in names
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]


def test_tampered_fixture_fails(tmp_path, no_network):
    work = tmp_path / "replay"
    shutil.copytree(FIXTURE, work)
    p = work / "cases" / "2025-01-13.json"
    d = json.loads(p.read_text())
    d["search"]["groups"][0]["best"]["cost_mnats"] -= 1                       # claim a cheaper optimum
    h = d["verdicts"]["hypotheses"][1]["hid"]
    d["verdicts"]["P_pre"]["verdicts"][h] = "SUPPORTED"                         # and a verdict the evidence doesn't give
    d["placebo"]["p_emp"] = 0.01                                                # and a significance it never had
    p.write_text(json.dumps(d))
    bad = {c.name for c in verify(work, ["2025-01-13"]) if not c.ok}
    assert {"manifest", "search", "verdicts", "placebo"} <= bad
