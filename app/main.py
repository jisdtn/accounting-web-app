from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg


app = FastAPI()


async def get_db_connection():
    return await asyncpg.connect(user='postgres', password='postgres', database='postgres', host='127.0.0.1')
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow('SELECT * FROM items WHERE id = $1', item_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return dict(row)
    finally:
        await conn.close()


class ReadRootRequest(BaseModel):
    name: str


@app.post("/")
def read_root(request: ReadRootRequest):
    if request.name:
        return {f"Hello, {request.name}!"}
    else:
        return {"Hello, World!"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/")
async def root():
    return {"message": "Hello World"}
