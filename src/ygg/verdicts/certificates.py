"""Tamper-evident forensic evidence certificates generated from Clingo ASP models."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EvidenceCertificate:
    day: str
    tau_star: str
    hypothesis_id: str
    verdict: str
    brave_consequences: list[str]
    cautious_consequences: list[str]
    inputs_hash: str
    certificate_id: str


def generate_certificate(day: str, tau_star: str, hid: str, verdict: str, brave: list[str], cautious: list[str]) -> EvidenceCertificate:
    payload = f"{day}::{tau_star}::{hid}::{verdict}::{sorted(brave)}::{sorted(cautious)}"
    inp_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    cert_id = f"CERT-{inp_hash[:16].upper()}"
    return EvidenceCertificate(
        day=day,
        tau_star=tau_star,
        hypothesis_id=hid,
        verdict=verdict,
        brave_consequences=sorted(brave),
        cautious_consequences=sorted(cautious),
        inputs_hash=inp_hash,
        certificate_id=cert_id
    )


def export_certificates(data_dir: Path, day: str, certs: list[EvidenceCertificate]) -> Path:
    out = Path(data_dir) / "cases" / f"{day}_certificates.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([asdict(c) for c in certs], indent=2), encoding="utf-8")
    return out
