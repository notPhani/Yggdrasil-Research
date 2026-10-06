"""Feasibility check of the report's clingo template (Section 14.1) on illustrative DeepSeek facts."""
import clingo
PROGRAM = r"""
% ---- illustrative facts (what claim extraction + Engine 2 would emit) ----
% Yggdrasil's own measurements (tier 0)
reported(m1, ygg, occurred(ev_r1), d0120).            reported(m2, ygg, occurred(ev_surge), d0126).
% text-derived reports
reported(r02, arxiv_v3, excludes_prior(v3), d1227).   reported(r31, outlet_a, all_in_cost_5m(v3), d0126).
reported(r40, outlet_b, smuggled_chips(deepseek), d0126). reported(r41, outlet_c, no_diversion(deepseek), d0126).
contrary(all_in_cost_5m(v3), excludes_prior(v3)).     contrary(smuggled_chips(deepseek), no_diversion(deepseek)).
contrary(X, Y) :- contrary(Y, X).
tier(ygg, 0). tier(arxiv_v3, 1). tier(outlet_a, 2). tier(outlet_b, 2). tier(outlet_c, 2).
independent(R1, R2) :- reported(R1, S1, _, _), reported(R2, S2, _, _), S1 != S2.
% hypotheses (from the search's explanation trees)
trigger(h1, ev_r1).  before(ev_r1, move).                       % R1 efficiency shock: no signature fact -> unproven
trigger(h3, ev_r1).  schema_refuter(h3, excludes_prior(v3)).     % "$5.6M all-in"
trigger(h4, ev_chips). before(ev_chips, move). signature_ok(h4). % chip smuggling
holds(occurred(ev_chips)) :- holds(smuggled_chips(deepseek)).
schema_refuter(h4, no_diversion(deepseek)).
trigger(h6, ev_surge). before(ev_surge, move). signature_ok(h6). % attention cascade
% ---- template (report Section 14.1) ----
ok(R)       :- reported(R, _, _, _), not defeated(R).
holds(L)    :- reported(R, _, L, _), ok(R).
defeated(R) :- reported(R, S, L, _), contrary(L, L2), reported(R2, S2, L2, _), ok(R2),
               independent(R, R2), tier(S, K), tier(S2, K2), K2 <= K.
refuted(H)  :- schema_refuter(H, L), holds(L).
expl(H)     :- trigger(H, E), holds(occurred(E)), before(E, move), signature_ok(H), not refuted(H).
hyp(H) :- trigger(H, _).
#show expl/1. #show refuted/1. #show hyp/1.
"""
def models(mode):
    ctl = clingo.Control(["0", f"--enum-mode={mode}"] if mode != "all" else ["0"])
    ctl.add("base", [], PROGRAM); ctl.ground([("base", [])])
    out = []
    with ctl.solve(yield_=True) as h:
        for m in h: out.append({str(s) for s in m.symbols(shown=True)})
    return out
allm = models("all"); brave = models("brave")[-1]; cautious = models("cautious")[-1]
print(f"stable models: {len(allm)}")
for i, m in enumerate(allm): print(f"  model {i+1}:", sorted(x for x in m if not x.startswith('hyp')))
hyps = sorted(x[4:-1] for x in cautious if x.startswith("hyp("))
print(f"\n{'H':4s} {'bIN':>4s} {'cIN':>4s} {'bOUT':>5s} {'cOUT':>5s}  verdict")
for h in hyps:
    bIN, cIN = f"expl({h})" in brave, f"expl({h})" in cautious
    bOUT, cOUT = f"refuted({h})" in brave, f"refuted({h})" in cautious
    v = "SUPPORTED" if cIN else "CONTRADICTED" if cOUT else "UNRESOLVED" if bOUT else "CONSISTENT-BUT-UNPROVEN"
    print(f"{h:4s} {int(bIN):4d} {int(cIN):4d} {int(bOUT):5d} {int(cOUT):5d}  {v}")
