from postgresql_app import models
from postgresql_app.database import SessionLocal, engine
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ReadRootRequest(BaseModel):
    name: str

@app.post("/")
def read_root(request: ReadRootRequest):
    if request.name:
        return {f"Hello, {request.name}!"}
    else:
        return {f"Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/")
async def root():
    return {"message": "Hello World"}