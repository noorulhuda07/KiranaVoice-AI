import os
from decimal import Decimal
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .db import init_db, SessionLocal, Product, Alias, Transaction, Sale
from . import engine as eng, gnani
from .parser import parse

app = FastAPI(title="KiranaVoice AI")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _start():
    init_db()


def get_db():
    with SessionLocal() as s:
        yield s


def pdict(p):
    return {"id": p.id, "name": p.name, "quantity": float(p.quantity), "unit": p.unit,
            "price": float(p.price), "low_stock_threshold": float(p.low_stock_threshold),
            "aliases": [a.alias for a in p.aliases],
            "low": p.quantity <= p.low_stock_threshold}


class ProductIn(BaseModel):
    name: str
    quantity: Decimal = Decimal(0)
    unit: str = "packet"
    price: Decimal = Decimal(0)
    low_stock_threshold: Decimal = Decimal(5)
    aliases: list[str] = []


class ProductPatch(BaseModel):
    name: str | None = None
    unit: str | None = None
    price: Decimal | None = None
    low_stock_threshold: Decimal | None = None
    add_aliases: list[str] = []


class CommandIn(BaseModel):
    transcript: str


class SaleIn(BaseModel):
    product_id: int
    quantity: Decimal


class SpeakIn(BaseModel):
    text: str
    language: str | None = None


@app.get("/api/health")
def health():
    return {"ok": True, "gnani_configured": bool(os.getenv("GNANI_API_KEY"))}


@app.post("/api/products")
def add_product(b: ProductIn, db: Session = Depends(get_db)):
    if b.quantity < 0:
        raise HTTPException(422, "quantity must be >= 0")
    p = Product(name=b.name, quantity=b.quantity, unit=b.unit, price=b.price,
                low_stock_threshold=b.low_stock_threshold)
    p.aliases = [Alias(alias=a.lower()) for a in b.aliases]
    db.add(p); db.commit()
    return pdict(p)


@app.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    return [pdict(p) for p in db.query(Product).order_by(Product.name)]


@app.get("/api/products/{pid}")
def get_product(pid: int, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "not found")
    return pdict(p)


@app.patch("/api/products/{pid}")  # metadata only; stock changes go through transactions
def patch_product(pid: int, b: ProductPatch, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "not found")
    for f in ("name", "unit", "price", "low_stock_threshold"):
        if getattr(b, f) is not None:
            setattr(p, f, getattr(b, f))
    for a in b.add_aliases:
        p.aliases.append(Alias(alias=a.lower()))
    db.commit()
    return pdict(p)


@app.post("/api/voice/transcribe")
async def transcribe(file: UploadFile = File(...)):
    return {"transcript": await gnani.transcribe(await file.read())}


@app.post("/api/voice/command")
def voice_command(b: CommandIn, db: Session = Depends(get_db)):
    cmd = parse(b.transcript)
    res = eng.execute(db, cmd)
    res["parsed"] = {"intent": cmd.intent, "product": cmd.product,
                     "quantity": float(cmd.quantity) if cmd.quantity is not None else None,
                     "unit": cmd.unit}
    return res


@app.post("/api/voice/confirm/{token}")
def voice_confirm(token: str, db: Session = Depends(get_db)):
    return eng.confirm(db, token)


@app.post("/api/voice/speak")
async def speak(b: SpeakIn):
    return Response(await gnani.speak(b.text, b.language), media_type="audio/wav")


@app.post("/api/sales")
def record_sale(b: SaleIn, db: Session = Depends(get_db)):
    p = db.get(Product, b.product_id)
    if not p:
        raise HTTPException(404, "not found")
    return eng.execute(db, parse(f"sell {b.quantity} {p.unit} {p.name}"))


@app.get("/api/transactions")
def transactions(db: Session = Depends(get_db)):
    rows = db.query(Transaction).order_by(Transaction.id.desc()).limit(100)
    return [{"id": t.id, "product": t.product_name, "action": t.action, "before": float(t.quantity_before),
             "change": float(t.quantity_change), "after": float(t.quantity_after),
             "transcript": t.transcript, "status": t.status,
             "undoable": t.status == "applied" and t.action in ("ADD_STOCK", "SELL"),
             "at": t.created_at.isoformat()} for t in rows]


@app.post("/api/transactions/{tid}/undo")
def undo(tid: int, db: Session = Depends(get_db)):
    return eng.undo_last(db, tx_id=tid)


@app.get("/api/alerts/low-stock")
def alerts(db: Session = Depends(get_db)):
    return [pdict(p) for p in eng.low_stock(db)]
