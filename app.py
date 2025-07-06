from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from urllib.parse import quote
import time
import logging
from serp import get_price_results_from_serpapi

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

RETAILERS = {
    "US": [
        {"name": "Walmart", "url": "https://www.walmart.com/search?q={}", "currency": "USD", "selector": "span[data-testid='list-view-price']", "use_selenium": True},
        {"name": "Target", "url": "https://www.target.com/s?searchTerm={}", "currency": "USD", "selector": "div[data-test='product-price']", "use_selenium": True},
        {"name": "Apple US", "url": "https://www.apple.com/shop/buy-iphone/iphone-16", "currency": "USD", "selector": "span.current_price", "fixed_query": "iPhone 16"}
    ],
    "UK": [
        {"name": "Argos", "url": "https://www.argos.co.uk/search/{}", "currency": "GBP", "selector": "div[data-test='product-card-price']", "use_selenium": True},
        {"name": "John Lewis", "url": "https://www.johnlewis.com/search?text={}", "currency": "GBP", "selector": "div[data-test='price']", "use_selenium": True},
        {"name": "Apple UK", "url": "https://www.apple.com/uk/shop/buy-iphone/iphone-16", "currency": "GBP", "selector": "span.current_price", "fixed_query": "iPhone 16"}
    ],
    "IN": [
        {"name": "Amazon India", "url": "https://www.amazon.in/s?k={}", "currency": "INR", "selector": "span.a-price-whole", "use_selenium": True},
        {"name": "Reliance Digital", "url": "https://www.reliancedigital.in/search?q={}", "currency": "INR", "selector": "span.pdp__price--new", "use_selenium": True},
        {"name": "Croma", "url": "https://www.croma.com/search/?q={}", "currency": "INR", "selector": "span.amount", "use_selenium": True}
    ]
}

def setup_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    return driver

def clean_price(price_text):
    try:
        price_match = re.search(r"[\d,.]+", price_text)
        if price_match:
            return float(re.sub(r"[^\d.]", "", price_match.group()))
    except Exception as e:
        logging.error(f"Failed to parse price: {e}")
    return None

def fetch_price_from_retailer(retailer, query, country, driver=None):
    try:
        normalized_query = query.replace("Iphone", "iPhone")

        if "fixed_query" in retailer and "iphone" in normalized_query.lower():
            url = retailer["url"]
        else:
            url = retailer["url"].format(quote(normalized_query))

        result = {
            "retailer": retailer["name"],
            "url": url,
            "price": None,
            "currency": retailer["currency"],
            "product_name": normalized_query
        }

        if retailer.get("use_selenium", False):
            if driver is None:
                raise ValueError("Selenium driver is not provided")

            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, retailer["selector"]))
            )
            price_element = driver.find_element(By.CSS_SELECTOR, retailer["selector"])
            if not price_element:
                logging.warning(f"Selector '{retailer['selector']}' not found for {retailer['name']}")
                return None
            price_text = price_element.text.strip()
        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            price_element = soup.select_one(retailer["selector"])
            if not price_element:
                logging.warning(f"Selector '{retailer['selector']}' not found for {retailer['name']}")
                return None
            price_text = price_element.text.strip()

        price = clean_price(price_text)
        if price:
            result["price"] = price
            return result
        else:
            logging.info(f"Could not extract price from text: '{price_text}'")
    except Exception as e:
        logging.error(f"Error fetching from {retailer['name']} ({country}): {e}")
    return None

@app.route("/selenium/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        country = data.get("country")
        query = data.get("query")

        if not country or not query or country not in RETAILERS:
            return jsonify({"error": "Invalid input. Please provide a valid country (US, UK, India) and query."}), 400

        results = []
        driver = setup_selenium()

        try:
            for retailer in RETAILERS[country]:
                for attempt in range(3):
                    result = fetch_price_from_retailer(retailer, query, country, driver)
                    if result:
                        results.append(result)
                        break
                    time.sleep(1)
        finally:
            driver.quit()

        valid_results = [r for r in results if r.get("price") is not None]
        if not valid_results:
            return jsonify({"error": f"No prices found for {query} in {country}"}), 404

        valid_results.sort(key=lambda x: x["price"])
        return jsonify(valid_results)

    except Exception as e:
        logging.exception("Unexpected server error")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        data = request.get_json()
        country = data.get("country")
        query = data.get("query")

        if not country or not query:
            return jsonify({"error": "Country and query are required."}), 400

        results = get_price_results_from_serpapi(country, query)
        if not results:
            return jsonify({"error": f"No results found for {query} in {country}"}), 404
        return jsonify(results), 200

    except Exception as e:
        logging.exception("Error using SerpAPI")
        print(e)
        return jsonify({"error": "Failed to retrieve results from SerpAPI"}), 500

if __name__ == "__main__":
    app.run(debug=True)
