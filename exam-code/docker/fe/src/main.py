"""Frontend and backend proxy for the course's cryptocurrency tracker."""

import os

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)
BACKEND_API_URL = os.getenv(
    "BACKEND_API_URL", "http://backend-service:5001/fetch_price"
)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.get("/fetch_price")
def fetch_price():
    try:
        response = requests.get(BACKEND_API_URL, timeout=20)
        response.raise_for_status()
        return jsonify(response.json())
    except (requests.RequestException, ValueError) as error:
        app.logger.error("Could not reach backend: %s", error)
        return jsonify({"error": "Could not fetch prices from the backend"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
