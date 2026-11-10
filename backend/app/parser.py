"""Deterministic Hindi/English/Hinglish command parser. No LLM touches the database."""
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

NUM_WORDS = {"ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5,
             "chhe": 6, "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "bees": 20,
             "pachees": 25, "tees": 30, "chalis": 40, "pachas": 50, "sau": 100,
             "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "twenty": 20, "fifty": 50, "hundred": 100,
             "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7,
             "आठ": 8, "नौ": 9, "दस": 10, "बीस": 20, "पचास": 50, "सौ": 100}
UNITS = {"packet": "packet", "packets": "packet", "pkt": "packet", "pkts": "packet",
         "पैकेट": "packet", "kg": "kg", "kilo": "kg", "किलो": "kg", "kgs": "kg",
         "litre": "L", "liter": "L", "litres": "L", "l": "L", "लीटर": "L",
         "gram": "g", "g": "g", "piece": "piece", "pcs": "piece", "pc": "piece", "पीस": "piece"}
INTENTS = [  # order matters: first match wins
    ("UNDO", ["undo", "wapas", "वापस", "revert", "galti se", "cancel last"]),
    ("LOW_STOCK", ["low stock", "kam stock", "kya khatam", "khatam", "कम स्टॉक", "running out"]),
    ("SELL", ["sell", "sold", "becha", "bech", "becho", "bika", "बेचा", "बेच", "बिका", "sale"]),
    ("ADD_STOCK", ["add", "jodo", "jod", "daalo", "dalo", "badhao", "aaya", "aya", "received",
                   "जोड़", "जोड़ो", "डालो", "आया", "stock in", "purchase"]),
    ("CHECK_STOCK", ["kitna", "kitne", "kitni", "how much", "how many", "check", "stock",
                     "batao", "बताओ", "कितना", "कितने", "कितनी", "hai kya", "है"]),
]
STOP = set("ke ka ki ko me mein se hai hain karo kar do de dena dijiye please the of in to a an "
           "add sell sold becha bech becho bika check stock batao kitna kitne kitni how much many "
           "is are my last wala wali की के का को में से है हैं करो कर दो बताओ कितना कितने कितनी "
           "jodo jod daalo dalo badhao aaya aya received packet packets pkt pkts kg kilo litre "
           "liter l gram pcs piece units unit stock जोड़ो जोड़ डालो आया बेचा बेच बिका पैकेट किलो लीटर पीस".split())


@dataclass
class Command:
    intent: str
    product: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    transcript: str = ""


def _tokens(text: str):
    text = text.lower().replace(",", " ").replace("?", " ").replace("।", " ")
    text = re.sub(r"(\d)([a-zA-Z\u0900-\u097F])", r"\1 \2", text)
    return text.split()


def parse(transcript: str) -> Command:
    t = transcript.strip().lower()
    toks = _tokens(t)
    intent = "UNKNOWN"
    for name, keys in INTENTS:
        if any((k in t) if " " in k else (k in toks) for k in keys):
            intent = name
            break
    qty, unit, used = None, None, set()
    for i, tok in enumerate(toks):
        val = None
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            val = Decimal(tok)
        elif tok in NUM_WORDS and intent not in ("UNDO",):
            val = Decimal(NUM_WORDS[tok])
        if val is not None and qty is None:
            qty = val
            used.add(i)
            for j in (i + 1, i - 1):
                if 0 <= j < len(toks) and toks[j] in UNITS:
                    unit = UNITS[toks[j]]
                    used.add(j)
                    break
    if unit is None:
        for tok in toks:
            if tok in UNITS and len(tok) > 1:
                unit = UNITS[tok]
    words = [w for i, w in enumerate(toks) if i not in used and w not in STOP and w not in UNITS]
    product = " ".join(words) or None
    if intent in ("UNDO", "LOW_STOCK"):
        product = None
    if intent == "CHECK_STOCK" and product is None:
        pass
    return Command(intent, product, qty, unit, transcript)
