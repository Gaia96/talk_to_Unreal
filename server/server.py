"""Local retrieval agent: e5 (retrieve) -> cross-encoder (rerank) -> decision.

POST /query {"text": "..."} -> status ok | ambiguous | out_of_scope (+ id, params, reply when ok).

Run:  uvicorn server:app --port 8000
Env:  RERANKER   BAAI/bge-reranker-v2-m3 (default, strong) | cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (light baseline)
      T_ACCEPT   min reranker score (0..1) to accept     (tune on your test set!)
      MARGIN     min gap between 1st and 2nd entry       (tune on your test set!)
      TOP_K      candidates passed to the reranker
"""
import json
import os
import time
from pathlib import Path

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import CrossEncoder, SentenceTransformer, util

HERE = Path(__file__).parent
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EMBEDDER = os.getenv("EMBEDDER", "intfloat/multilingual-e5-large")
RERANKER = os.getenv("RERANKER", "BAAI/bge-reranker-v2-m3")
T_ACCEPT = float(os.getenv("T_ACCEPT", "0.4"))
MARGIN = float(os.getenv("MARGIN", "0.05"))
TOP_K = int(os.getenv("TOP_K", "10"))

# ---- load models once ------------------------------------------------------
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32  # fp16 straight from load: fp32 first would not fit 6 GB
embedder = SentenceTransformer(EMBEDDER, device=DEVICE, model_kwargs={"torch_dtype": DTYPE})
reranker = CrossEncoder(RERANKER, device=DEVICE, activation_fn=torch.nn.Sigmoid(), model_kwargs={"torch_dtype": DTYPE})

# ---- load + index the catalog (embedded ONCE, here) ------------------------
catalog = json.loads((HERE / "catalog" / "catalog.json").read_text(encoding="utf-8"))
rows = [(i, d) for i, e in enumerate(catalog) for d in e["descriptions"]]  # one row per description
row_emb = embedder.encode(
    [f"passage: {d}" for _, d in rows], convert_to_tensor=True, normalize_embeddings=True
)

app = FastAPI()


class Query(BaseModel):
    text: str


def resolve(text: str):
    """Return (ranked entries [(entry_idx, score, matched_desc)], timings)."""
    t0 = time.perf_counter()
    q = embedder.encode(f"query: {text}", convert_to_tensor=True, normalize_embeddings=True)
    sims = util.cos_sim(q, row_emb)[0]
    order = torch.argsort(sims, descending=True).tolist()
    cand = order[:TOP_K]
    t1 = time.perf_counter()
    scores = reranker.predict([(text, rows[r][1]) for r in cand])
    t2 = time.perf_counter()
    best = {}  # entry_idx -> (score, desc)
    for r, s in zip(cand, scores):
        ei, desc = rows[r]
        if ei not in best or s > best[ei][0]:
            best[ei] = (float(s), desc)
    ranked = sorted(((ei, s, d) for ei, (s, d) in best.items()), key=lambda x: -x[1])
    return ranked, {"retrieve_ms": round((t1 - t0) * 1000, 1), "rerank_ms": round((t2 - t1) * 1000, 1)}


@app.get("/health")
def health():
    return {"device": DEVICE, "embedder": EMBEDDER, "reranker": RERANKER, "entries": len(catalog), "rows": len(rows)}


@app.post("/query")
def query(q: Query):
    ranked, timing = resolve(q.text)
    top_i, top_s, top_d = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    margin = top_s - second[1] if second else top_s

    if top_s < T_ACCEPT:
        status = "out_of_scope"
    elif margin < MARGIN:
        status = "ambiguous"
    else:
        status = "ok"

    e = catalog[top_i]
    out = {
        "status": status, "score": round(top_s, 4), "margin": round(margin, 4),
        "alternatives": [{"id": catalog[ei]["id"], "title": catalog[ei]["title"]} for ei, _, _ in ranked[:3]],
        "timing": timing,
    }
    if status == "ok":
        out.update(id=e["id"], params=e["params"], reply=e["reply"])
    return out
