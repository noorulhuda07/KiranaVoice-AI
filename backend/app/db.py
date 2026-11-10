from datetime import datetime
from sqlalchemy import (create_engine, Column, Integer, String, Numeric, DateTime,
                        ForeignKey)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

engine = create_engine("sqlite:///kirana.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()
Q = Numeric(12, 3)


class Shop(Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True)
    shop_name = Column(String, nullable=False)
    preferred_language = Column(String, default="hi-en")
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), default=1)
    name = Column(String, nullable=False)
    quantity = Column(Q, default=0)
    unit = Column(String, default="packet")
    price = Column(Q, default=0)
    low_stock_threshold = Column(Q, default=5)
    aliases = relationship("Alias", cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "product_aliases"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    alias = Column(String, nullable=False)


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, default=1)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity_sold = Column(Q)
    total_amount = Column(Q)
    status = Column(String, default="active")  # active | reversed
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, default=1)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String)
    action = Column(String)  # ADD_STOCK | SELL | UNDO
    quantity_before = Column(Q)
    quantity_change = Column(Q)
    quantity_after = Column(Q)
    transcript = Column(String, default="")
    status = Column(String, default="applied")  # applied | undone
    undo_of = Column(Integer, nullable=True)
    sale_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if s.query(Shop).count() == 0:
            s.add(Shop(shop_name="Demo Kirana"))
            demo = [("Maggi 70g", 20, "packet", 14, 10, ["chhota maggi", "छोटा मैगी"]),
                    ("Maggi 140g", 12, "packet", 28, 5, ["bada maggi", "बड़ा मैगी"]),
                    ("Rice", 8, "kg", 60, 10, ["chawal", "चावल"]),
                    ("Cooking oil", 15, "L", 150, 5, ["tel", "oil", "तेल"]),
                    ("Sugar", 30, "kg", 45, 8, ["cheeni", "chini", "चीनी"])]
            for n, q, u, p, t, al in demo:
                pr = Product(name=n, quantity=q, unit=u, price=p, low_stock_threshold=t)
                pr.aliases = [Alias(alias=a) for a in al]
                s.add(pr)
            s.commit()
