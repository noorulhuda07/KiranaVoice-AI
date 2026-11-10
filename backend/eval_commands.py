"""Runs 20 representative commands against a fresh demo DB and prints pass rate.
Usage (from backend/, venv active):  python eval_commands.py
Put the numbers it prints into your submission/demo."""
import os, time
if os.path.exists("kirana.db"): os.remove("kirana.db")
from app.db import init_db, SessionLocal
from app import engine as eng
from app.parser import parse
init_db()
CASES = [
 ("chhota maggi ke 10 packet add karo", "ok"), ("chhota maggi kitna hai", "ok"),
 ("5 packet chhota maggi becha", "ok"), ("bada maggi ke 3 packet bech do", "ok"),
 ("maggi ke 5 packet add karo", "clarify"), ("sell 50 packet chhota maggi", "rejected"),
 ("2 packet pizza becha", "clarify"), ("chawal 2.5 kg becha", "ok"), ("rice kitna hai", "ok"),
 ("cheeni kitni hai", "ok"), ("tel 2 litre becha", "ok"), ("tel 2 kg becha", "clarify"),
 ("oil kitna hai", "ok"), ("low stock batao", "ok"), ("undo", "ok"),
 ("paanch kilo cheeni add karo", "ok"), ("sugar ke das kilo becha", "ok"),
 ("undo my last stock update", "ok"), ("chawal 150 kg add karo", "needs_confirmation"),
 ("kuch bhi random bolo", "clarify"),
]
passed, times = 0, []
with SessionLocal() as db:
    for text, want in CASES:
        t0 = time.perf_counter(); r = eng.execute(db, parse(text)); times.append(time.perf_counter() - t0)
        ok = r["status"] == want; passed += ok
        print(("PASS" if ok else "FAIL"), f"{text!r} -> {r['status']} (want {want}): {r['message']}")
print(f"\n{passed}/{len(CASES)} passed; avg engine time {1000*sum(times)/len(times):.1f} ms (excludes STT/TTS)")
