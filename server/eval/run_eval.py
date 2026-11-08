"""Evaluate the pipeline in-process (no HTTP). Compares embedder-only vs embedder+reranker.

Run from the server folder:   python eval/run_eval.py
Set RERANKER / T_ACCEPT / MARGIN env vars to compare configurations.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402  (loads models + indexes the catalog)
import torch  # noqa: E402
from sentence_transformers import util  # noqa: E402

tests = json.loads((Path(__file__).parent / "testset.json").read_text(encoding="utf-8"))
in_scope = [t for t in tests if t["gold"]]
oos = [t for t in tests if not t["gold"]]

# --- stage 1 only: embedder (best row -> entry id) ---
hits_e5 = 0
for t in in_scope:
    q = server.embedder.encode(f"query: {t['q']}", convert_to_tensor=True, normalize_embeddings=True)
    best = int(torch.argmax(util.cos_sim(q, server.row_emb)[0]))
    hits_e5 += server.catalog[server.rows[best][0]]["id"] == t["gold"]

# --- full pipeline: retrieve + rerank + decision ---
hits_full = false_reject = ambiguous = 0
lat = []
for t in in_scope:
    t0 = time.perf_counter()
    r = server.query(server.Query(text=t["q"]))
    lat.append((time.perf_counter() - t0) * 1000)
    hits_full += r["status"] == "ok" and r["id"] == t["gold"]
    false_reject += r["status"] == "out_of_scope"
    ambiguous += r["status"] == "ambiguous"
oos_ok = sum(server.query(server.Query(text=t["q"]))["status"] == "out_of_scope" for t in oos)

n, m = len(in_scope), len(oos)
print(f"device={server.DEVICE} embedder={server.EMBEDDER} reranker={server.RERANKER}")
print(f"T_ACCEPT={server.T_ACCEPT} MARGIN={server.MARGIN} TOP_K={server.TOP_K}")
print(f"top-1 accuracy, e5 only          : {hits_e5}/{n}")
print(f"correct + accepted, e5 + rerank  : {hits_full}/{n}")
print(f"false-reject (in-scope refused)  : {false_reject}/{n}   ambiguous: {ambiguous}/{n}")
print(f"out-of-scope correctly refused   : {oos_ok}/{m}")
print(f"latency per query (ms)  median={sorted(lat)[len(lat)//2]:.0f}  max={max(lat):.0f}")
