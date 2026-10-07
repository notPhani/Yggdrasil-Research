from dataclasses import dataclass, field

from ygg.loop import WindowLoop, causality_violations, digest


@dataclass
class Counter:
    """Toy stage with memory: an exponential trace of input counts (causal)."""
    name: str = "trace"
    z: float = 0.0

    def step(self, t, inputs):
        self.z = 0.8 * self.z + 0.2 * len(inputs)
        return round(self.z, 12)


@dataclass
class Peeker:
    """Deliberately leaky stage: reads the whole future through a shared reference (must be caught)."""
    future: dict = field(default_factory=dict)
    name: str = "leak"

    def step(self, t, inputs):
        return sum(len(v) for k, v in self.future.items() if k > t)


DATA = {t: ["x"] * (t % 5) for t in range(40)}


def src(t):
    return DATA[t]


def perturbed(t):
    return DATA[t] if t <= 20 else ["y"] * 7


def test_double_run_is_bit_identical():
    a = WindowLoop([Counter()]).run(range(40), src)
    b = WindowLoop([Counter()]).run(range(40), src)
    assert all(digest(a[t]) == digest(b[t]) for t in range(40))


def test_causal_pipeline_passes_future_perturbation():
    assert causality_violations(lambda: WindowLoop([Counter()]), range(40), src, perturbed, cut=20) == []


def test_leaky_pipeline_is_caught():
    shared = {"which": DATA}

    def make():
        return WindowLoop([Peeker(future=shared["which"])])

    def run_with(source_data):
        shared["which"] = source_data
        return make()

    a = run_with(DATA).run(range(40), src)
    pert = {t: (DATA[t] if t <= 20 else ["y"] * 7) for t in range(40)}
    b = run_with(pert).run(range(40), perturbed)
    assert any(digest(a[t]) != digest(b[t]) for t in range(21))
