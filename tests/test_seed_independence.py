"""Replay state must not depend on Python's string-hash seed. Before the fix, entity weights were summed in set
order, so two runs with different PYTHONHASHSEED gave different floats. Each run here is a separate process."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = f"""
import sys
sys.path.insert(0, {str(HERE)!r})
from test_engine2a import make, synth
windows, vecs = synth()
eng = make()
for t in range(60):
    eng.step(t, windows[t], vecs)
print(eng.state_hash())
"""


def _run(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    return subprocess.run([sys.executable, "-c", SCRIPT], env=env, capture_output=True, text=True, check=True).stdout.strip()


def test_state_hash_is_identical_across_hash_seeds():
    a, b = _run("1"), _run("2")
    assert a and a == b
