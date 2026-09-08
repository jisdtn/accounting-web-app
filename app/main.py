import os
from contextlib import asynccontextmanager
from datetime import date, datetime

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import asyncpg
from typing import Optional
import logging
import httpx


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
)

# Balance.value is a Postgres `integer` column (32-bit signed).
PG_INTEGER_MAX = 2_147_483_647

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
API_URL = "https://api.exchangerate.host/live"

API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    if not API_AUTH_TOKEN:
        raise HTTPException(status_code=500, detail="API_AUTH_TOKEN is not configured")
    if credentials is None or credentials.credentials != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


pool: Optional[asyncpg.pool.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    yield
    await pool.close()


app = FastAPI(dependencies=[Depends(verify_token)], lifespan=lifespan)

# Allowed origins
origins = [
    "http://localhost:7070",
    "http://localhost:8000",
    "https://web.telegram.org",
]

# Public tunnel URL the frontend is served from during local demos (e.g. ngrok),
# so the Telegram WebApp / a phone browser can reach the backend across origins.
WEBAPP_URL = os.getenv("WEBAPP_URL")
if WEBAPP_URL:
    origins.append(WEBAPP_URL)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow the listed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/categories/")
async def read_categories():
    async with pool.acquire() as connection:
        categories = await connection.fetch("SELECT * FROM Categories")
        return categories

@app.post("/categories/")
async def create_category(request: Request):
    data = await request.json()
    name = data.get('name')
    currency = data.get('currency')

    if name is None or currency is None:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with pool.acquire() as connection:
        query = "INSERT INTO Categories (name, currency) VALUES ($1, $2) RETURNING id"
        try:
            category_id = await connection.fetchval(query, name, currency)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail=f"Category '{name}' already exists")
        return {"id": category_id, "name": name, "currency": currency}

@app.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    async with pool.acquire() as connection:
        try:
            result = await connection.execute("DELETE FROM Categories WHERE id = $1", category_id)
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(
                status_code=409,
                detail="Category has balance records; delete them first",
            )
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Category deleted successfully"}

@app.get("/balances/")
async def read_balance(from_date: date = Query(...), to_date: date = Query(...)):
    async with pool.acquire() as connection:
        query = """
        SELECT
            Balance.id,
            Balance.cat_id,
            Categories.name AS category_name,
            Balance.date,
            Balance.value,
            Balance.rate,
            ROUND(Balance.rate * Balance.value, 2) AS amount
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
                "rate": float(balance["rate"]),
                "converted_value": float(balance["amount"]),
            } for balance in balances]
        else:
            return []

@app.delete("/balance/{balance_id}")
async def delete_balance(balance_id: int):
    async with pool.acquire() as connection:
        query = "DELETE FROM Balance WHERE id = $1"
        result = await connection.execute(query, balance_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Balance not found")
        return {"message": "Balance deleted successfully"}


async def fetch_exchange_rates() -> dict:
    if not EXCHANGE_RATE_API_KEY:
        raise HTTPException(status_code=500, detail="EXCHANGE_RATE_API_KEY is not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params={"access_key": EXCHANGE_RATE_API_KEY, "source": "EUR"})
        if response.status_code != 200:
            logging.error(f"Failed to fetch exchange rates: {response.text}")
            raise HTTPException(status_code=500, detail="Unable to fetch exchange rates")

        data = response.json()
        logging.info(f"Response from API: {data}")

        if data.get("success") is False:
            error_info = data.get("error", {})
            logging.error(f"Exchange rate provider error: {error_info}")
            raise HTTPException(
                status_code=502,
                detail=f"Exchange rate provider error: {error_info.get('info', error_info)}",
            )

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

    for item in data:
        if item.get('cat_id') is None or item.get('value') is None:
            raise HTTPException(status_code=400, detail="Each item must have cat_id and value")
        if not (-PG_INTEGER_MAX - 1 <= item['value'] <= PG_INTEGER_MAX):
            raise HTTPException(status_code=400, detail=f"value out of range: {item['value']}")

    async with pool.acquire() as connection:
        results = []
        rates: Optional[dict] = None
        async with connection.transaction():
            for item in data:
                cat_id = item['cat_id']
                value = item['value']

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

                if rates is None:
                    logging.info("Fetching exchange rates once before processing categories...")
                    rates = await fetch_exchange_rates()
                    logging.info(f"Fetched rates: {rates}")

                rate = await get_exchange_rate(currency, rates)
                logging.info(f"Received cat_id={cat_id}, value={value}, rate={rate}")

                insert_query = """
                INSERT INTO Balance (cat_id, value, date, rate)
                VALUES ($1, $2, CURRENT_DATE, $3)
                RETURNING id, cat_id, date, value, rate
                """
                balance = await connection.fetchrow(insert_query, cat_id, value, rate)

                converted_value = round(balance["value"] * float(balance["rate"]), 2)
                logging.info(f"Calculated converted_value: {converted_value}")

                results.append({
                    "id": balance["id"],
                    "cat_id": balance["cat_id"],
                    "category_name": category_name,
                    "date": balance["date"],
                    "value": balance["value"],
                    "rate": float(balance["rate"]),
                    "converted_value": converted_value
                })
    return results


async def _set_balance_value(cat_id, date_clause: str, date_param, value):
    if not (-PG_INTEGER_MAX - 1 <= value <= PG_INTEGER_MAX):
        raise HTTPException(status_code=400, detail=f"value out of range: {value}")

    async with pool.acquire() as connection:
        query = f"""
        UPDATE Balance
        SET value = $1
        WHERE cat_id = $2 AND date = {date_clause}
        RETURNING id, cat_id, date, value
        """
        params = [value, cat_id] + ([date_param] if date_param is not None else [])
        balance = await connection.fetchrow(query, *params)

        if not balance:
            raise HTTPException(status_code=404, detail="Balance not found")

        return {
            "message": "Balance updated successfully",
            "balance": dict(balance)
        }


@app.put("/balance/")
async def update_balance(request: Request):
    data = await request.json()

    # Extract fields
    cat_id = data.get("cat_id")
    date = data.get("date")
    value = data.get("value")

    # Check required fields
    if cat_id is None or value is None or date is None:
        raise HTTPException(status_code=400, detail="Each item must have cat_id, date, and value")

    # Strip the timezone, keep only the date
    try:
        date_obj = datetime.fromisoformat(date).date()  # Convert to a plain date for the DB
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601 (e.g. 2024-06-27).")

    return await _set_balance_value(cat_id, "$3", date_obj, value)


@app.patch("/balance/")
async def patch_today_balance(request: Request):
    """Update today's balance for a category without needing to pass a date."""
    data = await request.json()
    cat_id = data.get("cat_id")
    value = data.get("value")

    if cat_id is None or value is None:
        raise HTTPException(status_code=400, detail="Each item must have cat_id and value")

    return await _set_balance_value(cat_id, "CURRENT_DATE", None, value)


logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
