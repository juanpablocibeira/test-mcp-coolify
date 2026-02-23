import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/testdb"
)

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")


class ItemCreate(BaseModel):
    name: str
    description: str = ""


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    model_config = {"from_attributes": True}


app = FastAPI(title="Test MCP App")


@app.on_event("startup")
def on_startup():
    for attempt in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception:
            import time
            time.sleep(2)


@app.get("/")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return {"status": "ok", "db": "error"}


@app.get("/items", response_model=list[ItemResponse])
def list_items():
    with Session(engine) as session:
        return session.query(Item).all()


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):
    db_item = Item(name=item.name, description=item.description)
    with Session(engine) as session:
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item
