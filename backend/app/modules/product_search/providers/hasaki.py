import requests

from backend.app.logging import setup_logger

logging = setup_logger(__name__)

url_hasaki = "https://hasaki.vn/api/v4/main/suggestion"

def search_hasaki(query: str) -> list:
    params = {
        "q": query,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    }

    response = requests.get(
        url=url_hasaki,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json().get("data", "")

    if data is None:
        logging.error("Cannot get data from Hasaki.")
        return

    logging.info("Get data successfully.")

    products = data.get("products", "")

    return products

if __name__ == "__main__":
    search_hasaki("kem chống")