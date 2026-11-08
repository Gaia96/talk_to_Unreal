import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server
tests = json.loads((Path(__file__).parent / "testset.json").read_text(encoding="utf-8"))
top1 = 0; n = 0
for t in tests:
    ranked, _ = server.resolve(t["q"])
    ids = [server.catalog[ei]["id"] for ei, _, _ in ranked[:2]]
    s1 = ranked[0][1]; s2 = ranked[1][1] if len(ranked) > 1 else 0
    if t["gold"]:
        n += 1; top1 += ids[0] == t["gold"]
    mark = "OK " if ids[0] == t["gold"] else ("oos" if not t["gold"] else "BAD")
    print(f"{mark} s1={s1:.3f} s2={s2:.3f} m={s1-s2:.3f} | {t['q'][:45]:45} | gold={t['gold']} top={ids[0]} 2nd={ids[1]}")
print(f"rerank top-1 (no thresholds): {top1}/{n}")
