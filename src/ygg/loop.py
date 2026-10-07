"""The window loop (decision 0.4): one process steps window by window through the stages in a fixed order.

There is no message bus. A stage is any object with `step(t, inputs) -> outputs`. The loop gives
each stage only the records whose time falls inside window t (D7). The `causality_violations`
harness checks that property for any pipeline: scrambling every input after window t must leave
every output up to t bit-identical.
"""
from __future__ import annotations

import hashlib
import pickle
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


class Stage(Protocol):
    name: str

    def step(self, t: int, inputs: Any) -> Any: ...


@dataclass
class WindowLoop:
    stages: Sequence[Stage]
    outputs: dict[int, dict[str, Any]] = field(default_factory=dict)

    def run(self, windows: Iterable[int], source: Callable[[int], Any]) -> dict[int, dict[str, Any]]:
        """source(t) returns the records that arrived in window t, and only those (D7)."""
        for t in windows:
            carry = source(t)
            per_stage: dict[str, Any] = {}
            for stage in self.stages:
                carry = stage.step(t, carry)
                per_stage[stage.name] = carry
            self.outputs[t] = per_stage
        return self.outputs


def digest(obj: Any) -> str:
    """Stable digest of a picklable output (protocol fixed); used to compare runs bit for bit."""
    return hashlib.sha256(pickle.dumps(obj, protocol=5)).hexdigest()


def causality_violations(make_loop: Callable[[], WindowLoop], windows: Sequence[int],
                         source: Callable[[int], Any], perturbed_source: Callable[[int], Any], cut: int) -> list[int]:
    """Future-perturbation test (A2/D7). perturbed_source must equal source for t <= cut.

    Returns the windows <= cut whose outputs changed. A correct, causal pipeline returns [].
    """
    a = make_loop().run(windows, source)
    b = make_loop().run(windows, perturbed_source)
    return [t for t in windows if t <= cut and digest(a[t]) != digest(b[t])]
