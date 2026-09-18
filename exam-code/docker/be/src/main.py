"""Backend API for the course's cryptocurrency price tracker."""

import os
import re
import time
from datetime import datetime, timezone

import mysql.connector
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = os.getenv("MYSQL_DATABASE", "crypto_db")
if not re.fullmatch(r"[A-Za-z0-9_]+", DATABASE):
    raise ValueError("MYSQL_DATABASE must contain only letters, digits, or underscores")

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysqldb"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": DATABASE,
}
COIN_API_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ripple&vs_currencies=usd"
)


def initialize_database():
    """Wait for MySQL and make sure the database and price table exist."""
    for attempt in range(1, 11):
        try:
            connection = mysql.connector.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                connection_timeout=5,
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DATABASE}`")
            cursor.close()
            connection.close()

            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS crypto_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    coin_name VARCHAR(10) NOT NULL,
                    price DECIMAL(18, 8) NOT NULL,
                    timestamp DATETIME NOT NULL
                )"""
            )
            connection.commit()
            cursor.close()
            connection.close()
            app.logger.info("Database is ready")
            return
        except mysql.connector.Error as error:
            app.logger.warning("MySQL is not ready (%s/10): %s", attempt, error)
            if attempt == 10:
                raise SystemExit("Could not initialize the database") from error
            time.sleep(5)


def get_crypto_prices():
    """Fetch Bitcoin and XRP prices; CoinGecko calls XRP 'ripple'."""
    response = requests.get(COIN_API_URL, timeout=15)
    response.raise_for_status()
    prices = response.json()
    return {
        "bitcoin": prices["bitcoin"]["usd"],
        "xrp": prices["ripple"]["usd"],
    }


def save_to_db(coin, price):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO crypto_prices (coin_name, price, timestamp) VALUES (%s, %s, %s)",
            (coin, price, datetime.now(timezone.utc).replace(tzinfo=None)),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except mysql.connector.Error as error:
        app.logger.error("Could not save %s to MySQL: %s", coin, error)
        return False


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.get("/fetch_price")
def fetch_price():
    try:
        prices = get_crypto_prices()
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        app.logger.error("Could not fetch prices: %s", error)
        return jsonify({"error": "Price service is temporarily unavailable"}), 502

    results = [
        {"coin": coin, "price": price, "saved": save_to_db(coin, price)}
        for coin, price in prices.items()
    ]
    return jsonify(results)


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5001)
