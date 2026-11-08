"""Demo script: run the demo turns (IT + EN) against a running server and print what Unreal should receive.

  python eval/demo_script.py            # server on http://127.0.0.1:8000

Each row: sentence -> expected (id, or status for ambiguous/out_of_scope) vs. actual. Exit code 1 if any row differs.
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:8000/query"
# (language, sentence, expected id | "ambiguous" | "out_of_scope", demo turn)
TURNS = [
    ("EN", "Make the cube red.", "cube_red", "1 action"),
    ("EN", "Now turn it blue.", "cube_blue", "1 paraphrase"),
    ("EN", "Paint the cube green, please.", "cube_green", "1 action"),
    ("EN", "Set the cube back to white.", "cube_white", "1 action"),
    ("EN", "Order me a pizza.", "out_of_scope", "2 out of scope"),
    ("EN", "Make the cube bigger.", "out_of_scope", "2 near miss"),
    ("IT", "Rendi il cubo rosso.", "cube_red", "1 action"),
    ("IT", "Colora il cubo di verde.", "cube_green", "1 action"),
    ("IT", "Ordinami una pizza.", "out_of_scope", "2 out of scope"),
]


def ask(text):
    req = urllib.request.Request(URL, json.dumps({"text": text}).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


bad = 0
print(f"{'':2} {'sentence':46} {'expected':22} {'got':22} {'score':>6} {'margin':>6}  turn")
for lang, text, expected, turn in TURNS:
    r = ask(text)
    got = r["id"] if r["status"] == "ok" else r["status"]
    ok = got == expected
    bad += not ok
    print(f"{lang} {text[:46]:46} {expected:22} {got:22} {r['score']:6.3f} {r['margin']:6.3f}  {turn}{'' if ok else '   <-- DIFFERS'}")
    if not ok:
        print("     top-3:", ", ".join(a["id"] for a in r["alternatives"]))
print(f"\n{len(TURNS) - bad}/{len(TURNS)} as expected")
sys.exit(1 if bad else 0)
