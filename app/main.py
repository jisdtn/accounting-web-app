from datetime import date

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from typing import Optional
import logging
import httpx
import xml.etree.ElementTree as ET


app = FastAPI()

DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"

# Конфигурация API для курса валют
API_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


# Разрешенные источники (origin)
origins = [
    "http://localhost:7070",
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


async def get_exchange_rate(currency: str) -> float:
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL)
        if response.status_code != 200:
            logging.error(f"Failed to fetch exchange rates: {response.text}")
            raise HTTPException(status_code=500, detail="Unable to fetch exchange rates")

        # Парсим XML ответ
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        # Находим все курсы валют
        namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                      'eurofxref': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        cube = root.find('.//eurofxref:Cube[@time]', namespaces)
        rates = {}

        for currency_cube in cube.findall('eurofxref:Cube', namespaces):
            currency_code = currency_cube.get('currency')
            rate = float(currency_cube.get('rate'))
            rates[currency_code] = rate

            # Добавляем курс евро для удобства (по сути 1 EUR = 1 EUR)
        rates["EUR"] = 1.0

        rates = response.json().get("rates")


        # Получаем курс евро (EUR)
        rate_eur = rates.get("EUR")
        if not rate_eur:
            raise HTTPException(status_code=500, detail="EUR rate not found in exchange rates")

        # Проверка для USDT
        if currency == "USDT":
            # Для USDT используем курс USD
            rate_usd = rates.get("USD")
            if not rate_usd:
                raise HTTPException(status_code=500, detail="USD rate not found in exchange rates")

            # Курс USDT относительно EUR такой же, как и курс USD к EUR
            rate_relative_to_eur = rate_eur / rate_usd
            logging.info(f"Курс для USDT (относительно EUR через USD): {rate_relative_to_eur}")
            return rate_relative_to_eur

        # Для остальных валют
        rate_currency = rates.get(currency)
        if not rate_currency:
            raise HTTPException(status_code=404, detail=f"Currency rate for {currency} not found")

        # Преобразуем курс валюты относительно евро
        rate_relative_to_eur = rate_eur / rate_currency
        logging.info(f"Курс валюты для {currency}: {rate_currency}")
        return rate_relative_to_eur


@app.post("/balance/")
async def create_balance(request: Request):
    data = await request.json()
    cat_id = data.get('cat_id')
    value = data.get('value')

    logging.info(f"Полученные данные: cat_id={cat_id}, value={value}, тип value={type(value)}")

    async with pool.acquire() as connection:
        category_query = "SELECT name, currency FROM Categories WHERE id = $1"
        category = await connection.fetchrow(category_query, cat_id)

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        category_name = category['name']
        currency = category['currency']

        rate = await get_exchange_rate(currency)
        rate_as_integer = int(rate * 10000)
        logging.info(f"Received cat_id={cat_id}, value={value}, rate={rate}, rate_as_integer={rate_as_integer}")

        logging.info(f"Preparing to insert balance with cat_id: {cat_id}, value: {value}, rate: {rate}")

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

            if not balance:
                raise HTTPException(status_code=400, detail="Failed to insert balance")


            return {
                    "id": balance["id"],
                    "cat_id": balance["cat_id"],
                    "category_name": category_name,
                    "date": balance["date"],
                    "value": balance["value"],
                    "rate": balance["rate"] / 10000,
                    "converted_value": converted_value
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
