from datetime import date

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from typing import Optional
import logging
import httpx


app = FastAPI()

DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"

API_URL = "https://api.exchangerate.host/live"

# Разрешенные источники (origin)
origins = [
    "http://localhost:7070",
    "http://localhost:8000",
    "https://web.telegram.org",
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешить указанные источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


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
                ROUND((Balance.rate / 10000.0) * Balance.value, 2) AS amount
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
                    "rate": balance["rate"] / 10000,
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


async def fetch_exchange_rates() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params={"access_key": "f7f6c2b62f3f536d814b4c1949b718ed", "source": "EUR"})
        if response.status_code != 200:
            logging.error(f"Failed to fetch exchange rates: {response.text}")
            raise HTTPException(status_code=500, detail="Unable to fetch exchange rates")

        data = response.json()
        logging.info(f"Response from API: {data}")
        rates = data.get("quotes")
        if not rates:
            raise HTTPException(status_code=500, detail="Rates not found in the response")
        return rates

async def get_exchange_rate(currency: str, rates: dict) -> float:
    if currency.upper() == "EUR":
        return 1.0

    if currency.upper() == "USDT":
        usd_rate = rates.get("EURUSD")
        if usd_rate:
            return 1 / usd_rate  # USD to EUR
        else:
            raise HTTPException(status_code=500, detail="USD rate not found in exchange rates")

    rate_currency = rates.get(f"EUR{currency.upper()}")
    if not rate_currency:
        raise HTTPException(status_code=404, detail=f"Currency rate for {currency} not found")

    rate_inverted = 1 / rate_currency
    logging.info(f"Currency rate for {currency} (в EUR): {rate_inverted}")
    return rate_inverted


@app.post("/balance/")
async def create_balance(request: Request):
    data = await request.json()

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Data should be a list of balances")

    logging.info("Fetching exchange rates once before processing categories...")
    rates = await fetch_exchange_rates()
    logging.info(f"Fetched rates: {rates}")

    async with pool.acquire() as connection:
        results = []
        for item in data:
            cat_id = item.get('cat_id')
            value = item.get('value')

            if cat_id is None or value is None:
                raise HTTPException(status_code=400, detail="Each item must have cat_id and value")

            logging.info(f"Data received: cat_id={cat_id}, value={value}")

            check_query = """
                SELECT 1 FROM Balance 
                WHERE cat_id = $1 AND date = CURRENT_DATE
                """
            existing_record = await connection.fetchval(check_query, cat_id)
            if existing_record:
                logging.warning(f"Balance for cat_id={cat_id} already exists for today")
                continue

            category_query = "SELECT name, currency FROM Categories WHERE id = $1"
            category = await connection.fetchrow(category_query, cat_id)

            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            category_name = category['name']
            currency = category['currency']

            rate = await get_exchange_rate(currency, rates)
            rate_as_integer = int(rate * 10000)
            logging.info(f"Received cat_id={cat_id}, value={value}, rate={rate}, rate_as_integer={rate_as_integer}")

            try:
                insert_query = """
                INSERT INTO Balance (cat_id, value, date, rate)
                VALUES ($1, $2, CURRENT_DATE, $3)
                RETURNING id, cat_id, date, value, rate
                """
                balance = await connection.fetchrow(insert_query, cat_id, value, rate_as_integer)
                logging.info(f"Calculating converted_value: value={balance['value']}, rate={balance['rate']} / 10000.0")

                converted_value = balance["value"] * (balance["rate"] / 10000.0)
                logging.info(f"Calculated converted_value: {converted_value}")

                results.append({
                    "id": balance["id"],
                    "cat_id": balance["cat_id"],
                    "category_name": category_name,
                    "date": balance["date"],
                    "value": balance["value"],
                    "rate": balance["rate"] / 10000,
                    "converted_value": converted_value
                })

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    return results

@app.put("/balance/")
async def update_balance(request: Request):
    data = await request.json()
    cat_id = data.get("cat_id")
    date = data.get("date")
    value = data.get("value")

    if value is None:
        raise HTTPException(status_code=400, detail="Value is required")

    async with pool.acquire() as connection:
        query = """
        UPDATE Balance
        SET value = $1
        WHERE cat_id = $2 AND date::date = $3::date
        RETURNING id, cat_id, date, value
        """
        balance = await connection.fetchrow(query, value, cat_id, date)

        if not balance:
            raise HTTPException(status_code=404, detail="Balance not found")

        return {"message": "Balance updated successfully", "balance": dict(balance)}


logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
