"""Stage 3 of the claim cascade (decision 6.13'): verify, never generate.

For a candidate (subject, predicate, value) and a sentence from an archived page, an NLI cross-encoder decides
whether the sentence entails a templated hypothesis. GLiNER checks that the subject really is an entity of
an allowed type in that sentence. The model only answers about spans that deterministic code found, so it
cannot add knowledge. theta is fitted on stage-2 silver labels (A9 style: no hand labels). With pinned
weights, CPU inference and a fixed thread count, the output is replay-deterministic, and it is archived too (D5).
Models: cross-encoder/nli-deberta-v3-small and urchade/gliner_small-v2.1 (both Apache-2.0). GLiREL is
omitted because its model card declares no license.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NER_MODEL = "urchade/gliner_small-v2.1"
ENTITY_LABELS = ["organization", "company", "AI model", "product", "person", "government body"]
TEMPLATES = {
    "released": "{s} released a new AI model.",
    "cost_of": "Training {s} cost about {v} dollars.",
    "capability_parity": "{s} performs as well as leading AI models.",
    "ranks_top": "{s} became the top app in the app store.",
    "denies": "{s} denied the allegation.",
    "alleges": "Someone alleged wrongdoing by {s}.",
    "restricts_exports": "The government restricted chip exports.",
    "guides_capex": "{s} plans to spend {v} dollars on AI infrastructure.",
}


@lru_cache(maxsize=1)
def _nli():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    torch.set_num_threads(1)                       # D3: fixed thread count for reproducible reductions
    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).eval()
    labels = [model.config.id2label[i].lower() for i in range(model.config.num_labels)]
    return tok, model, labels


@lru_cache(maxsize=1)
def _ner():
    from gliner import GLiNER

    return GLiNER.from_pretrained(NER_MODEL)


def entail_probs(pairs: list[tuple[str, str]]) -> np.ndarray:
    """Rows of (P(contradiction), P(entailment), P(neutral)) in that order, whatever the model's label order."""
    import torch

    if not pairs:
        return np.zeros((0, 3))
    tok, model, labels = _nli()
    out = []
    with torch.no_grad():
        for i in range(0, len(pairs), 16):
            batch = pairs[i:i + 16]
            enc = tok([p for p, _ in batch], [h for _, h in batch], return_tensors="pt", padding=True, truncation=True, max_length=256)
            probs = torch.softmax(model(**enc).logits, dim=-1).numpy()
            order = [labels.index("contradiction"), labels.index("entailment"), labels.index("neutral")]
            out.append(probs[:, order])
    return np.concatenate(out)


def subject_is_entity(sentence: str, subject_name: str, threshold: float = 0.4) -> bool:
    ents = _ner().predict_entities(sentence, ENTITY_LABELS, threshold=threshold)
    s = subject_name.lower()
    return any(s in e["text"].lower() or e["text"].lower() in s for e in ents)


def fit_theta(silver_pairs: list[tuple[str, str]], silver_labels: list[int], grid=np.linspace(0.3, 0.95, 14)) -> float:
    """Smallest entailment threshold whose precision on the rule-stage silver labels is >= 0.9 (else 0.9)."""
    if not silver_pairs:
        return 0.9
    p = entail_probs(silver_pairs)[:, 1]
    y = np.array(silver_labels)
    for th in grid:
        pred = p >= th
        if pred.sum() and (y[pred] == 1).mean() >= 0.9:
            return float(th)
    return 0.9


def verify(sentence: str, predicate: str, subject: str, value: str = "", theta: float = 0.7) -> tuple[bool, float, float]:
    """(accepted, P(entail), P(contradict)) for one templated claim against one sentence."""
    hyp = TEMPLATES[predicate].format(s=subject, v=value)
    pc, pe, _ = entail_probs([(sentence, hyp)])[0]
    return bool(pe >= theta), float(pe), float(pc)
