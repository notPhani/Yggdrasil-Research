import json
from ygg.verdicts.certificates import generate_certificate, export_certificates

def test_certificate_generation_and_export(tmp_path):
    cert = generate_certificate(
        day="2025-01-27",
        tau_star="2025-01-27T08:00:00+00:00",
        hid="h_deepseek",
        verdict="CONSISTENT-BUT-UNPROVEN",
        brave=["occurred(e1)", "supported(h1)"],
        cautious=["occurred(e1)"]
    )
    assert cert.certificate_id.startswith("CERT-")
    assert cert.verdict == "CONSISTENT-BUT-UNPROVEN"
    
    out_file = export_certificates(tmp_path, "2025-01-27", [cert])
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["certificate_id"] == cert.certificate_id
