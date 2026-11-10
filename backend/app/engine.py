"""Business rules. All stock changes pass through here, atomically."""
import os, uuid, difflib
from decimal import Decimal
from sqlalchemy.orm import Session
from .db import Product, Alias, Sale, Transaction
from .parser import Command, parse

LARGE = Decimal(os.getenv("LARGE_CHANGE_THRESHOLD", "100"))
PENDING: dict = {}  # token -> (Command); in-memory is fine for single-demo-shop MVP


def fmt(x) -> str:
    x = Decimal(x)
    return str(int(x)) if x == x.to_integral() else f"{x.normalize():f}"


def reply(status, message, **extra):
    return {"status": status, "message": message, "spoken": message, **extra}


def find_product(db: Session, name: str):
    """Returns (matches, kind). Alias/name exact first, then substring, then fuzzy."""
    name = name.lower().strip()
    products = db.query(Product).all()
    table = {}
    for p in products:
        table.setdefault(p.name.lower(), set()).add(p.id)
        for a in p.aliases:
            table.setdefault(a.alias.lower(), set()).add(p.id)
    if name in table:
        ids = table[name]
    else:
        ids = {i for k, v in table.items() if name in k.split() or name in k for i in v}
        if not ids:
            close = difflib.get_close_matches(name, list(table), n=3, cutoff=0.75)
            ids = {i for k in close for i in table[k]}
    return [p for p in products if p.id in ids]


def _record(db, p, action, before, change, transcript, sale_id=None, undo_of=None):
    p.quantity = before + change
    tx = Transaction(product_id=p.id, product_name=p.name, action=action,
                      quantity_before=before, quantity_change=change,
                      quantity_after=p.quantity, transcript=transcript,
                      sale_id=sale_id, undo_of=undo_of)
    db.add(tx)
    return tx


def execute(db: Session, cmd: Command, confirmed: bool = False):
    i = cmd.intent
    if i == "UNKNOWN":
        return reply("clarify", "Samajh nahi aaya. Try: 'Maggi ke 10 packet add karo'.")
    if i == "LOW_STOCK":
        return low_stock_reply(db)
    if i == "UNDO":
        return undo_last(db, cmd.transcript)
    if not cmd.product:
        return reply("clarify", "Kaunsa product? Please say the product name.")
    matches = find_product(db, cmd.product)
    if not matches:
        return reply("clarify", f"'{cmd.product}' not found. Add it in Inventory first.",
                     reason="unknown_product")
    if len(matches) > 1:
        names = ", ".join(m.name for m in matches)
        return reply("clarify", f"Which one: {names}?", reason="ambiguous_product",
                     options=[m.name for m in matches])
    p = matches[0]
    before = Decimal(p.quantity)

    if i == "CHECK_STOCK":  # read-only
        return reply("ok", f"{p.name}: {fmt(before)} {p.unit} in stock.", product=p.name)

    if cmd.quantity is None or cmd.quantity <= 0:
        return reply("clarify", f"How many {p.unit} of {p.name}?", reason="missing_quantity")
    if cmd.unit and cmd.unit != p.unit:
        return reply("clarify", f"{p.name} is tracked in {p.unit}, but you said {cmd.unit}. "
                                "Please repeat in the correct unit.", reason="unit_mismatch")
    qty = Decimal(cmd.quantity)
    if i == "SELL" and qty > before:
        return reply("rejected", f"You have {fmt(before)} {p.unit} of {p.name}, but asked to sell "
                                 f"{fmt(qty)}. Did you mean a smaller number?",
                     reason="insufficient_stock")
    if qty >= LARGE and not confirmed:
        token = uuid.uuid4().hex[:8]
        PENDING[token] = cmd
        verb = "add" if i == "ADD_STOCK" else "sell"
        return reply("needs_confirmation", f"Confirm: {verb} {fmt(qty)} {p.unit} of {p.name}?",
                     token=token)

    if i == "ADD_STOCK":
        _record(db, p, "ADD_STOCK", before, qty, cmd.transcript)
        msg = f"{fmt(qty)} {p.name} {p.unit} added. Current stock is {fmt(p.quantity)} {p.unit}."
    else:
        sale = Sale(product_id=p.id, quantity_sold=qty, total_amount=qty * Decimal(p.price))
        db.add(sale); db.flush()
        _record(db, p, "SELL", before, -qty, cmd.transcript, sale_id=sale.id)
        msg = f"Sold {fmt(qty)} {p.unit} of {p.name}. Stock left: {fmt(p.quantity)} {p.unit}."
    db.commit()
    if p.quantity <= p.low_stock_threshold:
        msg += f" Low stock alert: only {fmt(p.quantity)} {p.unit} left."
    return reply("ok", msg, product=p.name, quantity_after=float(p.quantity))


def undo_last(db: Session, transcript="", tx_id=None):
    q = db.query(Transaction).filter(Transaction.status == "applied",
                                     Transaction.action.in_(["ADD_STOCK", "SELL"]))
    tx = db.get(Transaction, tx_id) if tx_id else q.order_by(Transaction.id.desc()).first()
    if not tx or tx.status != "applied" or tx.action not in ("ADD_STOCK", "SELL"):
        return reply("rejected", "Nothing eligible to undo.")
    p = db.get(Product, tx.product_id)
    before = Decimal(p.quantity)
    change = -Decimal(tx.quantity_change)
    if before + change < 0:
        return reply("rejected", "Can't undo: stock would go negative.")
    _record(db, p, "UNDO", before, change, transcript or "undo", undo_of=tx.id)  # compensating
    tx.status = "undone"
    if tx.sale_id:
        db.get(Sale, tx.sale_id).status = "reversed"
    db.commit()
    return reply("ok", f"Undone. {p.name} is back to {fmt(p.quantity)} {p.unit}.")


def low_stock(db: Session):
    return [p for p in db.query(Product).all() if p.quantity <= p.low_stock_threshold]


def low_stock_reply(db):
    items = low_stock(db)
    if not items:
        return reply("ok", "Nothing is low on stock.")
    return reply("ok", "Low stock: " + ", ".join(f"{p.name} {fmt(p.quantity)} {p.unit}" for p in items))


def run_text(db: Session, text: str):
    return execute(db, parse(text))


def confirm(db: Session, token: str):
    cmd = PENDING.pop(token, None)
    if not cmd:
        return reply("rejected", "That confirmation expired.")
    return execute(db, cmd, confirmed=True)
