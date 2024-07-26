from datetime import date

from fastapi import FastAPI, HTTPException, Request, Query
import asyncpg
from typing import Optional


app = FastAPI()

DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"


async def get_pool() -> asyncpg.pool.Pool:
    return await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)

pool: Optional[asyncpg.pool.Pool] = None

@app.on_event("startup")
async def startup():
    global pool
    pool = await get_pool()

@app.on_event("shutdown")
async def shutdown():
    await pool.close()

@app.get("/categories/")
async def read_categories():
    async with pool.acquire() as connection:
        try:
            categories = await connection.fetch("SELECT * FROM Categories")
            return categories
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/categories/")
async def create_category(request: Request):
    data = await request.json()
    name = data.get('name')
    currency = data.get('currency')

    if name is None or currency is None:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with pool.acquire() as connection:
        try:
            query = "INSERT INTO Categories (name, currency) VALUES ($1, $2) RETURNING id"
            category_id = await connection.fetchval(query, name, currency)
            return {"id": category_id, "name": name, "currency": currency}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/balances/")
async def read_balance(from_date: date = Query(...), to_date: date = Query(...)):
    async with pool.acquire() as connection:
        try:
            query = """
            SELECT
                Balance.id,
                Balance.cat_id,
                Categories.name AS category_name,
                Balance.date,
                Balance.value,
                Balance.rate,
                ROUND(Balance.value * Balance.rate)/1000 AS amount
            FROM Balance
            FULL OUTER JOIN Categories ON Categories.id = Balance.cat_id
            WHERE Balance.date >= $1 AND Balance.date <= $2
            GROUP BY Balance.id, Balance.cat_id, Categories.name, Balance.date, Balance.value, Balance.rate
            """
            balances = await connection.fetch(query, from_date, to_date)
            if balances:
                return [{
                    "id": balance["id"],
                    "cat_id": balance["cat_id"],
                    "category_name": balance["category_name"],
                    "date": balance["date"],
                    "value": balance["value"],
                    "rate": balance["rate"] / 1000,
                    "converted_value": balance["amount"],
                } for balance in balances]
            else:
                return []
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.delete("/balance/{balance_id}")
async def delete_balance(balance_id: int):
    async with pool.acquire() as connection:
        try:
            query = "DELETE FROM Balance WHERE id = $1"
            result = await connection.execute(query, balance_id)
            if result == 'DELETE 0':
                raise HTTPException(status_code=404, detail="Balance not found")
            return {"message": "Balance deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/balance/")
async def create_balance(request: Request):
    data = await request.json()
    cat_id = data.get('cat_id')
    value = data.get('value')
    rate = data.get('rate')
    async with pool.acquire() as connection:
        try:
            insert_query = """
            INSERT INTO Balance (cat_id, value, date, rate) 
            VALUES ($1, $2, CURRENT_DATE, CAST($3 * 1000 AS INTEGER))
            RETURNING id, cat_id, date, value, rate
            """
            balance = await connection.fetchrow(insert_query, cat_id, value, rate)

            if not balance:
                raise HTTPException(status_code=400, detail="Failed to insert balance")

            category_query = "SELECT name FROM Categories WHERE id = $1"
            category_name = await connection.fetchval(category_query, cat_id)

            if not category_name:
                raise HTTPException(status_code=404, detail="Category not found")

            return {
                    "id": balance["id"],
                    "cat_id": balance["cat_id"],
                    "category_name": category_name,
                    "date": balance["date"],
                    "value": balance["value"],
                    "rate": balance["rate"] / 1000,
                    "converted_value": (balance["value"] * balance["rate"]) / 1000
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
